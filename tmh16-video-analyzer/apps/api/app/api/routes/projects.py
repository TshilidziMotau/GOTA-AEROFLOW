from collections import defaultdict
from pathlib import Path

import cv2
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.models import (
    AnalysisRun,
    EvidenceExport,
    ManualEdit,
    ParkingEvent,
    PedestrianEvent,
    Project,
    QueueEvent,
    SceneDefinition,
    Track,
    TurningEvent,
    Video,
)
from app.schemas.schemas import ManualCorrectionInput, ProjectCreate, ProjectOut, SceneDefinitionInput
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

    cap = cv2.VideoCapture(str(target))
    fps = cap.get(cv2.CAP_PROP_FPS) or 0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    duration = (frames / fps) if fps else None

    video = Video(
        project_id=project_id,
        filename=file.filename,
        path=str(target),
        duration_s=duration,
        fps=fps or None,
        resolution=f'{width}x{height}' if width and height else None,
    )
    db.add(video)
    db.commit()
    return {'status': 'uploaded', 'video_path': str(target), 'fps': fps, 'duration_s': duration, 'resolution': video.resolution}
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


@router.get('/{project_id}/tracks')
def get_tracks(project_id: int, db: Session = Depends(get_db)):
    tracks = db.query(Track).filter(Track.project_id == project_id).order_by(Track.id.desc()).limit(500).all()
    return [
        {
            'id': t.id,
            'run_id': t.run_id,
            'object_class': t.object_class,
            'confidence_avg': t.confidence_avg,
            'start_frame': t.start_frame,
            'end_frame': t.end_frame,
            'path': t.path,
        }
        for t in tracks
    ]


@router.post('/{project_id}/manual-corrections')
def manual_corrections(project_id: int, payload: ManualCorrectionInput, db: Session = Depends(get_db)):
    edit = ManualEdit(project_id=project_id, user_id=1, edit_type=payload.edit_type, payload=payload.payload)
    db.add(edit)

    if payload.edit_type == 'reclassify_track':
        track_id = payload.payload.get('track_id')
        new_class = payload.payload.get('new_class')
        track = db.get(Track, track_id) if track_id else None
        if track and new_class:
            track.object_class = new_class

    db.commit()
    return {'status': 'recorded'}


@router.get('/{project_id}/counts')
def counts(project_id: int, db: Session = Depends(get_db)):
    events = db.query(TurningEvent).filter(TurningEvent.project_id == project_id).all()
    intervals: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for e in events:
        bucket = int(e.event_time_s // 900)
        intervals[bucket][e.movement] += 1
    out = []
    for bucket, vals in sorted(intervals.items()):
        out.append({'interval_index': bucket, 'start_s': bucket * 900, 'end_s': (bucket + 1) * 900, 'movements': vals})
    return {
        'project_id': project_id,
        'intervals': out,
        'peak_interval': max(out, key=lambda x: sum(x['movements'].values()), default=None),
        'assumption_note': 'Movement counts are automated detections and should be reviewed before sign-off.',
    }


@router.get('/{project_id}/queues')
def queues(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(QueueEvent).filter(QueueEvent.project_id == project_id).all()
    if not rows:
        return {'project_id': project_id, 'queue_summary': 'estimated from occupancy', 'items': []}
    values = [r.occupied_count for r in rows]
    return {
        'project_id': project_id,
        'queue_summary': 'estimated from occupancy',
        'average_queue': sum(values) / len(values),
        'max_queue': max(values),
        'items': [{'time_s': r.event_time_s, 'occupied_count': r.occupied_count} for r in rows[:500]],
    }


@router.get('/{project_id}/pedestrians')
def pedestrians(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(PedestrianEvent).filter(PedestrianEvent.project_id == project_id).all()
    return {
        'project_id': project_id,
        'crossings': [{'crossing_name': r.crossing_name, 'time_s': r.event_time_s} for r in rows],
        'total_crossings': len(rows),
        'conflicts': [],
    }


@router.get('/{project_id}/school-mode')
def school_mode(project_id: int, db: Session = Depends(get_db)):
    queue_rows = db.query(QueueEvent).filter(QueueEvent.project_id == project_id).all()
    flags = []
    if any(q.occupied_count >= 6 for q in queue_rows):
        flags.append('queue_buildup_near_gate_estimated')
    return {
        'project_id': project_id,
        'drop_off_events': [],
        'flags': flags,
        'review_note': 'School safety observations are draft flags and require analyst confirmation.',
    }


@router.get('/{project_id}/parking')
def parking(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(ParkingEvent).filter(ParkingEvent.project_id == project_id).all()
    return {
        'project_id': project_id,
        'occupancy': [{'zone_name': r.zone_name, 'event_type': r.event_type, 'dwell_s': r.dwell_s} for r in rows],
        'no_stopping_infringements': [],
    }
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
    latest_run = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).order_by(AnalysisRun.id.desc()).first()
    export = EvidenceExport(project_id=project_id, export_type='pdf', path=f'/storage/reports/{project_id}.pdf')
    db.add(export)
    db.commit()
    return {'status': 'queued', 'latest_run_id': latest_run.id if latest_run else None}
    export = EvidenceExport(project_id=project_id, export_type='pdf', path=f'/storage/reports/{project_id}.pdf')
    db.add(export)
    db.commit()
    return {'status': 'queued'}


@router.get('/{project_id}/exports')
def list_exports(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(EvidenceExport).filter(EvidenceExport.project_id == project_id).all()
    return [{'id': r.id, 'type': r.export_type, 'path': r.path} for r in rows]
