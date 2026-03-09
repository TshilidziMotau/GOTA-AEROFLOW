# API Spec (MVP)

## Auth
- `POST /auth/login`

## Projects
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`

## Video + Scene
- `POST /projects/{project_id}/videos`
- `POST /projects/{project_id}/scene`

## Analysis
- `POST /projects/{project_id}/analysis/run`
- `GET /projects/{project_id}/analysis/status`

## Outputs
- `GET /projects/{project_id}/counts`
- `GET /projects/{project_id}/queues`
- `GET /projects/{project_id}/pedestrians`
- `GET /projects/{project_id}/school-mode`
- `GET /projects/{project_id}/parking`
- `POST /projects/{project_id}/manual-corrections`
- `POST /projects/{project_id}/report/generate`
- `GET /projects/{project_id}/exports`
