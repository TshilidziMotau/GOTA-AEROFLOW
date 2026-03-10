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

## Phase 3 currently implemented
- Queue duration/peak summaries from persisted queue events
- Pedestrian crossing summaries and school mode risk flags
- Parking stop/dwell event summaries and turnover estimate
- TMH16 alignment summary endpoint (`GET /projects/{id}/tmh16-alignment`)

## Phase 4 currently implemented
- Draft evidence pack generation endpoint with HTML report and CSV/XLSX turning exports
- Export records persisted and available via `GET /projects/{id}/exports`
- Report generation UI to trigger and review generated export artifacts

## Phase 5 currently implemented
- Video management API/UI for upload + metadata listing per project
- Scene setup API/UI with persisted calibration/geometry JSON editor
- Manual QA enhancements: track reclassify, delete, and merge controls from detection review UI
- Extended API spec documenting full phase progression endpoints

## Phase 6 currently implemented
- Seeded admin bootstrap on API startup using `ADMIN_EMAIL` / `ADMIN_PASSWORD`
- Credential verification with bcrypt hashing + JWT role claims
- Protected `/projects/*` endpoints with bearer-token auth and role checks for mutating actions
- Frontend login persists token and API client sends bearer headers automatically

## Phase 7 currently implemented
- Added authenticated session introspection endpoint (`GET /auth/me`)
- Protected analysis endpoints with bearer auth and role checks
- Added settings page session visibility and explicit sign-out control

## Phase 8 currently implemented
- Added analysis review-state endpoint to mark runs as review-needed/completed/failed with audit logging
- Added manual edit audit-trail endpoint (`GET /projects/{id}/manual-edits`)
- Detection review UI now displays manual edit history for defensible QA traceability
- Counts dashboard supports explicit “approve counts” action captured in audit trail

## Phase 9 currently implemented
- Added project summary endpoint (`GET /projects/{id}/summary`) for operational dashboard KPIs
- Added analysis retry endpoint (`POST /projects/{id}/analysis/{run_id}/retry`)
- Dashboard now supports run/retry/review-needed actions with live operational summary

## Phase 10 currently implemented
- Added analysis governance audit endpoint (`GET /projects/{id}/analysis/audit`)
- Dashboard now includes per-run governance controls (mark review-needed/completed/failed)
- Dashboard now surfaces governance event history for operational traceability

## Phase 11 currently implemented
- Added project readiness endpoint (`GET /projects/{id}/readiness`) for evidence completeness checks
- Dashboard now surfaces readiness state and missing evidence items
- Readiness includes explicit disclaimer that final engineering sign-off is still required

## Phase 12 currently implemented
- Added final-review governance endpoint (`GET /projects/{id}/final-review`) with blocker checks
- Added final-review approval action (`POST /projects/{id}/final-review/approve`) gated by readiness
- Dashboard now exposes final-review state, blockers, and approval control

## Phase 13 currently implemented
- Added evidence manifest endpoint (`GET /projects/{id}/evidence-manifest`)
- Manifest includes videos, runs, exports, manual edits and a SHA-256 integrity hash
- Dashboard now surfaces manifest hash for defensible evidence traceability


## Phase 14 currently implemented
- Added manifest drift endpoint (`GET /projects/{id}/manifest-drift`) to compare current evidence hash against approved snapshot
- Added manifest snapshot approval action (`POST /projects/{id}/manifest-snapshot/approve`) with audit persistence
- Dashboard now surfaces snapshot status, drift detection and approval control


## Phase 15 currently implemented
- Added release readiness endpoint (`GET /projects/{id}/release-readiness`) combining final-review, manifest snapshot/drift, and export availability checks
- Added draft-pack issue action (`POST /projects/{id}/release/issue-draft-pack`) with readiness gating and audit capture
- Dashboard now surfaces release readiness blockers and an explicit issue-draft-pack control



## Phase 16 currently implemented
- Added release governance audit endpoint (`GET /projects/{id}/release-audit`) that aggregates the key release-control events
- Dashboard now surfaces latest governance timestamps for counts approval, final review approval, manifest snapshot approval, and draft-pack issue
- Release audit includes explicit workflow disclaimer for professional sign-off boundaries



## Phase 17 currently implemented
- Added release candidate endpoint (`GET /projects/{id}/release-candidate`) that composes readiness, manifest state, and governance timestamps into a single snapshot
- Release candidate response includes deterministic `candidate_sha256` to support handoff traceability of draft-pack state
- Dashboard now surfaces the release candidate snapshot hash and readiness state



## Phase 18 currently implemented
- Added release candidate lock status endpoint (`GET /projects/{id}/release-candidate-lock`) to detect drift between current and locked release candidate snapshots
- Added release candidate lock action (`POST /projects/{id}/release-candidate-lock`) with idempotent behavior and audit persistence
- Dashboard now surfaces lock state and explicit lock action for release candidate snapshots



## Phase 19 currently implemented
- Added release package endpoint (`GET /projects/{id}/release-package`) to aggregate release readiness, candidate/manifest lock state, and latest export into a single traceability bundle
- Release package response includes deterministic `package_sha256` fingerprint for handoff integrity checks
- Dashboard now surfaces release package fingerprint and lock-drift indicators



## Phase 20 currently implemented
- Added release package export endpoint (`GET /projects/{id}/release-package/export`) to return a deterministic JSON payload for handoff tooling
- Dashboard now surfaces release package export status and a copy-to-clipboard action for JSON package content
- Export payload retains explicit draft-evidence disclaimer and package fingerprint linkage



## Phase 21 currently implemented
- Updated web runtime scripts to bind `0.0.0.0` and honor `PORT` (`next ... -p ${PORT:-3000}`) for managed platforms
- Updated `apps/web/Dockerfile` to build for production and run `npm run start` instead of `npm run dev`
- This avoids startup crash loops caused by dev-mode boot and fixed-port mismatches on Zeabur-style deployments



## Phase 22 currently implemented
- Normalized web runtime defaults to `PORT=8080` for both `dev` and `start` scripts to match Zeabur expectations
- Updated web Dockerfile to expose/bind `8080` with production build + `next start` runtime
- Added Zeabur web deployment checklist to prevent root-path and runtime-command misconfiguration that causes 502s



## Phase 23 currently implemented
- Simplified `apps/web` scripts to a single canonical set (`dev`, `build`, `start`, `lint`) with no duplicate script definitions
- Removed `-H` host flag from Next.js scripts and standardized runtime to `next start -p ${PORT:-8080}` for Zeabur
- Added explicit Next.js host/port troubleshooting notes in Zeabur deployment docs



## Phase 24 currently implemented
- Added a canonical root-level `Dockerfile.zeabur-web` for deploying `apps/web` without monorepo root package assumptions
- Expanded Zeabur deployment docs with an explicit safe Dockerfile and anti-pattern warnings (no build-time source rewriting, no invalid workspace assumptions)
- Clarified stable runtime expectation for managed deploys: single `npm run start` command on `PORT=8080`

## Zeabur deployment
See `docs/deployment-zeabur.md`.

## Future roadmap (v2)
- Higher-fidelity queue estimation with lane-level calibration
- Semi-automated conflict classification improvement
- Multi-camera stitching/orientation support
- More advanced manual QA diff/versioning

## Safety note
All outputs are draft technical evidence and must be reviewed and signed off by a qualified professional traffic engineer.
