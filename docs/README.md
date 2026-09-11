# PaperForge documentation

PaperForge is currently in **P0 release remediation and production validation**. The public product name is **PaperForge — Verified Academic Document Agent**. Older names and version numbers are retained only where they are necessary to preserve historical development records; see `PROJECT_STATUS.md` and the production runbook for current facts.

## Start here

- [Architecture overview](ARCHITECTURE_OVERVIEW.md) — GitHub-friendly system view of the verified Agent loop and module boundaries.
- [Project architecture](ARCHITECTURE.md) — detailed FastAPI, DOCX model, planning, execution, verification, governance, and UI boundaries.
- [Demo guide](DEMO_GUIDE.md) — a 30-second, reproducible walkthrough using the included real-run assets and demo files.
- [Limitations](LIMITATIONS.md) — supported boundaries, non-goals, and review expectations.
- [GitHub presentation guide](GITHUB_PRESENTATION.md) — repository metadata, pinned-repository, and interview-entry recommendations.
- [Release review checklist](RELEASE_REVIEW_CHECKLIST.md) — pre-release technical, documentation, demo, and interview checks.
- [Repository governance](REPOSITORY_GOVERNANCE.md) — source-of-truth, agent handoff, secret, and release workflow rules.
- [Risk level system](RISK_LEVEL_SYSTEM.md) — how low-risk, warning, and human-review work is handled.
- [Agent Trace](AGENT_TRACE.md) — the explainability fields exposed by the runtime.
- [Docker deployment](DOCKER_DEPLOYMENT.md) — local container startup and environment configuration.
- [V2 release notes](PAPERFORGE_V2_RELEASE_NOTES.md) — current release scope, evidence, and boundaries.

## New Visitor Guide

For a first visit, use this reading order:

1. [README.md](../README.md) — product scope, engineering value, demo entry, and quick start.
2. [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) — verified Agent loop and system boundaries.
3. [DEMO_GUIDE.md](DEMO_GUIDE.md) — 30-second workflow with included demo files and real-run screenshots.
4. [RISK_LEVEL_SYSTEM.md](RISK_LEVEL_SYSTEM.md) — automatic actions versus warning and human-review policy.
5. [INTERVIEW_DEMO_PACKAGE.md](INTERVIEW_DEMO_PACKAGE.md) — interview narrative, longer demo script, and likely questions.
6. [LIMITATIONS.md](LIMITATIONS.md) — explicit constraints and non-goals.

## Reference material

- [Deployment plan](DEPLOYMENT_PLAN.md) — implementation and deployment notes.

## Historical material

`docs/archive/` contains beta preparation, interview Q&A, and earlier release records. Those files describe their original stage and should not be read as the current product specification.

The screenshots under `docs/assets/` are presentation evidence. They are not a substitute for running the current application or the current regression suite.
