# TMH16 Video Analyzer

TMH16 Video Analyzer is a production-oriented MVP that converts drone traffic survey video into **structured evidence** for South African TMH 16-style TIA/STA workflows.

## Who it is for
- Traffic engineers
- Transport planners
- Mobility consultants

## What it does
- Upload and manage drone survey videos (`.mp4`)
- Define calibrated scene geometry and count/queue/pedestrian/school zones
- Run asynchronous analysis pipelines (detection/tracking/event extraction)
- Produce turning counts, queue summaries, pedestrian/school/parking outputs
- Generate TMH16 alignment checklist status cards
- Export CSV/XLSX and generate draft PDF evidence packs

## What TMH16 alignment means in this app
The app provides a **structured checklist and evidence completeness layer**, not legal certification.

## What this app does not do
- Does **not** guarantee TMH16 compliance
- Does **not** provide municipal or legal sign-off
- Does **not** replace professional engineering judgment

## Monorepo layout
- `apps/web` - Next.js frontend
- `apps/api` - FastAPI backend + worker logic
- `packages/shared-types` - shared API/data contracts
- `packages/tmh16-rules` - TMH16 checklist engine
- `packages/report-templates` - report templates
- `infra` - local Docker compose and env examples
- `docs` - architecture/setup/deployment/API docs

## Local setup
1. Copy env file examples and set values.
2. Start stack:
   ```bash
   cd tmh16-video-analyzer/infra
   docker compose up --build
   ```
3. Web: `http://localhost:3000`
4. API docs: `http://localhost:8000/docs`

## Running services directly
- Frontend:
  ```bash
  cd apps/web
  npm install
  npm run dev
  ```
- API:
  ```bash
  cd apps/api
  pip install -r requirements.txt
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
- Worker:
  ```bash
  cd apps/api
  celery -A app.workers.celery_app worker -l info
  ```


## Phase 2 currently implemented
- Basic OpenCV background-subtraction detection and centroid tracking in worker pipeline
- Persisted `tracks`, `turning_events`, `queue_events`, `pedestrian_events`, `parking_events` tables
- 15-minute interval movement aggregation from turning events
- Detection review API (`GET /projects/{id}/tracks`) and manual reclassify support

## Zeabur deployment
See `docs/deployment-zeabur.md`.

## Future roadmap (v2)
- Higher-fidelity queue estimation with lane-level calibration
- Semi-automated conflict classification improvement
- Multi-camera stitching/orientation support
- More advanced manual QA diff/versioning

## Safety note
All outputs are draft technical evidence and must be reviewed and signed off by a qualified professional traffic engineer.
