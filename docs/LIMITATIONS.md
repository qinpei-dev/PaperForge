# PaperForge Limitations

PaperForge is designed to make supported DOCX processing more reliable and traceable. It does not claim that every Word feature, academic requirement, or review scenario can be safely automated.

## DOCX and OpenXML scope

PaperForge relies on `python-docx` for supported document operations. Its coverage is intentionally limited for complex OpenXML structures, including:

- complex tables, nested layouts, and advanced formatting inheritance;
- fields, automatic tables of contents, cross-references, and some numbering behavior;
- footnotes, endnotes, formulas, tracked changes, comments, and some headers or footers;
- complex images, shapes, charts, captions, and embedded Office objects.

When a reliable locator or supported operation is unavailable, the system should preserve the limitation through unsupported evidence or Human Review instead of silently claiming success.

## Review and verification scope

- Verification is strongest for supported target-level changes with reliable paragraph or section locators.
- An output DOCX re-read is evidence of supported checks, not a guarantee of perfect visual fidelity in every Word renderer.
- Templates can provide formatting references, but complex templates may be partially interpreted or produce warnings.
- Content review is constrained and risk-gated; it is not a promise of deep academic editing or improved scholarly argumentation.

## AI and scoring scope

- Local mode is deterministic and does not use an AI score.
- AI mode can use an LLM for analysis and review candidates, with local fallback if it is unavailable.
- AI-assisted suggestions are not proof of correctness and do not bypass policy, execution, or verification.
- Scores and sample improvements are diagnostic signals for the processed document; they are not publication-readiness guarantees.

## Product non-goals

PaperForge is not:

- a paper-generation, ghostwriting, or researcher-replacement tool;
- a formal plagiarism-checking service; repeated-content functionality is described only as **重复风险检测** or **相似度预检**;
- a substitute for institutional formatting rules, advisor review, editorial review, or academic-integrity processes;
- a general-purpose Word automation platform or a complete asynchronous multi-user SaaS system.

## Recommended use

Use PaperForge to inspect and improve supported document formatting, review traceable output, and identify items needing attention. Review the final DOCX in the target Word environment before submission, especially when it includes advanced formatting, citations, formulas, tables, or institution-specific templates.
