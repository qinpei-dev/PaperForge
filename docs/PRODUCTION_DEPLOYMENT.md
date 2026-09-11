# Production deployment runbook

## Current release facts

This is the production source of truth for deployment facts. As of 2026-09-12,
the target public frontend is `https://aetherislab.xyz` and the browser API base
is `https://aetherislab.xyz/api`. The current P0 release candidate is `v3.7.3`,
with release commit `729fe2f19864a7e80dc590084e0d0becdb04fe71`. The canonical ACR
run reached the login step but was rejected by the current repository ACR secret;
no application image was built or pushed and no ECS change was made. Image
digests, ECS deployment time, migration result and readiness result must be
written here only after the release is actually performed. Until those fields
are recorded from the target runtime, do not describe the candidate as deployed
or production-ready.

The production runtime is Aliyun ECS Docker/Compose. Local Docker Desktop is
only a developer image-build/validation environment. A stopped local Docker
Desktop is not a production incident and must not trigger production Docker
configuration changes.

The historical `ops/acr-build-v3.6` branch/workflow is retired. It checks out an
old commit/IP and omits required frontend public build arguments. Do not reuse
it. Use the canonical `.github/workflows/acr-build-paperforge.yml` or the
equivalent `scripts/build_and_push_acr.ps1` runner.

Before a frontend image can be published, the build log/configuration must show
all three build-time arguments:

```text
NEXT_PUBLIC_API_BASE_URL=https://aetherislab.xyz/api
NEXT_PUBLIC_PAPERFORGE_PREVIEW_AUTO_LOGIN=false
NEXT_PUBLIC_PAPERFORGE_APP_ENV=production
```

The frontend image must be inspected for the production API URL and absence of
`http://localhost:8000` before ECS pulls it. `docker-compose.prod.yml` consumes
prebuilt images and intentionally does not inject `NEXT_PUBLIC_*` at runtime.

This runbook deploys immutable images through `docker-compose.prod.yml`; it does not use local build context or `latest` as a release source.

1. On the production host, check out the intended release runbook and create a protected environment file from `.env.production.example` outside Git.
2. Verify the immutable backend/frontend image references, release tag, public API URL, CORS origin, and persistent Docker volumes. Build `NEXT_PUBLIC_API_BASE_URL` into the frontend image before publishing it; Next.js public variables are compiled into the image and cannot be changed by the production Compose runtime.
3. Run `scripts/backup_postgres.ps1` (or the equivalent host command), verify the backup exists and is non-empty, then record the current `alembic current` revision.
4. Pull immutable images: `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml pull`.
5. Run the forward migration using the backend image: `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml run --rm backend alembic upgrade head`. Verify `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml run --rm backend alembic current` is `0012_day17_token_version`. Do not run production downgrade automatically.
6. Start services with `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml up -d`; verify PostgreSQL, backend health, frontend route, authentication, active workspace task views, SSE, and artifact download.
7. Monitor logs for migration errors, repeated 500s, auth failures, and secret exposure.

Application rollback means restarting the previously recorded immutable backend/frontend images with the existing volumes. Database restore is separate, high risk, and only follows a verified backup plus an operator-reviewed restoration plan. A forward migration may not be compatible with a prior application image; do not treat database downgrade as routine rollback.

The public edge must supply TLS, a public frontend domain, a backend API route, forwarded headers (`Host`, `X-Forwarded-For`, `X-Forwarded-Proto`), adequate upload/download limits, and SSE-compatible buffering/timeouts. A reproducible Nginx example is provided at `deploy/nginx/paperforge.conf`; review hostnames and certificate paths before use. Route browser API, SSE, and artifact-download traffic to the backend without response buffering; retain streaming connections long enough for task events. The repository does not prescribe Kubernetes, HA, or autoscaling.

The environment contract is intentionally split: PostgreSQL credentials (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`) construct the backend `DATABASE_URL` inside Compose; `JWT_SECRET_KEY`, `APP_ENV=production`, `AUTH_REQUIRED=true`, `CORS_ORIGINS`, and optional `DEEPSEEK_*` configure the backend. `PAPERFORGE_RELEASE_VERSION` must match the backend/frontend image tag and is applied as a label to all three services; `PAPERFORGE_*_IMAGE` must be immutable image references. `NEXT_PUBLIC_API_BASE_URL` is a frontend **build-time** contract, and `CORS_ORIGINS` is the matching runtime browser-origin allowlist. Local filesystem storage paths remain `/app/uploads`, `/app/outputs`, `/app/template_storage`, `/app/task_states`, and `/app/templates`, each mounted to a named volume.

Repository documents may record secret names, purposes and whether they are
required. They must never record secret values, AccessKeys, passwords, tokens,
JWT secret material, private keys or other production credentials.

## File lifecycle maintenance

Classification uploads are deleted immediately after classification. Task input uploads are retained for retry compatibility and output files referenced by `Artifact` rows are formal deliverables. Run `python scripts/cleanup_orphan_files.py` as a dry-run maintenance check; review candidates and use `--apply` only in an approved maintenance window. The default retention is 30 days and is configurable with `PAPERFORGE_RETENTION_DAYS`. The command never deletes files referenced by a Task or Artifact row.
# Day11 Durable Task Runtime

`tasks` and `task_events` in PostgreSQL are the authoritative source for SaaS task lifecycle and replayable SSE history. The JSON task-state file remains a compatibility artifact for the document pipeline and must not be used to decide a production task's state.

On backend startup, every persisted `running` task is treated as orphaned because the in-process worker cannot safely resume DOCX execution. It is transitioned to `interrupted`, with a `backend_restart` reason, detection timestamp, and the prior worker run identity. This is intentional: PaperForge currently has no verified checkpoint/resume semantics.

SSE clients may reconnect with `Last-Event-ID`; the server authorizes the task against the selected tenant and replays only later tenant-scoped rows from `task_events`. Production operators must run the current Alembic head `0012_day17_token_version` before deploying the backend image; it includes the durable runtime and token-version migrations.

# Day12 Security Baseline

Production startup requires `AUTH_REQUIRED=true`, a non-placeholder `JWT_SECRET_KEY` of at least 32 characters, and an explicit `CORS_ORIGINS` public origin. Do not expose PostgreSQL outside the internal Docker network; database credentials and application secrets must be injected by the deployment environment, never committed.

All task, event, template and artifact API reads are tenant-scoped. Outputs are not statically mounted: filename download, preview and confirmation routes resolve a tenant-authorized artifact before opening a local file. DOCX upload validation checks filename, extension, MIME, container structure, archive entry count, compressed upload size and bounded uncompressed expansion.

The bundled rate limit is intentionally a single-process guard for login, upload and Agent request bursts. The Nginx public-edge example additionally applies a per-IP rate limit, but neither control is a complete WAF or distributed DDoS service. The current frontend stores bearer tokens in localStorage, so a later httpOnly-cookie/session design remains a defense-in-depth improvement. JWTs carry a database-backed `token_version`; `POST /auth/revoke-sessions` invalidates all existing tokens for that user and requires a fresh login.
