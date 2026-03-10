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


## Web service checklist (to avoid 502)
- Set the **service root/workdir** to `tmh16-video-analyzer/apps/web` (or equivalent path in your repo view).
- Ensure startup binds `0.0.0.0` and uses Zeabur `PORT` (defaulted here to `8080`).
- Do not run `next dev` in production containers; build first and run `next start`.
- If build succeeds but runtime logs are empty, verify the deployed image command is `npm run start` and not overridden in the dashboard.


## Next.js CLI host/port notes
- Use `next start -p ${PORT:-8080}` for runtime on Zeabur.
- Avoid duplicate `scripts` keys/entries in `package.json`; only one `start` script should exist.
- If runtime crashes immediately after successful build, verify the effective start command in container logs.


## Recommended Zeabur web Dockerfile
Use `Dockerfile.zeabur-web` at repository root and avoid mutating source files during build.

```dockerfile
FROM node:20-alpine

WORKDIR /app
COPY apps/web/package.json ./package.json
RUN npm install
COPY apps/web/. .

ENV NODE_ENV=production
ENV PORT=8080

RUN npm run build
EXPOSE 8080
CMD ["npm", "run", "start"]
```

### Important
- Do **not** inject `cat > .../app/projects/[id]/page.tsx` (or similar) in Docker build steps.
- Do **not** mix `pnpm` workspace assumptions unless a root workspace file/package manifest exists.
- Keep one clear runtime command: `npm run start`.


## If you see "import/export cannot be used outside module code"
- This usually indicates the file content was mutated during build (for example by an injected `cat > ...page.tsx` step).
- Remove all custom source-rewrite commands from Zeabur build spec and rely on the repository Dockerfile only.
- Re-deploy from a clean commit where `apps/web/app/video-upload/page.tsx` has imports only at the top of the file.
