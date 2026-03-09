from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import AnalysisRun
from app.services.analysis import enqueue_analysis

router = APIRouter()


@router.post('/{project_id}/analysis/run')
def run_analysis(project_id: int, db: Session = Depends(get_db)):
    run = AnalysisRun(project_id=project_id, status='queued', stage='queued')
    db.add(run)
    db.commit()
    db.refresh(run)
    enqueue_analysis(run.id)
    return {'run_id': run.id, 'status': run.status}


@router.get('/{project_id}/analysis/status')
def analysis_status(project_id: int, db: Session = Depends(get_db)):
    runs = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).all()
    return [{'id': r.id, 'status': r.status, 'stage': r.stage} for r in runs]
