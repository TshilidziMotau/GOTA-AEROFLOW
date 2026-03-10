from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import AnalysisRun, ManualEdit
from app.schemas.schemas import AnalysisRunRequest, AnalysisReviewRequest
from app.services.analysis import enqueue_analysis
from app.services.auth import CurrentUser, get_current_user, require_roles

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post('/{project_id}/analysis/run')
def run_analysis(
    project_id: int,
    payload: AnalysisRunRequest,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_roles('admin', 'analyst')),
):
    run = AnalysisRun(
        project_id=project_id,
        status='queued',
        stage='queued',
        metadata_json={
            'frame_skip': payload.frame_skip,
            'confidence_threshold': payload.confidence_threshold,
        },
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    enqueue_analysis(run.id)
    return {'run_id': run.id, 'status': run.status}


@router.get('/{project_id}/analysis/status')
def analysis_status(project_id: int, db: Session = Depends(get_db)):
    runs = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).order_by(AnalysisRun.id.desc()).all()
    return [{'id': r.id, 'status': r.status, 'stage': r.stage, 'metadata': r.metadata_json} for r in runs]


@router.get('/{project_id}/analysis/audit')
def analysis_audit(project_id: int, db: Session = Depends(get_db)):
    runs = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).order_by(AnalysisRun.id.desc()).all()
    review_edits = db.query(ManualEdit).filter(
        ManualEdit.project_id == project_id,
        ManualEdit.edit_type.in_(['analysis_review_status', 'analysis_retry']),
    ).order_by(ManualEdit.id.desc()).all()
    return {
        'project_id': project_id,
        'runs': [
            {
                'id': r.id,
                'status': r.status,
                'stage': r.stage,
                'metadata': r.metadata_json,
                'created_at': r.created_at.isoformat(),
            }
            for r in runs
        ],
        'governance_events': [
            {
                'id': e.id,
                'user_id': e.user_id,
                'edit_type': e.edit_type,
                'payload': e.payload,
                'created_at': e.created_at.isoformat(),
            }
            for e in review_edits
        ],
    }


@router.post('/{project_id}/analysis/{run_id}/review')
def review_analysis_run(
    project_id: int,
    run_id: int,
    payload: AnalysisReviewRequest,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles('admin', 'analyst')),
):
    run = db.get(AnalysisRun, run_id)
    if not run or run.project_id != project_id:
        raise HTTPException(status_code=404, detail='Analysis run not found')

    allowed = {'review_needed', 'completed', 'failed'}
    if payload.status not in allowed:
        raise HTTPException(status_code=400, detail=f'Invalid status. Allowed: {sorted(allowed)}')

    run.status = payload.status
    run.stage = payload.status
    meta = run.metadata_json or {}
    meta['review_note'] = payload.note or ''
    run.metadata_json = meta

    db.add(ManualEdit(project_id=project_id, user_id=user.id, edit_type='analysis_review_status', payload={'run_id': run_id, 'status': payload.status, 'note': payload.note}))
    db.commit()
    return {'id': run.id, 'status': run.status, 'stage': run.stage, 'metadata': run.metadata_json}


@router.post('/{project_id}/analysis/{run_id}/retry')
def retry_analysis_run(
    project_id: int,
    run_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles('admin', 'analyst')),
):
    old = db.get(AnalysisRun, run_id)
    if not old or old.project_id != project_id:
        raise HTTPException(status_code=404, detail='Analysis run not found')

    run = AnalysisRun(
        project_id=project_id,
        status='queued',
        stage='queued',
        metadata_json=dict(old.metadata_json or {}),
    )
    db.add(run)
    db.flush()
    db.add(ManualEdit(project_id=project_id, user_id=user.id, edit_type='analysis_retry', payload={'from_run_id': run_id, 'new_run_id': run.id}))
    db.commit()
    enqueue_analysis(run.id)
    return {'run_id': run.id, 'status': run.status, 'retried_from': run_id}
