# PaperForge repository-driven development

PaperForge uses **Repository-Driven Development**. Chat conversation is temporary
working context; the repository is the durable memory and handoff contract for all
agents, including Codex, Claude Code, Cursor, and other tools.

## Source of Truth

| Fact | Source of Truth |
| --- | --- |
| System implementation | Source code and tests |
| Current project state | `PROJECT_STATUS.md` |
| Next work and remaining items | `TODO.md` |
| Production deployment facts | `docs/PRODUCTION_DEPLOYMENT.md` |
| Project history | Git history and release tags |
| Temporary reasoning/context | Chat conversation only |

When chat content conflicts with the repository or a running environment, verify
the real code and runtime first, then update the repository documents.

## Agent start sequence

Before a substantial task, read in order:

1. `AI_CONTEXT.md`
2. `PROJECT_STATUS.md`
3. `TODO.md`
4. `docs/PRODUCTION_DEPLOYMENT.md` for deployment or production work
5. Recent `git log`, current `HEAD`, and worktree status
6. The design, security, and release documents directly related to the task

Summarize the project identity, current stage, P0 work, known bugs, and applicable
development rules before editing.

## Agent finish sequence

Before commit or push:

- Update `PROJECT_STATUS.md` when the real project state changes.
- Update `TODO.md` when work items or priorities change.
- Update `docs/PRODUCTION_DEPLOYMENT.md` when production or deployment facts change.
- Update `AI_CONTEXT.md` and relevant governance/design documents when architecture
  or long-term rules change.
- Run the applicable regression checks and record PASS/FAIL honestly.

Do not leave code, deployment, and repository status documents describing different
stages of the project.

## Secrets

Repository documents may name a secret, describe its purpose, and state whether it
is required. They must never contain a secret value, access key, password, token,
private key, or other production credential.

## Retired ACR workflow

The historical `ops/acr-build-v3.6` branch and `acr-build-v3.6.yml` workflow are
retired. They target an old commit/IP and do not provide the complete production
frontend build arguments. They must not be used for a current release. The current
canonical build entry is `.github/workflows/acr-build-paperforge.yml`, with
`scripts/build_and_push_acr.ps1` as the equivalent operator-runner.

## Handoff test

A new agent with no chat history should be able to answer from the files above:

- what PaperForge is and what it can safely do;
- the current stage, production URL/API, version, release commit, and image facts;
- completed work and remaining P0/P1/P2 items;
- the next safe action and operations that are forbidden;
- how to run tests and how to deploy without exposing secrets or deleting data.
