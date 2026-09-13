# GitHub repository presentation guide

PaperForge v3.7.5 is **READY FOR CONTROLLED PUBLIC BETA**. Public repository presentation must describe the current verified SaaS product, not early showcase UI or historical release baselines.

## Repository description

> Verified academic DOCX processing with deterministic execution, evidence, and human review.

This wording communicates the product boundary without implying paper generation, formal plagiarism checking, or autonomous research.

## Suggested topics

```text
ai-agent
document-ai
docx
fastapi
nextjs
python-docx
verification
human-in-the-loop
observability
provenance
academic-tools
```

Use only topics that remain accurate. Avoid `paper-generator`, `autonomous-research`, `plagiarism-checker`, or an LLM-provider topic unless the published scope changes.

## Recommended first-visit path

1. Start at the [README](../README.md) for product scope, current status, and local setup.
2. Read [Architecture Overview](ARCHITECTURE_OVERVIEW.md) for the verified Agent loop.
3. Read [Production deployment](PRODUCTION_DEPLOYMENT.md) for current release facts and operational boundaries.
4. Read [Limitations](LIMITATIONS.md) to understand supported scope and non-goals.

Use current, authorized SaaS screenshots only after they have been reviewed for privacy and release accuracy. Do not use the archived v0.9.x screenshots as current UI evidence.

## Before publishing

- Confirm release wording against `PROJECT_STATUS.md` and `docs/PRODUCTION_DEPLOYMENT.md`.
- Confirm no personal information, production IPs, task identifiers, credentials, or local paths are present in images or prose.
- Use [RELEASE_REVIEW_CHECKLIST.md](RELEASE_REVIEW_CHECKLIST.md) before public release or showcase updates.
