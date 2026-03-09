from pathlib import Path
import hashlib
import json

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
from app.services.reporting import write_counts_csv, write_counts_xlsx, write_report_html
from app.services.auth import CurrentUser, get_current_user, require_roles

router = APIRouter(dependencies=[Depends(get_current_user)])


def _build_project_summaries(project_id: int, db: Session) -> dict:
    turn_rows = db.query(TurningEvent).filter(TurningEvent.project_id == project_id).all()
    queue_rows = db.query(QueueEvent).filter(QueueEvent.project_id == project_id).all()
    ped_rows = db.query(PedestrianEvent).filter(PedestrianEvent.project_id == project_id).all()
    parking_rows = db.query(ParkingEvent).filter(ParkingEvent.project_id == project_id).all()

    count_summary = summarize_turning_events([{'event_time_s': e.event_time_s, 'movement': e.movement} for e in turn_rows])
    queue_summary = summarize_queue_events([{'event_time_s': r.event_time_s, 'occupied_count': r.occupied_count} for r in queue_rows])
    ped_summary = summarize_pedestrian_events([{'crossing_name': r.crossing_name, 'time_s': r.event_time_s} for r in ped_rows])
    school_flags = school_mode_flags(queue_summary, ped_summary, len(turn_rows))
    alignment_cards = tmh16_alignment_card(
        has_peak_15=bool(count_summary['peak_interval']),
        has_movement_breakdown=any((row.get('movements') for row in count_summary['intervals'])),
        has_queue=bool(queue_rows),
        has_peds=bool(ped_rows),
        has_school=bool(queue_rows or ped_rows),
        has_parking=bool(parking_rows),
        has_public_transport=False,
        has_service_heavy=any(getattr(t, 'object_class', '') == 'heavy_truck' for t in db.query(Track).filter(Track.project_id == project_id).all()),
    )
    return {
        'count_summary': count_summary,
        'queue_summary': queue_summary,
        'ped_summary': ped_summary,
        'school_flags': school_flags,
        'alignment_cards': alignment_cards,
        'parking_count': len(parking_rows),
    }


@router.get('', response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@router.post('', response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles('admin', 'analyst'))):
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




@router.get('/{project_id}/videos')
def list_videos(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(Video).filter(Video.project_id == project_id).order_by(Video.id.desc()).all()
    return [
        {
            'id': r.id,
            'filename': r.filename,
            'path': r.path,
            'duration_s': r.duration_s,
            'fps': r.fps,
            'resolution': r.resolution,
            'created_at': r.created_at.isoformat(),
        }
        for r in rows
    ]


@router.get('/{project_id}/scene')
def get_scene(project_id: int, db: Session = Depends(get_db)):
    scene = db.query(SceneDefinition).filter(SceneDefinition.project_id == project_id).order_by(SceneDefinition.id.desc()).first()
    if not scene:
        return {'project_id': project_id, 'config': {}, 'status': 'not_configured'}
    return {'project_id': project_id, 'config': scene.config, 'status': 'configured'}

@router.post('/{project_id}/videos')
def upload_video(project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles('admin', 'analyst'))):
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
def save_scene(project_id: int, payload: SceneDefinitionInput, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles('admin', 'analyst'))):
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
def manual_corrections(project_id: int, payload: ManualCorrectionInput, db: Session = Depends(get_db), user: CurrentUser = Depends(require_roles('admin', 'analyst'))):
    edit = ManualEdit(project_id=project_id, user_id=user.id, edit_type=payload.edit_type, payload=payload.payload)
    db.add(edit)

    if payload.edit_type == 'reclassify_track':
        track_id = payload.payload.get('track_id')
        new_class = payload.payload.get('new_class')
        track = db.get(Track, track_id) if track_id else None
        if track and new_class:
            track.object_class = new_class

    if payload.edit_type == 'delete_track':
        track_id = payload.payload.get('track_id')
        track = db.get(Track, track_id) if track_id else None
        if track:
            db.delete(track)

    if payload.edit_type == 'merge_tracks':
        source_id = payload.payload.get('source_track_id')
        target_id = payload.payload.get('target_track_id')
        source = db.get(Track, source_id) if source_id else None
        target = db.get(Track, target_id) if target_id else None
        if source and target:
            merged = sorted((target.path or []) + (source.path or []), key=lambda p: p[2] if len(p) > 2 else 0)
            target.path = merged
            target.start_frame = min(target.start_frame, source.start_frame)
            target.end_frame = max(target.end_frame, source.end_frame)
            db.delete(source)

    db.commit()
    return {'status': 'recorded'}




