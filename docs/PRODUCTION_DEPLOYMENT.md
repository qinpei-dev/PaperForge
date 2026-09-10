# Production deployment runbook

This runbook deploys immutable images through `docker-compose.prod.yml`; it does not use local build context or `latest` as a release source.

1. On the production host, check out the intended release runbook and create a protected environment file from `.env.production.example` outside Git.
2. Verify the immutable backend/frontend image references, release tag, public API URL, CORS origin, and persistent Docker volumes. Build `NEXT_PUBLIC_API_BASE_URL` into the frontend image before publishing it; Next.js public variables are compiled into the image and cannot be changed by the production Compose runtime.
3. Run `scripts/backup_postgres.ps1` (or the equivalent host command), verify the backup exists and is non-empty, then record the current `alembic current` revision.
4. Pull immutable images: `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml pull`.
5. Run the forward migration using the backend image: `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml run --rm backend alembic upgrade head`. Verify `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml run --rm backend alembic current` is `0009_day10_ownership_audit_settings`. Do not run production downgrade automatically.
6. Start services with `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml up -d`; verify PostgreSQL, backend health, frontend route, authentication, active workspace task views, SSE, and artifact download.
7. Monitor logs for migration errors, repeated 500s, auth failures, and secret exposure.

Application rollback means restarting the previously recorded immutable backend/frontend images with the existing volumes. Database restore is separate, high risk, and only follows a verified backup plus an operator-reviewed restoration plan. A forward migration may not be compatible with a prior application image; do not treat database downgrade as routine rollback.

The public edge must supply TLS, a public frontend domain, a backend API route, forwarded headers (`Host`, `X-Forwarded-For`, `X-Forwarded-Proto`), adequate upload/download limits, and SSE-compatible buffering/timeouts. Route browser API, SSE, and artifact-download traffic to the backend without response buffering; retain streaming connections long enough for task events. The repository does not prescribe Nginx, Caddy, Kubernetes, HA, or autoscaling.

The environment contract is intentionally split: PostgreSQL credentials (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`) construct the backend `DATABASE_URL` inside Compose; `JWT_SECRET_KEY`, `APP_ENV=production`, `AUTH_REQUIRED=true`, `CORS_ORIGINS`, and optional `DEEPSEEK_*` configure the backend. `PAPERFORGE_*_IMAGE` must be immutable image references. `NEXT_PUBLIC_API_BASE_URL` is a frontend **build-time** contract, and `CORS_ORIGINS` is the matching runtime browser-origin allowlist. Local filesystem storage paths remain `/app/uploads`, `/app/outputs`, `/app/template_storage`, `/app/task_states`, and `/app/templates`, each mounted to a named volume.
