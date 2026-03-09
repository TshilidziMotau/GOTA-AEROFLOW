# Zeabur Deployment

## Services
1. `web` (Next.js)
2. `api` (FastAPI)
3. `worker` (Celery)
4. `postgres`
5. `redis` (optional but recommended)

## Required env vars
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `SECRET_KEY`
- `NEXT_PUBLIC_API_URL`
- `STORAGE_PATH`
- `REPORT_TEMP_PATH`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

## Notes
- Set persistent storage for uploaded media and generated artifacts.
- Route `NEXT_PUBLIC_API_URL` to your Zeabur API domain.
- Ensure worker has access to same DB and storage path as API.
