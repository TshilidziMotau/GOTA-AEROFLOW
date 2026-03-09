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
from app.services.analytics import (
    school_mode_flags,
    summarize_pedestrian_events,
    summarize_queue_events,
    summarize_turning_events,
    tmh16_alignment_card,
)

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
    summary = summarize_turning_events([{'event_time_s': e.event_time_s, 'movement': e.movement} for e in events])
    return {
        'project_id': project_id,
        'intervals': summary['intervals'],
        'peak_interval': summary['peak_interval'],
        'assumption_note': 'Movement counts are automated detections and should be reviewed before sign-off.',
    }


@router.get('/{project_id}/queues')
def queues(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(QueueEvent).filter(QueueEvent.project_id == project_id).all()
    summary = summarize_queue_events([{'event_time_s': r.event_time_s, 'occupied_count': r.occupied_count} for r in rows])
    return {
        'project_id': project_id,
        'queue_summary': 'estimated from tracked occupancy and slow-moving objects',
        **summary,
    }


@router.get('/{project_id}/pedestrians')
def pedestrians(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(PedestrianEvent).filter(PedestrianEvent.project_id == project_id).all()
    summary = summarize_pedestrian_events([{'crossing_name': r.crossing_name, 'time_s': r.event_time_s} for r in rows])
    return {
        'project_id': project_id,
        'crossings': summary['events'],
        'crossing_counts': summary['crossing_counts'],
        'total_crossings': summary['total_crossings'],
        'conflicts': [],
    }


@router.get('/{project_id}/school-mode')
def school_mode(project_id: int, db: Session = Depends(get_db)):
    queue_rows = db.query(QueueEvent).filter(QueueEvent.project_id == project_id).all()
    ped_rows = db.query(PedestrianEvent).filter(PedestrianEvent.project_id == project_id).all()
    turn_rows = db.query(TurningEvent).filter(TurningEvent.project_id == project_id).all()

    queue_summary = summarize_queue_events([{'event_time_s': r.event_time_s, 'occupied_count': r.occupied_count} for r in queue_rows])
    ped_summary = summarize_pedestrian_events([{'crossing_name': r.crossing_name, 'time_s': r.event_time_s} for r in ped_rows])
    flags = school_mode_flags(queue_summary, ped_summary, len(turn_rows))

    return {
        'project_id': project_id,
        'drop_off_events': [],
        'flags': flags,
        'queue_peak': queue_summary.get('max_queue', 0),
        'pedestrian_activity': ped_summary.get('total_crossings', 0),
        'review_note': 'School safety observations are draft flags and require analyst confirmation.',
    }


@router.get('/{project_id}/parking')
def parking(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(ParkingEvent).filter(ParkingEvent.project_id == project_id).all()
    occupancy = [{'zone_name': r.zone_name, 'event_type': r.event_type, 'dwell_s': r.dwell_s} for r in rows]
    short_stay = [o for o in occupancy if o['dwell_s'] <= 180]
    return {
        'project_id': project_id,
        'occupancy': occupancy,
        'short_stay_count': len(short_stay),
        'turnover_estimate': len(occupancy),
        'no_stopping_infringements': [],
    }


@router.get('/{project_id}/tmh16-alignment')
def tmh16_alignment(project_id: int, db: Session = Depends(get_db)):
    count_rows = db.query(TurningEvent).filter(TurningEvent.project_id == project_id).all()
    queue_rows = db.query(QueueEvent).filter(QueueEvent.project_id == project_id).all()
    ped_rows = db.query(PedestrianEvent).filter(PedestrianEvent.project_id == project_id).all()
    parking_rows = db.query(ParkingEvent).filter(ParkingEvent.project_id == project_id).all()

    count_summary = summarize_turning_events([{'event_time_s': e.event_time_s, 'movement': e.movement} for e in count_rows])
    cards = tmh16_alignment_card(
        has_peak_15=bool(count_summary['peak_interval']),
        has_movement_breakdown=any((row.get('movements') for row in count_summary['intervals'])),
        has_queue=bool(queue_rows),
        has_peds=bool(ped_rows),
        has_school=bool(queue_rows or ped_rows),
        has_parking=bool(parking_rows),
        has_public_transport=False,
        has_service_heavy=any(t.movement.startswith('cross_') for t in count_rows),
    )
    return {
        'project_id': project_id,
        'cards': cards,
        'disclaimer': 'This checklist supports evidence completeness only. Final TMH16 compliance requires professional engineering judgment.',
    }


@router.post('/{project_id}/report/generate')
def generate_report(project_id: int, db: Session = Depends(get_db)):
    latest_run = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).order_by(AnalysisRun.id.desc()).first()
    export = EvidenceExport(project_id=project_id, export_type='pdf', path=f'/storage/reports/{project_id}.pdf')
    db.add(export)
    db.commit()
    return {'status': 'queued', 'latest_run_id': latest_run.id if latest_run else None}


@router.get('/{project_id}/exports')
def list_exports(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(EvidenceExport).filter(EvidenceExport.project_id == project_id).all()
    return [{'id': r.id, 'type': r.export_type, 'path': r.path} for r in rows]
