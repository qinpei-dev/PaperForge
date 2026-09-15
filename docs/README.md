# PaperForge documentation

PaperForge v3.7.5 is **READY FOR CONTROLLED PUBLIC BETA**. This page is the public documentation entrypoint; current release and production facts are maintained in `PROJECT_STATUS.md` and the production runbook.

## Product

- [Project README](../README.md) — product scope, workflow, local setup, and current boundaries.
- [Public evidence](knowledge/CONTENT_EVIDENCE.md) — evidence-backed public claims and non-claims.

## Live Product

PaperForge is deployed and running in production at [aetherislab.xyz](https://aetherislab.xyz). The sanitized production landing capture is included in the project README. No local or Preview image is labeled as production evidence. See [Production Screenshot Audit](PRODUCTION_SCREENSHOT_AUDIT.md).

## Product Workflow

The production New Task capture is retained at [`assets/screenshots/production/production_04_new_task.jpeg`](assets/screenshots/production/production_04_new_task.jpeg) for review, but its login-state redaction affects layout and it is not used as a primary README image. The supplemental UI gallery is in [`assets/screenshots/current/`](assets/screenshots/current/). These assets were captured from the current `main` local runtime with a synthetic preview workspace and test DOCX. They are sanitized workflow material, not production evidence or benchmark evidence.

- [Landing](assets/screenshots/current/01_landing.png)
- [Login](assets/screenshots/current/02_login.png)
- [Dashboard](assets/screenshots/current/03_dashboard.png)
- [New Task with test files](assets/screenshots/current/04_new_task_selected.png)
- [Task Detail](assets/screenshots/current/05_task_detail.png)
- [Agent Trace](assets/screenshots/current/06_trace.png)

The current gallery intentionally excludes the legacy `docs/archive/screenshots/` set and the local Preview rendering capture with character-encoding corruption. No screenshot values should be read as product accuracy or success-rate claims.

## Architecture

- [Architecture overview](ARCHITECTURE_OVERVIEW.md) — the verified Agent loop and component boundaries.
- [Detailed architecture](ARCHITECTURE.md) — API, task, document, execution, verification, and governance layers.
- [Agent Trace](AGENT_TRACE.md) — traceability fields exposed by the runtime.

## Operations

- [Production deployment runbook](PRODUCTION_DEPLOYMENT.md) — authoritative release and deployment facts.
- [Docker deployment](DOCKER_DEPLOYMENT.md) — local container startup and configuration.
- [Backup and restore](BACKUP_RESTORE.md) — backup and recovery boundaries.
- [Release review checklist](RELEASE_REVIEW_CHECKLIST.md) — current-release review checks.

## Security

- [Repository governance](REPOSITORY_GOVERNANCE.md) — source-of-truth, secret, and release workflow rules.
- [Risk level system](RISK_LEVEL_SYSTEM.md) — supported automatic actions and human-review boundaries.
- [Public project facts](knowledge/PROJECT_FACTS.md) — concise current capability and limitation reference.

## Testing and limitations

- [Limitations](LIMITATIONS.md) — supported scope, non-goals, and review expectations.
- [Test corpus notes](../paper-ai/backend/test_documents/README.md) — test-data boundaries and provenance.

## Archive

[Historical archive](archive/README.md) contains prior showcase, release, deployment, screenshot, and engineering-audit material. Archived files preserve their original conclusions but are not current product specifications or current UI evidence.