@router.get('/{project_id}/manual-edits')
def list_manual_edits(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(ManualEdit).filter(ManualEdit.project_id == project_id).order_by(ManualEdit.id.desc()).limit(200).all()
    return [
        {
            'id': r.id,
            'user_id': r.user_id,
            'edit_type': r.edit_type,
            'payload': r.payload,
            'created_at': r.created_at.isoformat(),
        }
        for r in rows
    ]

@router.get('/{project_id}/counts')
def counts(project_id: int, db: Session = Depends(get_db)):
    summary = _build_project_summaries(project_id, db)['count_summary']
    return {
        'project_id': project_id,
        'intervals': summary['intervals'],
        'peak_interval': summary['peak_interval'],
        'assumption_note': 'Movement counts are automated detections and should be reviewed before sign-off.',
    }


@router.get('/{project_id}/queues')
def queues(project_id: int, db: Session = Depends(get_db)):
    summary = _build_project_summaries(project_id, db)['queue_summary']
    return {
        'project_id': project_id,
        'queue_summary': 'estimated from tracked occupancy and slow-moving objects',
        **summary,
    }


@router.get('/{project_id}/pedestrians')
def pedestrians(project_id: int, db: Session = Depends(get_db)):
    summary = _build_project_summaries(project_id, db)['ped_summary']
    return {
        'project_id': project_id,
        'crossings': summary['events'],
        'crossing_counts': summary['crossing_counts'],
        'total_crossings': summary['total_crossings'],
        'conflicts': [],
    }


@router.get('/{project_id}/school-mode')
def school_mode(project_id: int, db: Session = Depends(get_db)):
    summaries = _build_project_summaries(project_id, db)
    return {
        'project_id': project_id,
        'drop_off_events': [],
        'flags': summaries['school_flags'],
        'queue_peak': summaries['queue_summary'].get('max_queue', 0),
        'pedestrian_activity': summaries['ped_summary'].get('total_crossings', 0),
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




@router.get('/{project_id}/summary')
def project_summary(project_id: int, db: Session = Depends(get_db)):
    summaries = _build_project_summaries(project_id, db)
    latest_run = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).order_by(AnalysisRun.id.desc()).first()
    latest_export = db.query(EvidenceExport).filter(EvidenceExport.project_id == project_id).order_by(EvidenceExport.id.desc()).first()
    return {
        'project_id': project_id,
        'latest_run': {'id': latest_run.id, 'status': latest_run.status, 'stage': latest_run.stage} if latest_run else None,
        'latest_export': {'id': latest_export.id, 'type': latest_export.export_type, 'path': latest_export.path} if latest_export else None,
        'peak_interval': summaries['count_summary']['peak_interval'],
        'queue_max': summaries['queue_summary'].get('max_queue', 0),
        'total_pedestrians': summaries['ped_summary'].get('total_crossings', 0),
        'school_flags': summaries['school_flags'],
        'alignment_complete_count': len([c for c in summaries['alignment_cards'] if c.get('status') == 'complete']),
        'alignment_total_count': len(summaries['alignment_cards']),
    }



@router.get('/{project_id}/readiness')
def project_readiness(project_id: int, db: Session = Depends(get_db)):
    summaries = _build_project_summaries(project_id, db)
    latest_run = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).order_by(AnalysisRun.id.desc()).first()
    latest_scene = db.query(SceneDefinition).filter(SceneDefinition.project_id == project_id).order_by(SceneDefinition.id.desc()).first()
    latest_video = db.query(Video).filter(Video.project_id == project_id).order_by(Video.id.desc()).first()
    latest_export = db.query(EvidenceExport).filter(EvidenceExport.project_id == project_id).order_by(EvidenceExport.id.desc()).first()

    checks = {
        'video_uploaded': bool(latest_video),
        'scene_configured': bool(latest_scene),
        'analysis_completed': bool(latest_run and latest_run.status == 'completed'),
        'turning_counts_available': bool(summaries['count_summary'].get('intervals')),
        'queue_evidence_available': summaries['queue_summary'].get('max_queue', 0) > 0,
        'pedestrian_evidence_available': summaries['ped_summary'].get('total_crossings', 0) > 0,
        'report_export_available': bool(latest_export),
    }
    missing = [k for k, v in checks.items() if not v]
    return {
        'project_id': project_id,
        'ready_for_professional_review': len(missing) == 0,
        'checks': checks,
        'missing_items': missing,
        'disclaimer': 'Readiness indicates data completeness only. Final engineering sign-off and TMH16 compliance judgment remain professional responsibilities.',
    }

