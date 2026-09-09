# PaperForge Release Review Checklist

Use this checklist before creating a release, publishing a showcase update, or changing public repository presentation. Check only items supported by the release evidence; do not convert planned work into completed claims.

## Technical

- [ ] Required backend tests passed for the release candidate.
- [ ] Frontend production build passed for the release candidate.
- [ ] API contracts remain stable, or documented compatibility notes are included.
- [ ] Local mode still returns `ai_score = null` and `ai_used = false`.
- [ ] AI failure fallback preserves the main document-processing path.
- [ ] Dependencies and lockfiles are unchanged, or changes are explicitly reviewed.
- [ ] No unreviewed runtime artifacts, credentials, or generated outputs are included in the release diff.

## Documentation

- [ ] README includes project identity, verified workflow, demo entry, technical focus, quick start, and boundaries.
- [ ] Architecture overview and detailed architecture accurately reflect public behavior.
- [ ] Limitations and non-goals remain explicit and current.
- [ ] Demo, release notes, and repository metadata use consistent terminology.
- [ ] Repeated-content functionality is described only as **重复风险检测** or **相似度预检**.
- [ ] Historical documents remain preserved and are not presented as current product specifications.

## Demo

- [ ] Referenced screenshots are real, available in the repository, and accurately captioned.
- [ ] Demo inputs and outputs are constructed, de-identified, or otherwise authorized for publication.
- [ ] The demo flow covers upload, processing, Trace, verification, preview, and download.
- [ ] Scores and sample outcomes are labeled as run-specific evidence, not universal guarantees.
- [ ] Unsupported or high-risk outcomes are presented as Human Review, not as successful automation.

## Interview

- [ ] The project story explains why this is not a black-box GPT wrapper.
- [ ] The explanation covers the Verified Agent Loop, deterministic execution, optional LLM fallback, Human-in-the-loop, and Evidence / Trace.
- [ ] A concise architecture walkthrough is prepared.
- [ ] A 30-second demo path and a longer implementation discussion path are available.
- [ ] Limitations can be explained clearly without overclaiming.

## Current V2 evidence

The documented V2 acceptance baseline reports 26 core capability checks passed, end-to-end scenarios A–F passed, real DOCX regression 10/10 PASS with 0 warnings and 0 blocking failures, and a passing frontend production build. Confirm the evidence remains applicable before reusing it for a new release or public claim.
