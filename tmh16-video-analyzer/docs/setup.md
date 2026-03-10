# Setup

## Requirements
- Docker + Docker Compose
- Node 20+
- Python 3.11+

## Environment
Use `infra/env.examples` to create:
- `apps/api/.env`
- `apps/web/.env.local`

## Boot local stack
```bash
cd infra
docker compose up --build
```