@router.get('/{project_id}/tmh16-alignment')
def tmh16_alignment(project_id: int, db: Session = Depends(get_db)):
    summaries = _build_project_summaries(project_id, db)
    return {
        'project_id': project_id,
        'cards': summaries['alignment_cards'],
        'disclaimer': 'This checklist supports evidence completeness only. Final TMH16 compliance requires professional engineering judgment.',
    }






@router.get('/{project_id}/evidence-manifest')
def evidence_manifest(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')

    videos = db.query(Video).filter(Video.project_id == project_id).order_by(Video.id.asc()).all()
    runs = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).order_by(AnalysisRun.id.asc()).all()
    exports = db.query(EvidenceExport).filter(EvidenceExport.project_id == project_id).order_by(EvidenceExport.id.asc()).all()
    edits = db.query(ManualEdit).filter(ManualEdit.project_id == project_id).order_by(ManualEdit.id.asc()).all()

    manifest = {
        'project_id': project_id,
        'project_name': project.name,
        'videos': [
            {'id': v.id, 'filename': v.filename, 'duration_s': v.duration_s, 'fps': v.fps, 'resolution': v.resolution}
            for v in videos
        ],
        'analysis_runs': [
            {'id': r.id, 'status': r.status, 'stage': r.stage, 'metadata': r.metadata_json}
            for r in runs
        ],
        'exports': [
            {'id': e.id, 'type': e.export_type, 'path': e.path}
            for e in exports
        ],
        'manual_edits': [
            {'id': m.id, 'user_id': m.user_id, 'edit_type': m.edit_type, 'payload': m.payload}
            for m in edits
        ],
        'disclaimer': 'Manifest supports traceability and integrity checks only; final professional engineering judgment remains required.',
    }
    digest_src = json.dumps(manifest, sort_keys=True, default=str).encode('utf-8')
    manifest_hash = hashlib.sha256(digest_src).hexdigest()
    return {'manifest': manifest, 'sha256': manifest_hash}


def _latest_manifest_snapshot_approval(project_id: int, db: Session):
    return db.query(ManualEdit).filter(
        ManualEdit.project_id == project_id,
        ManualEdit.edit_type == 'manifest_snapshot_approved',
    ).order_by(ManualEdit.id.desc()).first()


@router.get('/{project_id}/manifest-drift')
def manifest_drift(project_id: int, db: Session = Depends(get_db)):
    manifest_response = evidence_manifest(project_id, db)
    current_hash = manifest_response['sha256']
    approval = _latest_manifest_snapshot_approval(project_id, db)

    approved_hash = approval.payload.get('sha256') if approval and approval.payload else None
    return {
        'project_id': project_id,
        'current_manifest_sha256': current_hash,
        'approved_manifest_sha256': approved_hash,
        'has_approved_snapshot': bool(approved_hash),
        'drift_detected': bool(approved_hash and approved_hash != current_hash),
        'last_approved_at': approval.created_at.isoformat() if approval else None,
        'disclaimer': 'Snapshot drift signals evidence changes after internal approval. Professional judgment and formal sign-off remain required.',
    }


