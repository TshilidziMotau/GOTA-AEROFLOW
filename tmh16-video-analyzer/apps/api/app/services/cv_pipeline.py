from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cv2
from sqlalchemy.orm import Session

from app.models.models import (
    AnalysisRun,
    ParkingEvent,
    PedestrianEvent,
    Project,
    QueueEvent,
    SceneDefinition,
    Track,
    TurningEvent,
    Video,
)


@dataclass
class TrackState:
    temp_id: int
    cls: str
    points: list[tuple[int, int, float, int]]
    last_seen_frame: int


def _dist(a: tuple[int, int], b: tuple[int, int]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _line_side(point: tuple[int, int], p1: tuple[int, int], p2: tuple[int, int]) -> float:
    return (p2[0] - p1[0]) * (point[1] - p1[1]) - (p2[1] - p1[1]) * (point[0] - p1[0])


def run_pipeline(db: Session, run_id: int) -> dict:
    run = db.get(AnalysisRun, run_id)
    if not run:
        return {'status': 'failed', 'reason': 'run_not_found'}

    project = db.get(Project, run.project_id)
    video = db.query(Video).filter(Video.project_id == run.project_id).order_by(Video.id.desc()).first()
    scene = db.query(SceneDefinition).filter(SceneDefinition.project_id == run.project_id).order_by(SceneDefinition.id.desc()).first()

    if not project or not video:
        run.status = 'failed'
        run.stage = 'failed'
        run.metadata_json = {'reason': 'missing_project_or_video'}
        db.commit()
        return {'status': 'failed'}

    run.status = 'processing'
    run.stage = 'detection_tracking'
    db.commit()

    cap = cv2.VideoCapture(str(Path(video.path)))
    if not cap.isOpened():
        run.status = 'failed'
        run.stage = 'failed'
        run.metadata_json = {'reason': 'video_open_failed'}
        db.commit()
        return {'status': 'failed'}

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_skip = int((run.metadata_json or {}).get('frame_skip', 3))
    bg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=36, detectShadows=True)

    active: dict[int, TrackState] = {}
    completed_tracks: list[TrackState] = []
    next_id = 1
    frame_idx = 0
    queue_events = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % frame_skip != 0:
            continue

        fg = bg.apply(frame)
        fg = cv2.GaussianBlur(fg, (5, 5), 0)
        _, th = cv2.threshold(fg, 200, 255, cv2.THRESH_BINARY)
        th = cv2.morphologyEx(th, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))

        contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        detections: list[tuple[int, int, str]] = []
        for c in contours:
            area = cv2.contourArea(c)
            if area < 220:
                continue
            x, y, w, h = cv2.boundingRect(c)
            cx, cy = x + w // 2, y + h // 2
            if area < 1300:
                obj_cls = 'pedestrian'
            elif area < 3500:
                obj_cls = 'car'
            elif area < 7000:
                obj_cls = 'minibus_taxi'
            else:
                obj_cls = 'heavy_truck'
            obj_cls = 'pedestrian' if area < 1300 else 'car'
            detections.append((cx, cy, obj_cls))

        used_tracks: set[int] = set()
        for cx, cy, cls in detections:
            chosen = None
            best = 999999.0
            for tid, state in active.items():
                if tid in used_tracks:
                    continue
                d = _dist((cx, cy), (state.points[-1][0], state.points[-1][1]))
                if d < 45 and d < best:
                    best, chosen = d, tid
            t = frame_idx / fps
            if chosen is None:
                active[next_id] = TrackState(temp_id=next_id, cls=cls, points=[(cx, cy, t, frame_idx)], last_seen_frame=frame_idx)
                used_tracks.add(next_id)
                next_id += 1
            else:
                active[chosen].points.append((cx, cy, t, frame_idx))
                active[chosen].last_seen_frame = frame_idx
                used_tracks.add(chosen)

        for tid in list(active.keys()):
            if frame_idx - active[tid].last_seen_frame > 30:
                completed_tracks.append(active[tid])
                del active[tid]

        queue_estimate = sum(1 for t in active.values() if len(t.points) > 2 and _dist((t.points[-1][0], t.points[-1][1]), (t.points[-3][0], t.points[-3][1])) < 8)
        if queue_estimate > 0:
            db.add(QueueEvent(project_id=run.project_id, run_id=run.id, occupied_count=queue_estimate, event_time_s=frame_idx / fps))
            queue_events += 1

    cap.release()

    run.stage = 'event_extraction'
    db.commit()

    scene_lines = []
    if scene and isinstance(scene.config, dict):
        scene_lines = scene.config.get('count_lines', [])

    stored_tracks = 0
    turning_events = 0
    pedestrian_events = 0
    parking_events = 0

    completed_tracks.extend(active.values())

    for st in completed_tracks:
        if len(st.points) < 2:
            continue
        db_track = Track(
            project_id=run.project_id,
            run_id=run.id,
            object_class=st.cls,
            confidence_avg=0.55,
            start_frame=st.points[0][3],
            end_frame=st.points[-1][3],
            path=[[p[0], p[1], p[2]] for p in st.points],
        )
        db.add(db_track)
        db.flush()
        stored_tracks += 1

        for line in scene_lines:
            p1 = tuple(line.get('p1', [0, 0]))
            p2 = tuple(line.get('p2', [0, 0]))
            name = line.get('name', 'count_line')
            prev = _line_side((st.points[0][0], st.points[0][1]), p1, p2)
            for px, py, t, _ in st.points[1:]:
                cur = _line_side((px, py), p1, p2)
                if prev == 0:
                    prev = cur
                    continue
                if cur == 0 or (prev < 0 < cur) or (prev > 0 > cur):
                    db.add(TurningEvent(project_id=run.project_id, run_id=run.id, track_id=db_track.id, movement=f'cross_{name}', event_time_s=t))
                    turning_events += 1
                    break
                prev = cur

        if st.cls == 'pedestrian':
            db.add(PedestrianEvent(project_id=run.project_id, run_id=run.id, track_id=db_track.id, crossing_name='observed', event_time_s=st.points[-1][2]))
            pedestrian_events += 1


        if st.cls in {'car', 'minibus_taxi', 'heavy_truck'} and len(st.points) >= 6:
            start = st.points[0]
            end = st.points[-1]
            displacement = _dist((start[0], start[1]), (end[0], end[1]))
            dwell = max(0.0, end[2] - start[2])
            if displacement < 25 and dwell >= 8:
                db.add(ParkingEvent(project_id=run.project_id, run_id=run.id, zone_name='detected_stop_zone', event_type='stop', dwell_s=dwell))
                parking_events += 1

    run.status = 'completed'
    run.stage = 'completed'
    run.metadata_json = {
        'stored_tracks': stored_tracks,
        'turning_events': turning_events,
        'queue_events': queue_events,
        'pedestrian_events': pedestrian_events,
        'parking_events': parking_events,
        'note': 'Automated detections are draft evidence and require analyst review.',
    }
    db.commit()
    return run.metadata_json
