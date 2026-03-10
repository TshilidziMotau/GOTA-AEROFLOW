# API Spec (MVP+ Extended Phases)

## Auth
- `POST /auth/login`
- `GET /auth/me`

## Projects
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`

## Video + Scene + Review
- `POST /projects/{project_id}/videos`
- `GET /projects/{project_id}/videos`
- `POST /projects/{project_id}/scene`
- `GET /projects/{project_id}/scene`
- `GET /projects/{project_id}/tracks`
- `POST /projects/{project_id}/manual-corrections`
  - `reclassify_track`
  - `delete_track`
  - `merge_tracks`
  - `approve_counts`
- `GET /projects/{project_id}/manual-edits`

## Analysis
- `POST /projects/{project_id}/analysis/run`
  - payload: `{ "frame_skip": 3, "confidence_threshold": 0.4 }`
- `GET /projects/{project_id}/analysis/status`
- `GET /projects/{project_id}/analysis/audit`
- `POST /projects/{project_id}/analysis/{run_id}/review` (`review_needed` | `completed` | `failed`)
- `POST /projects/{project_id}/analysis/{run_id}/retry`

## Outputs
- `GET /projects/{project_id}/counts`
- `GET /projects/{project_id}/queues`
- `GET /projects/{project_id}/pedestrians`
- `GET /projects/{project_id}/school-mode`
- `GET /projects/{project_id}/parking`
- `GET /projects/{project_id}/tmh16-alignment`
- `POST /projects/{project_id}/report/generate` (creates HTML + CSV + XLSX draft evidence exports)
- `GET /projects/{project_id}/exports`
- `GET /projects/{project_id}/summary`
- `GET /projects/{project_id}/readiness`
- `GET /projects/{project_id}/final-review`
- `GET /projects/{project_id}/evidence-manifest`
- `GET /projects/{project_id}/manifest-drift`
- `POST /projects/{project_id}/final-review/approve`
- `POST /projects/{project_id}/manifest-snapshot/approve`
- `GET /projects/{project_id}/release-readiness`
- `POST /projects/{project_id}/release/issue-draft-pack`
- `GET /projects/{project_id}/release-audit`
- `GET /projects/{project_id}/release-candidate`
- `GET /projects/{project_id}/release-candidate-lock`
- `POST /projects/{project_id}/release-candidate-lock`
- `GET /projects/{project_id}/release-package`
- `GET /projects/{project_id}/release-package/export`

## Authentication
- All `/projects/*` endpoints require `Authorization: Bearer <token>`.
- Login via `POST /auth/login` with seeded admin credentials from environment.

## Notes
- Queue and parking analytics are estimated from tracked occupancy and movement persistence.
- Report generation produces draft technical evidence only.
- Automated detections are draft evidence and require professional analyst review and sign-off.
