# API Spec (MVP+ Phase 2)

## Auth
- `POST /auth/login`

## Projects
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`

## Video + Scene + Review
- `POST /projects/{project_id}/videos`
- `POST /projects/{project_id}/scene`
- `GET /projects/{project_id}/tracks`
- `POST /projects/{project_id}/manual-corrections`

## Analysis
- `POST /projects/{project_id}/analysis/run`
  - payload: `{ "frame_skip": 3, "confidence_threshold": 0.4 }`
- `GET /projects/{project_id}/analysis/status`

## Outputs
- `GET /projects/{project_id}/counts`
- `GET /projects/{project_id}/queues`
- `GET /projects/{project_id}/pedestrians`
- `GET /projects/{project_id}/school-mode`
- `GET /projects/{project_id}/parking`
- `POST /projects/{project_id}/report/generate`
- `GET /projects/{project_id}/exports`

## Notes
Automated detections are draft evidence and require professional analyst review and sign-off.
