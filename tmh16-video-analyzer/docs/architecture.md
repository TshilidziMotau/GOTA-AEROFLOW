# Architecture

## Overview
- **Web**: Next.js App Router UI for project setup, scene calibration, QA, dashboards, reporting.
- **API**: FastAPI with SQLAlchemy models, JWT auth, async job enqueue endpoints.
- **Worker**: Celery worker for ingestion and analysis stages.
- **Data**: PostgreSQL for relational project/evidence records; Redis for job broker.
- **CV pipeline**: OpenCV + pluggable detector/tracker interfaces (YOLO/ByteTrack placeholders in MVP).

## Pipeline
1. Upload video metadata + file.
2. Preprocess (ffprobe/ffmpeg extraction hooks).
3. Detection/tracking.
4. Event extraction (crossings/turns/queues/pedestrian/parking/school).
5. Aggregation and TMH16 rule checklist.
6. Export/report generation.

## Trust & defensibility
- Every auto output remains reviewable.
- Manual edits stored with audit trail.
- Report includes assumptions and professional-review disclaimer.