@router.post('/{project_id}/manifest-snapshot/approve')
def approve_manifest_snapshot(
    project_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles('admin', 'analyst')),
):
    manifest_response = evidence_manifest(project_id, db)
    current_hash = manifest_response['sha256']
    current_state = manifest_drift(project_id, db)

    if current_state['has_approved_snapshot'] and not current_state['drift_detected']:
        return {
            'status': 'unchanged',
            'project_id': project_id,
            'sha256': current_hash,
            'message': 'Current manifest already matches approved snapshot.',
        }

    edit = ManualEdit(
        project_id=project_id,
        user_id=user.id,
        edit_type='manifest_snapshot_approved',
        payload={'sha256': current_hash},
    )
    db.add(edit)
    db.commit()
    return {
        'status': 'approved',
        'project_id': project_id,
        'sha256': current_hash,
        'approved_at': edit.created_at.isoformat(),
    }

@router.get('/{project_id}/final-review')
def final_review_status(project_id: int, db: Session = Depends(get_db)):
    readiness = project_readiness(project_id, db)
    latest_run = db.query(AnalysisRun).filter(AnalysisRun.project_id == project_id).order_by(AnalysisRun.id.desc()).first()
    approve_counts_edit = db.query(ManualEdit).filter(
        ManualEdit.project_id == project_id,
        ManualEdit.edit_type == 'approve_counts',
    ).order_by(ManualEdit.id.desc()).first()
    final_approval = db.query(ManualEdit).filter(
        ManualEdit.project_id == project_id,
        ManualEdit.edit_type == 'final_review_approved',
    ).order_by(ManualEdit.id.desc()).first()

    checks = {
        'analysis_completed': bool(latest_run and latest_run.status == 'completed'),
        'counts_approved': bool(approve_counts_edit),
        'evidence_readiness_complete': bool(readiness.get('ready_for_professional_review')),
        'final_review_approved': bool(final_approval),
    }
    blockers = [k for k, v in checks.items() if not v and k != 'final_review_approved']

    return {
        'project_id': project_id,
        'checks': checks,
        'blockers': blockers,
        'can_issue_draft_pack': len(blockers) == 0,
        'last_counts_approval': approve_counts_edit.created_at.isoformat() if approve_counts_edit else None,
        'last_final_approval': final_approval.created_at.isoformat() if final_approval else None,
        'disclaimer': 'Final review state is an internal workflow marker. Professional engineering judgment and formal sign-off remain required.',
    }


@router.post('/{project_id}/final-review/approve')
def approve_final_review(
    project_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles('admin', 'analyst')),
):
    status = final_review_status(project_id, db)
    if not status['can_issue_draft_pack']:
        raise HTTPException(status_code=400, detail=f"Final review cannot be approved yet. Missing: {status['blockers']}")

    edit = ManualEdit(
        project_id=project_id,
        user_id=user.id,
        edit_type='final_review_approved',
        payload={'approved': True, 'note': 'Final review approved for draft evidence issue'},
    )
    db.add(edit)
    db.commit()
    return {'status': 'approved', 'project_id': project_id, 'approved_at': edit.created_at.isoformat()}



@router.get('/{project_id}/release-readiness')
def release_readiness(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')

    final_status = final_review_status(project_id, db)
    drift_status = manifest_drift(project_id, db)
    latest_export = db.query(EvidenceExport).filter(EvidenceExport.project_id == project_id).order_by(EvidenceExport.id.desc()).first()

    checks = {
        'final_review_approved': bool(final_status['checks'].get('final_review_approved')),
        'approved_manifest_snapshot': bool(drift_status.get('has_approved_snapshot')),
        'manifest_drift_free': not bool(drift_status.get('drift_detected')),
        'has_exports': bool(latest_export),
    }
    blockers = [k for k, v in checks.items() if not v]

    return {
        'project_id': project_id,
        'checks': checks,
        'blockers': blockers,
        'can_issue_draft_pack': len(blockers) == 0,
        'latest_export': {'id': latest_export.id, 'type': latest_export.export_type, 'path': latest_export.path} if latest_export else None,
        'disclaimer': 'Release readiness is an internal workflow control only; professional engineering judgment and formal sign-off remain required.',
    }


@router.post('/{project_id}/release/issue-draft-pack')
def issue_draft_pack(
    project_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles('admin', 'analyst')),
):
    status = release_readiness(project_id, db)
    if not status['can_issue_draft_pack']:
        raise HTTPException(status_code=400, detail=f"Draft pack cannot be issued yet. Missing: {status['blockers']}")

    edit = ManualEdit(
        project_id=project_id,
        user_id=user.id,
        edit_type='draft_pack_issued',
        payload={'release_checks': status['checks']},
    )
    db.add(edit)
    db.commit()
    return {
        'status': 'issued',
        'project_id': project_id,
        'issued_at': edit.created_at.isoformat(),
        'latest_export': status['latest_export'],
    }



