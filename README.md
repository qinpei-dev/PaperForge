# PaperForge — Verified Academic Document Agent

PaperForge is a DOCX-focused academic document agent that turns document cleanup into a verifiable workflow: **Plan → Execute → Verify → Human Review → Evidence**. It detects document structure, plans safe changes, applies low-risk formatting and content actions, re-reads the output DOCX, and explains what was changed, verified, deferred, or left for human review.

It is built for academic document formatting and review—not automatic paper writing, deep rewriting, formal plagiarism checking, or arbitrary Word automation.

## Why PaperForge is more than a formatter or API wrapper

The system does not treat an LLM response as proof that a document was changed correctly. A DOCX Document Model feeds a Rule Engine and Planner; the Executor applies target-aware changes; the Verifier reads the generated DOCX again and compares expected versus actual results. Provenance, risk policy, stale-conflict protection, fallback behavior, and Human-in-the-Loop decisions are kept in the result so users can see the basis for each outcome.

```text
DOCX input
  → Document Model
  → Rule Engine + Planner
  → Conflict Check
  → Executor
  → Re-read output DOCX
  → Target-level Verification
  → Decision / Human Review
  → Provenance + Evidence
  → Confirmed DOCX / Preview / Download
```

## What it can do today

- Classify DOCX documents and request confirmation for non-standard inputs.
- Use an optional DOCX template as a formatting reference, with safe fallback behavior.
- Repair common title, body, font, spacing, indentation, margin, and basic caption formatting.
- Check references, citations, figure/table numbering, and **重复风险检测 / 相似度预检**.
- Separate safe automatic fixes, suggestions, and high-risk actions requiring human review.
- Verify changes at target level where a reliable paragraph or section locator exists.
- Preserve before / expected / after evidence, provenance, change summaries, and pending actions.
- Provide local deterministic processing, AI-assisted review, AI failure fallback, online preview, and confirmed DOCX download.

## Verified execution and safety boundaries

PaperForge treats a suggestion as a suggestion until it is explicitly accepted and written to a new confirmed DOCX. A failed or unsupported verification does not become a successful score. High-risk facts, numbers, experimental results, conclusions, citations, methods, definitions, formulas, and ambiguous targets are not silently rewritten; they remain visible as Human Review items.

The current product does not promise:

- fully automatic paper writing or deep academic rewriting;
- reliable automation for every complex Word feature, including complex tables, fields, footnotes, formulas, cross-references, or table-of-contents internals;
- formal plagiarism-checking services such as CNKI, 维普, or 万方;
- autonomous multi-tenant SaaS, asynchronous recovery, checkpoint/resume, or a general-purpose agent platform.

## Architecture

The public architecture is intentionally small and inspectable:

- `paper-ai/backend/main.py` — FastAPI upload, classify, run, preview, and download endpoints.
- `paper-ai/backend/services/document_model.py` — normalized DOCX document representation.
- `paper-ai/backend/services/rule_engine.py` — rules, evidence, risk, and supported actions.
- `paper-ai/backend/services/planner.py` — deterministic execution plan and conflict normalization.
- `paper-ai/backend/services/executor_adapter.py` — safe target-aware execution and provenance records.
- `paper-ai/backend/services/verifier.py` — output DOCX re-read and target-level verification.
- `paper-ai/backend/services/governance.py` — COMPLETE / REPLAN / HUMAN_REVIEW / FAIL decisions.
- `paper-ai/frontend/app/page.tsx` — upload, workflow, verification, evidence, review, preview, and download experience.

See [the architecture reference](docs/ARCHITECTURE.md) and [the documentation index](docs/README.md).

## Evidence from real execution

The current V2 acceptance baseline records:

- 26 core capability checks passed;
- end-to-end scenarios A–F passed;
- Safety Audit, Provenance / Verification, Score Credibility, AI failure fallback, and legacy compatibility passed;
- real DOCX regression: **10/10 PASS, 0 warnings, 0 blocking failures**;
- frontend production build passed.

These are repository test and acceptance results, not a claim that every DOCX will receive the same outcome. The application still recommends human review before submission.

## Technology

FastAPI · Python · `python-docx` · Next.js · React · TypeScript · Docker Compose

## Quick start

### Local development

Backend:

```powershell
cd paper-ai/backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend, in a second terminal:

```powershell
cd paper-ai/frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3000`. The backend health endpoint is `http://127.0.0.1:8000/health`.

### Docker Compose

```powershell
Copy-Item paper-ai/backend/.env.example paper-ai/backend/.env
docker compose up --build
```

Set `NEXT_PUBLIC_API_BASE_URL` for a non-local backend and configure `CORS_ORIGINS` on the backend when the frontend is hosted elsewhere. See [Docker deployment](docs/DOCKER_DEPLOYMENT.md).

## Verification commands

```powershell
cd paper-ai/backend
python -m compileall -q main.py services
python test_p2_content_review_closure.py
python test_p2_closure.py
python test_score_consistency.py
python test_smoke_agent_flow.py

cd ../frontend
npm run build
```

The full DOCX regression entry point is `paper-ai/backend/run_real_doc_regression.py`; it uses the repository's test assets and writes results under the ignored regression output directory.

## Repository map

```text
paper-ai/backend/     FastAPI app, document model, rules, runtime, tests
paper-ai/frontend/    Next.js user interface
demo_inputs/          Small de-identified demo DOCX inputs
demo_outputs/         Reviewed demo outputs and evidence samples
docs/                 Public docs, architecture, deployment, and archived history
qa/                   Additional quality checks and acceptance material
```

## Release status

The current public release is **PaperForge V2**, tagged `v2.0-paperforge`. The repository is in Release Freeze: future work should be limited to documentation, deployment stability, controlled user feedback, and blocking regression fixes.

## License

MIT License
