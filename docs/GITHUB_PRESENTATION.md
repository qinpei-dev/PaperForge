# GitHub Repository Presentation Guide

This guide recommends how to present PaperForge on its GitHub repository page. It is advisory only: it does not modify repository settings, topics, social preview, or pinned repositories.

## Repository Description 推荐

Use a concise, engineering-focused description:

> Verified AI agent for traceable academic DOCX processing — plan, execute, verify, and review with evidence.

The description emphasizes verification and traceability without implying paper generation, formal plagiarism checking, or autonomous research.

## Topics 推荐

Suggested GitHub topics:

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

Use only topics that remain accurate for the public repository. Avoid topics such as `paper-generator`, `autonomous-research`, `plagiarism-checker`, or a specific LLM provider unless the published project scope changes.

## Pin Repository 推荐内容

When PaperForge is pinned on a profile, use the repository description above and make the first three visible ideas consistent:

1. **Verified execution:** a DOCX change is planned, executed, re-read, and verified rather than trusted as model output.
2. **Controlled AI:** LLM assistance is optional, with deterministic local processing and fallback behavior.
3. **Inspectable results:** Agent Trace, provenance, evidence, and Human Review preserve the basis for each outcome.

Use the existing real application overview as the README social evidence. Do not use generated mockups or imply that the screenshot represents every document.

## 面试展示入口推荐

Recommended interview path:

1. Start at the [README](../README.md) and introduce the verified Agent loop.
2. Open [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) to explain the separation of AI, deterministic execution, verification, and governance.
3. Use [DEMO_GUIDE.md](DEMO_GUIDE.md) with the included DOCX inputs and real-run screenshots.
4. Open [INTERVIEW_DEMO_PACKAGE.md](INTERVIEW_DEMO_PACKAGE.md) for deeper implementation discussion.
5. End with [LIMITATIONS.md](LIMITATIONS.md) to demonstrate scope discipline and reliability boundaries.

Suggested one-sentence introduction:

> PaperForge is a verified document-processing Agent: AI assists analysis, deterministic rules perform supported changes, and the output is re-read with traceable evidence and human-review gates.

## README 浏览路径

The README is intended to support this first-visit path:

```text
Identity and engineering focus
    ↓
Real application screenshot
    ↓
Problem and verified approach
    ↓
Capabilities, fallback, HITL, and observability
    ↓
Architecture and demo
    ↓
Verification evidence, limitations, and quick start
```

Before publishing a release, use [RELEASE_REVIEW_CHECKLIST.md](RELEASE_REVIEW_CHECKLIST.md) to verify that repository metadata, documentation, and demo claims remain aligned.