@router.get('/{project_id}/release-audit')
def release_audit(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')

    relevant_types = [
        'approve_counts',
        'final_review_approved',
        'manifest_snapshot_approved',
        'draft_pack_issued',
    ]
    events = db.query(ManualEdit).filter(
        ManualEdit.project_id == project_id,
        ManualEdit.edit_type.in_(relevant_types),
    ).order_by(ManualEdit.id.desc()).limit(200).all()

    grouped = {event_type: [] for event_type in relevant_types}
    for event in events:
        grouped[event.edit_type].append(
            {
                'id': event.id,
                'user_id': event.user_id,
                'payload': event.payload,
                'created_at': event.created_at.isoformat(),
            }
        )

    latest = {k: (v[0] if v else None) for k, v in grouped.items()}
    return {
        'project_id': project_id,
        'latest': latest,
        'events': grouped,
        'event_count': len(events),
        'disclaimer': 'Release audit is an internal traceability view and does not replace professional engineering judgment or formal sign-off.',
    }



@router.get('/{project_id}/release-candidate')
def release_candidate(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')

    readiness = release_readiness(project_id, db)
    manifest_state = manifest_drift(project_id, db)
    audit = release_audit(project_id, db)

    candidate = {
        'project_id': project_id,
        'project_name': project.name,
        'can_issue_draft_pack': readiness['can_issue_draft_pack'],
        'latest_export': readiness.get('latest_export'),
        'manifest_sha256': manifest_state.get('current_manifest_sha256'),
        'approved_manifest_sha256': manifest_state.get('approved_manifest_sha256'),
        'governance_timestamps': {
            'counts_approved_at': (audit.get('latest', {}).get('approve_counts') or {}).get('created_at'),
            'final_review_approved_at': (audit.get('latest', {}).get('final_review_approved') or {}).get('created_at'),
            'manifest_snapshot_approved_at': (audit.get('latest', {}).get('manifest_snapshot_approved') or {}).get('created_at'),
            'draft_pack_issued_at': (audit.get('latest', {}).get('draft_pack_issued') or {}).get('created_at'),
        },
        'blockers': readiness.get('blockers', []),
        'disclaimer': 'Release candidate snapshot is a workflow artifact for traceability only; professional engineering judgment and formal sign-off remain required.',
    }
    digest_src = json.dumps(candidate, sort_keys=True, default=str).encode('utf-8')
    candidate['candidate_sha256'] = hashlib.sha256(digest_src).hexdigest()
    return candidate



@router.get('/{project_id}/release-candidate-lock')
def release_candidate_lock(project_id: int, db: Session = Depends(get_db)):
    candidate = release_candidate(project_id, db)
    lock = db.query(ManualEdit).filter(
        ManualEdit.project_id == project_id,
        ManualEdit.edit_type == 'release_candidate_locked',
    ).order_by(ManualEdit.id.desc()).first()

    locked_hash = lock.payload.get('candidate_sha256') if lock and lock.payload else None
    return {
        'project_id': project_id,
        'current_candidate_sha256': candidate.get('candidate_sha256'),
        'locked_candidate_sha256': locked_hash,
        'has_locked_candidate': bool(locked_hash),
        'drift_detected': bool(locked_hash and locked_hash != candidate.get('candidate_sha256')),
        'locked_at': lock.created_at.isoformat() if lock else None,
        'disclaimer': 'Candidate lock drift highlights workflow-state changes after locking; professional engineering sign-off remains required.',
    }


@router.post('/{project_id}/release-candidate-lock')
def approve_release_candidate_lock(
    project_id: int,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_roles('admin', 'analyst')),
):
    lock_state = release_candidate_lock(project_id, db)
    current_hash = lock_state['current_candidate_sha256']

    if lock_state['has_locked_candidate'] and not lock_state['drift_detected']:
        return {
            'status': 'unchanged',
            'project_id': project_id,
            'candidate_sha256': current_hash,
            'message': 'Current release candidate already matches locked snapshot.',
        }

    edit = ManualEdit(
        project_id=project_id,
        user_id=user.id,
        edit_type='release_candidate_locked',
        payload={'candidate_sha256': current_hash},
    )
    db.add(edit)
    db.commit()
    return {
        'status': 'locked',
        'project_id': project_id,
        'candidate_sha256': current_hash,
        'locked_at': edit.created_at.isoformat(),
    }



@router.get('/{project_id}/release-package')
def release_package(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')

    candidate = release_candidate(project_id, db)
    candidate_lock = release_candidate_lock(project_id, db)
    manifest = evidence_manifest(project_id, db)
    manifest_lock = manifest_drift(project_id, db)
    readiness = release_readiness(project_id, db)

    package = {
        'project_id': project_id,
        'project_name': project.name,
        'release_ready': readiness.get('can_issue_draft_pack', False),
        'blockers': readiness.get('blockers', []),
        'candidate_sha256': candidate.get('candidate_sha256'),
        'candidate_locked_sha256': candidate_lock.get('locked_candidate_sha256'),
        'candidate_lock_drift_detected': candidate_lock.get('drift_detected', False),
        'manifest_sha256': manifest.get('sha256'),
        'manifest_approved_sha256': manifest_lock.get('approved_manifest_sha256'),
        'manifest_drift_detected': manifest_lock.get('drift_detected', False),
        'latest_export': readiness.get('latest_export'),
        'disclaimer': 'Release package is an internal traceability bundle for draft evidence handoff and does not replace professional engineering sign-off.',
    }
    digest_src = json.dumps(package, sort_keys=True, default=str).encode('utf-8')
    package['package_sha256'] = hashlib.sha256(digest_src).hexdigest()
    return package

@router.post('/{project_id}/report/generate')
def generate_report(project_id: int, db: Session = Depends(get_db), _: CurrentUser = Depends(require_roles('admin', 'analyst'))):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail='Project not found')

    summaries = _build_project_summaries(project_id, db)
    reports_dir = Path(settings.report_temp_path)
    html_path = reports_dir / f'project_{project_id}_evidence.html'
    csv_path = reports_dir / f'project_{project_id}_turning_counts.csv'
    xlsx_path = reports_dir / f'project_{project_id}_turning_counts.xlsx'

    write_counts_csv(csv_path, summaries['count_summary']['intervals'])
    write_counts_xlsx(xlsx_path, summaries['count_summary']['intervals'])
    write_report_html(
        html_path,
        {
            'project': project,
            'count_summary': summaries['count_summary'],
            'queue_summary': summaries['queue_summary'],
            'ped_summary': summaries['ped_summary'],
            'school_flags': summaries['school_flags'],
            'alignment_cards': summaries['alignment_cards'],
        },
    )

    db.add(EvidenceExport(project_id=project_id, export_type='html', path=str(html_path)))
    db.add(EvidenceExport(project_id=project_id, export_type='csv', path=str(csv_path)))
    db.add(EvidenceExport(project_id=project_id, export_type='xlsx', path=str(xlsx_path)))
    db.commit()
    return {
        'status': 'generated',
        'exports': [
            {'type': 'html', 'path': str(html_path)},
            {'type': 'csv', 'path': str(csv_path)},
            {'type': 'xlsx', 'path': str(xlsx_path)},
        ],
        'disclaimer': 'Draft outputs only. Professional engineering review and sign-off are required.',
    }


@router.get('/{project_id}/exports')
def list_exports(project_id: int, db: Session = Depends(get_db)):
    rows = db.query(EvidenceExport).filter(EvidenceExport.project_id == project_id).all()
    return [{'id': r.id, 'type': r.export_type, 'path': r.path} for r in rows]
