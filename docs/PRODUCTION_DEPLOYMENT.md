# Production deployment runbook

## Current release facts

This is the production source of truth for deployment facts. As of 2026-09-12,
the target public frontend is `https://aetherislab.xyz` and the browser API base
is `https://aetherislab.xyz/api`. Release `v3.7.5` was built from commit
`4ca4bf29a1eee67f05bcdd6c7b5dfd8a0841a018`, published by canonical ACR run
`34678107681`, and deployed to Aliyun ECS. The production runtime is operational;
the final public-beta gate is **READY FOR CONTROLLED PUBLIC BETA** after the
2026-09-12 authenticated production audit.

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

## Current ECS runtime snapshot

- ACR workflow run: `34678107681` (success); the prior runs are historical.
- Backend image: `crpi-z345rofd99au0che.cn-chengdu.personal.cr.aliyuncs.com/paperforge/paperforge-backend:v3.7.5@sha256:27522b2f2c04010c657d03d30e3e741abd17843700df04241ed6853f3c1167c8`.
- Frontend image: `crpi-z345rofd99au0che.cn-chengdu.personal.cr.aliyuncs.com/paperforge/paperforge-frontend:v3.7.5@sha256:40f26beb77117a434f002e498c20abdd69ef24b3e4ed7bd224b67378617acb09`.
- ACR frontend layer scan: production API URL present; localhost and loopback API URLs absent; all three production build args were present in the workflow logs.
- ECS host: `47.109.185.251`, deployment directory `/opt/paperforge`; backend container created `2026-09-11T20:08:31Z`, frontend container created `2026-09-11T20:07:23Z`.
- Migration: `0013_beta_feedback (head)`; explicit `upgrade head` completed before the runtime update.
- Runtime probes after deployment and JWT rotation: internal/public health, readiness and public homepage all returned HTTP 200; backend and PostgreSQL health were healthy. The historical frontend Compose file has no container healthcheck, so its public HTTP 200 is the route health signal.
- Data safety: PostgreSQL image/container and named volume were retained. Existing bind mounts `/opt/paperforge-data/uploads`, `/opt/paperforge-data/outputs`, and `/opt/paperforge-data/template_storage` were retained; no database, volume, or production data was deleted or rebuilt. A non-empty PostgreSQL custom-format pre-release dump was stored in the ECS deployment backup directory; only its metadata belongs in project records.
- Secrets: repository ACR secret names `ACR_USERNAME` and `ACR_PASSWORD` were refreshed through encrypted secret management; `JWT_SECRET_KEY` was rotated after stable deployment without recording its value. `POSTGRES_PASSWORD` was not changed. On 2026-09-12 `DEEPSEEK_API_KEY` was configured through a loopback-only, no-echo input flow after two isolated fake-value HTTP 200 self-tests; the fake value never entered production. Compose injection matched the protected `.env` value exactly, backend was recreated, and a production-container AI Agent smoke returned `language_mode_ai=true`, `ai_used=true`, and a non-null AI score. Health/readiness and log/Secret-leak checks passed. No credential value is recorded here or elsewhere in the repository.
- Programmatic audit: authenticated feedback submit returned 201 and was found in PostgreSQL; unauthenticated feedback returned 401; ordinary user `/admin/feedback` returned 403; Local task, SSE, preview, usage and non-empty valid DOCX download all passed. On 2026-09-12 production `.env` was backed up, `ADMIN_EMAILS` was configured and injected into the ECS historical Compose backend, then the backend was recreated and reported healthy. The configured administrator login returned `is_admin=true`; `/admin/stats` and `/admin/feedback` returned 200; `/admin` and `/admin/feedback` returned 200; unauthenticated admin API requests returned 401; a temporary ordinary test account returned 403 for both admin APIs.
- Compose compatibility warning: ECS `/opt/paperforge/docker-compose.prod.yml` is a historical runtime file with direct image references and bind mounts. Do not replace it with the repository named-volume Compose without a separately reviewed data migration plan.

1. On the production host, check out the intended release runbook and create a protected environment file from `.env.production.example` outside Git.
2. Verify the immutable backend/frontend image references, release tag, public API URL, CORS origin, and persistent Docker volumes. Build `NEXT_PUBLIC_API_BASE_URL` into the frontend image before publishing it; Next.js public variables are compiled into the image and cannot be changed by the production Compose runtime.
3. Run `scripts/backup_postgres.ps1` (or the equivalent host command), verify the backup exists and is non-empty, then record the current `alembic current` revision.
4. Pull immutable images: `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml pull`.
5. Run the forward migration using the backend image: `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml run --rm backend alembic upgrade head`. Verify `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml run --rm backend alembic current` is `0012_day17_token_version`. Do not run production downgrade automatically.
6. Start services with `docker compose --env-file /secure/paperforge.env -f docker-compose.prod.yml up -d`; verify PostgreSQL, backend health, frontend route, authentication, active workspace task views, SSE, and artifact download.
7. Monitor logs for migration errors, repeated 500s, auth failures, and secret exposure.

Application rollback means restarting the previously recorded immutable backend/frontend images with the existing volumes. Database restore is separate, high risk, and only follows a verified backup plus an operator-reviewed restoration plan. A forward migration may not be compatible with a prior application image; do not treat database downgrade as routine rollback.

The public edge must supply TLS, a public frontend domain, a backend API route, forwarded headers (`Host`, `X-Forwarded-For`, `X-Forwarded-Proto`), adequate upload/download limits, and SSE-compatible buffering/timeouts. A reproducible Nginx example is provided at `deploy/nginx/paperforge.conf`; review hostnames and certificate paths before use. Route browser API, SSE, and artifact-download traffic to the backend without response buffering; retain streaming connections long enough for task events. The repository does not prescribe Kubernetes, HA, or autoscaling.

The canonical repository environment contract is intentionally split: PostgreSQL credentials (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`) construct the backend `DATABASE_URL` inside Compose; `JWT_SECRET_KEY`, `APP_ENV=production`, `AUTH_REQUIRED=true`, `CORS_ORIGINS`, and optional `DEEPSEEK_*` configure the backend. `PAPERFORGE_RELEASE_VERSION` must match the backend/frontend image tag and is applied as a label to all three services; `PAPERFORGE_*_IMAGE` must be immutable image references. `NEXT_PUBLIC_API_BASE_URL` is a frontend **build-time** contract, and `CORS_ORIGINS` is the matching runtime browser-origin allowlist. The repository Compose uses named volumes for local filesystem storage; the current ECS legacy Compose uses the bind mounts listed in the snapshot above and must not be changed without a data migration plan.

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
