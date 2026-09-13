# PaperForge public evidence

This file controls public claims about PaperForge. It contains product and engineering evidence only; personal background, marketing operations, account activity, and private working notes do not belong here.

Last verified: 2026-09-12.

## E001 · Production status

- **Verified fact:** PaperForge v3.7.5 is deployed at [aetherislab.xyz](https://aetherislab.xyz) and is **READY FOR CONTROLLED PUBLIC BETA**.
- **Evidence:** `PROJECT_STATUS.md` and `docs/PRODUCTION_DEPLOYMENT.md`.
- **Public wording:** “PaperForge is deployed and operating in controlled public beta.”
- **Do not claim:** general availability, user-count, revenue, or high-availability guarantees.

## E002 · Verified document-processing workflow

- **Verified fact:** PaperForge classifies DOCX documents, plans supported low-risk changes, applies deterministic formatting rules, re-reads the result, and exposes traceable evidence for review.
- **Evidence:** source code, architecture documents, backend tests, and the production smoke record.
- **Public wording:** “AI-assisted analysis is constrained by deterministic execution, verification, and human-review boundaries.”

## E003 · Current security and SaaS boundaries

- **Verified fact:** The current product includes JWT authentication with session revocation, tenant isolation, RBAC, tenant-scoped templates, durable tasks, SSE replay, quotas, admin controls, and authenticated feedback.
- **Evidence:** `PROJECT_STATUS.md`, migrations, backend tests, and the production runbook.
- **Do not claim:** WAF coverage, multi-region availability, distributed workers, SSO/SCIM, or billing.

## E004 · AI and scoring boundaries

- **Verified fact:** Local mode is deterministic and returns `ai_score = null` and `ai_used = false`. AI mode falls back to local rules when an LLM is unavailable.
- **Do not claim:** deep academic rewriting, formal plagiarism checking, or that a score increase proves equivalent content improvement.

## E005 · Testing evidence

- **Verified fact:** On 2026-09-12, backend `pytest -q` recorded 107 passed and the frontend production build passed. Production smoke covered authenticated task creation, SSE, preview, download, feedback, and admin authorization.
- **Do not claim:** that all UI interaction is covered by automated browser tests; the repository does not contain a Playwright or Cypress suite.

## E006 · Sample and archive boundaries

- **Verified fact:** Demo DOCX assets are constructed and de-identified. Historical screenshots and release material are archived and must not be presented as the current SaaS UI.
- **Evidence:** `docs/archive/` and repository asset records.
