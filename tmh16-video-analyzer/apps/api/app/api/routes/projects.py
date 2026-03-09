from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import Project, Video, SceneDefinition, ManualEdit, EvidenceExport
from app.schemas.schemas import ProjectCreate, ProjectOut, SceneDefinitionInput, ManualCorrectionInput
from app.core.config import settings

router = APIRouter()


@router.get('', response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@router.post('', response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get('/{project_id}', response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    return project


@router.post('/{project_id}/videos')
def upload_video(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')
    target_dir = Path(settings.storage_path) / str(project_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / file.filename
    target.write_bytes(file.file.read())
    video = Video(project_id=project_id, filename=file.filename, path=str(target))
    db.add(video)
    db.commit()
    return {'status': 'uploaded', 'video_path': str(target)}


@router.post('/{project_id}/scene')
def save_scene(project_id: int, payload: SceneDefinitionInput, db: Session = Depends(get_db)):
    scene = SceneDefinition(project_id=project_id, config=payload.config)
    db.add(scene)
    db.commit()
    return {'status': 'saved'}


@router.post('/{project_id}/manual-corrections')
def manual_corrections(project_id: int, payload: ManualCorrectionInput, db: Session = Depends(get_db)):
    edit = ManualEdit(project_id=project_id, user_id=1, edit_type=payload.edit_type, payload=payload.payload)
    db.add(edit)
    db.commit()
    return {'status': 'recorded'}


@router.get('/{project_id}/counts')
def counts(project_id: int):
    return {'project_id': project_id, 'intervals': [], 'review_note': 'TODO: aggregation output integration'}


@router.get('/{project_id}/queues')
def queues(project_id: int):
    return {'project_id': project_id, 'queue_summary': 'estimated from occupancy', 'items': []}


@router.get('/{project_id}/pedestrians')
def pedestrians(project_id: int):
    return {'project_id': project_id, 'crossings': [], 'conflicts': []}


@router.get('/{project_id}/school-mode')
def school_mode(project_id: int):
    return {'project_id': project_id, 'drop_off_events': [], 'flags': []}


@router.get('/{project_id}/parking')
def parking(project_id: int):
    return {'project_id': project_id, 'occupancy': [], 'no_stopping_infringements': []}


@router.post('/{project_id}/report/generate')
def generate_report(project_id: int, db: Session = Depends(get_db)):
    export = EvidenceExport(project_id=project_id, export_type='pdf', path=f'/storage/reports/{project_id}.pdf')
    db.add(export)
    db.commit()
    return {'status': 'queued'}


@router.get('/{project_id}/exports')
def list_exports(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(EvidenceExport).filter(EvidenceExport.project_id == project_id).all()
    return [{'id': r.id, 'type': r.export_type, 'path': r.path} for r in rows]
