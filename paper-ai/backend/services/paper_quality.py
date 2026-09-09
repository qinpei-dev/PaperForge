from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class QualityReport:
    overall_score: int
    dimensions: dict[str, dict[str, Any]]
    improvements: list[dict[str, Any]]
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DIMENSIONS = ("format", "structure", "reference", "visual")


def analyze_paper_quality(
    document_analysis: dict[str, Any] | None,
    reasoning_results: list[dict[str, Any]] | None,
    verification_results: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a deterministic quality report from existing pipeline evidence."""
    analysis = document_analysis or {}
    reasoning = [item for item in (reasoning_results or []) if isinstance(item, dict)]
    verification = verification_results or {}
    dimensions = {
        "format": _format_dimension(reasoning, verification),
        "structure": _structure_dimension(analysis),
        "reference": _reference_dimension(analysis, reasoning),
        "visual": _visual_dimension(analysis, reasoning, verification),
    }
    improvements = _improvements(dimensions, reasoning, verification)
    scores = [int(item["score"]) for item in dimensions.values()]
    confidence = _confidence(analysis, reasoning, verification)
    return QualityReport(round(sum(scores) / len(scores)), dimensions, improvements, confidence).to_dict()


def _format_dimension(reasoning: list[dict[str, Any]], verification: dict[str, Any]) -> dict[str, Any]:
    summary = verification.get("verification_summary") or {}
    total = int(summary.get("total", 0) or 0)
    verified = int(summary.get("verified", 0) or 0)
    failed = int(summary.get("failed", 0) or 0)
    issues = [item for item in reasoning if (item.get("context") or {}).get("issue_type") in {"heading_mismatch", "paragraph_format_mismatch"}]
    if total:
        score = round(max(0, min(100, verified / total * 100)))
        evidence = {"source": "verification_results.verification_summary", "total": total, "verified": verified, "failed": failed}
    else:
        score = max(0, 100 - 15 * len(issues))
        evidence = {"source": "reasoning_results", "issue_ids": [item.get("issue_id") for item in issues], "verification_summary": "not_available"}
    return {"score": score, "evidence": evidence, "status": "pass" if score >= 90 else "needs_improvement"}


def _structure_dimension(analysis: dict[str, Any]) -> dict[str, Any]:
    sections = analysis.get("sections") or []
    elements = analysis.get("elements") or []
    confidence = float(analysis.get("confidence") or 0.0)
    unknown_sections = sum(1 for item in sections if isinstance(item, dict) and item.get("type") == "unknown")
    unknown_elements = sum(1 for item in elements if isinstance(item, dict) and item.get("semantic_type") == "unknown")
    score = round(max(0, min(100, confidence * 100 - unknown_sections * 5 - unknown_elements * 2)))
    return {"score": score, "evidence": {"source": "document_analysis", "analysis_confidence": confidence, "section_count": len(sections), "element_count": len(elements), "unknown_sections": unknown_sections, "unknown_elements": unknown_elements}, "status": "pass" if score >= 90 else "needs_improvement"}


def _reference_dimension(analysis: dict[str, Any], reasoning: list[dict[str, Any]]) -> dict[str, Any]:
    metadata = analysis.get("metadata") or {}
    issues = [item for item in reasoning if (item.get("context") or {}).get("issue_type") == "reference_format_issue"]
    reference_count = int(metadata.get("reference_count", 0) or 0)
    score = 100 if reference_count and not issues else (65 if issues else 80 if reference_count == 0 else 90)
    return {"score": score, "evidence": {"source": "document_analysis + reasoning_results", "reference_count": reference_count, "issue_ids": [item.get("issue_id") for item in issues]}, "status": "pass" if score >= 90 else "needs_improvement"}


def _visual_dimension(analysis: dict[str, Any], reasoning: list[dict[str, Any]], verification: dict[str, Any]) -> dict[str, Any]:
    integrity = (verification.get("structural_integrity") or {}).get("status")
    issues = [item for item in reasoning if (item.get("context") or {}).get("issue_type") == "figure_table_issue"]
    figure_count = int((analysis.get("metadata") or {}).get("figure_count", 0) or 0)
    table_count = int((analysis.get("metadata") or {}).get("table_count", 0) or 0)
    if integrity == "UNSAFE":
        score = 40
    elif issues:
        score = 70
    elif integrity in {"SAFE", "PASS", "UNCHANGED"}:
        score = 100
    else:
        score = 80 if figure_count or table_count else 75
    return {"score": score, "evidence": {"source": "document_analysis + verification_results + reasoning_results", "structural_integrity": integrity or "not_available", "figure_count": figure_count, "table_count": table_count, "issue_ids": [item.get("issue_id") for item in issues]}, "status": "pass" if score >= 90 else "needs_improvement"}


def _improvements(dimensions: dict[str, dict[str, Any]], reasoning: list[dict[str, Any]], verification: dict[str, Any]) -> list[dict[str, Any]]:
    improvements: list[dict[str, Any]] = []
    for name, dimension in dimensions.items():
        if dimension["score"] < 90:
            improvements.append({"dimension": name, "score": dimension["score"], "evidence": dimension["evidence"], "recommendation": _recommendation(name, reasoning, verification)})
    return improvements


def _recommendation(name: str, reasoning: list[dict[str, Any]], verification: dict[str, Any]) -> str:
    if name == "format":
        return "根据验证失败项复核标题、正文段落格式及未通过的格式规则。"
    if name == "structure":
        return "补充或人工确认未可靠识别的章节和段落语义。"
    if name == "reference":
        return "人工检查参考文献编号连续性、条目格式和正文引用对应关系。"
    if (verification.get("structural_integrity") or {}).get("status") == "UNSAFE":
        return "优先复核输出文档的结构完整性，确认图表和文档结构未发生不安全变化。"
    return "检查图表题注、编号和布局，并对高风险图表问题进行人工确认。"


def _confidence(analysis: dict[str, Any], reasoning: list[dict[str, Any]], verification: dict[str, Any]) -> float:
    signals = []
    if analysis.get("confidence") is not None:
        signals.append(float(analysis.get("confidence") or 0.0))
    if reasoning:
        signals.append(sum(float(item.get("confidence") or 0.0) for item in reasoning) / len(reasoning))
    if verification:
        signals.append(1.0 if verification.get("passed") is not None else 0.5)
    return round(max(0.0, min(1.0, sum(signals) / len(signals))) if signals else 0.0, 4)
