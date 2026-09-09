from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ReasoningResult:
    issue_id: str
    context: dict[str, Any]
    reason: str
    recommendation: str
    risk_level: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ISSUE_ALIASES = {
    "heading": "heading_mismatch",
    "heading_format": "heading_mismatch",
    "heading_mismatch": "heading_mismatch",
    "body_font": "paragraph_format_mismatch",
    "spacing_indent": "paragraph_format_mismatch",
    "paragraph": "paragraph_format_mismatch",
    "paragraph_format": "paragraph_format_mismatch",
    "paragraph_format_mismatch": "paragraph_format_mismatch",
    "reference": "reference_format_issue",
    "references": "reference_format_issue",
    "reference_format": "reference_format_issue",
    "reference_format_issue": "reference_format_issue",
    "figure": "figure_table_issue",
    "table": "figure_table_issue",
    "figures_tables": "figure_table_issue",
    "figure_table": "figure_table_issue",
    "figure_table_issue": "figure_table_issue",
}


def generate_reasoning(
    document_analysis: dict[str, Any] | None,
    detected_issues: Iterable[dict[str, Any]] | None,
    template_rules: Iterable[dict[str, Any]] | None,
    template_analysis: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Explain detected format issues without changing the document.

    This layer is deliberately local and deterministic.  It consumes the
    existing analysis/rule artifacts so an unavailable LLM cannot interrupt
    planning or execution.
    """
    analysis = document_analysis or {}
    rules = list(template_rules or [])
    template = template_analysis or {}
    effective_rules = template.get("effective_rules") if isinstance(template.get("effective_rules"), dict) else {}
    results: list[dict[str, Any]] = []
    for index, raw_issue in enumerate(detected_issues or []):
        if not isinstance(raw_issue, dict):
            continue
        kind = _canonical_issue(raw_issue)
        if kind is None:
            continue
        issue_id = str(raw_issue.get("issue_id") or f"{kind}-{index + 1}")
        score = _score(raw_issue)
        rule_matches = _matching_rules(kind, raw_issue, rules, effective_rules, float(template.get("confidence") or 0.0))
        confidence = _confidence(analysis, raw_issue, rule_matches, template)
        context = {
            "issue_type": kind,
            "score": score,
            "evidence": raw_issue.get("evidence") or raw_issue.get("message") or raw_issue.get("issues") or [],
            "rule_ids": [str(rule.get("id")) for rule in rule_matches if rule.get("id")],
            "template_sections": [item.get("type") for item in template.get("sections", []) if isinstance(item, dict)],
            "protected_region_types": [item.get("type") for item in template.get("protected_regions", []) if isinstance(item, dict)],
            "effective_rule_scope": rule_matches[0].get("target") if rule_matches and rule_matches[0].get("id", "").startswith("effective-") else None,
            "effective_rule": rule_matches[0].get("value") if rule_matches and rule_matches[0].get("id", "").startswith("effective-") else None,
        }
        reason, recommendation, default_risk = _explain(kind, raw_issue, score, rule_matches)
        result = ReasoningResult(
            issue_id=issue_id,
            context=context,
            reason=reason,
            recommendation=recommendation,
            risk_level=str(raw_issue.get("risk_level") or default_risk),
            confidence=confidence,
        )
        results.append(result.to_dict())
    return results


def _canonical_issue(issue: dict[str, Any]) -> str | None:
    raw = issue.get("issue_type") or issue.get("type") or issue.get("key") or issue.get("target")
    if not raw:
        return None
    value = str(raw).lower().replace("-", "_")
    return ISSUE_ALIASES.get(value)


def _score(issue: dict[str, Any]) -> int | None:
    try:
        return int(issue["score"]) if issue.get("score") is not None else None
    except (TypeError, ValueError):
        return None


def _matching_rules(
    kind: str,
    issue: dict[str, Any],
    rules: list[dict[str, Any]],
    effective_rules: dict[str, Any] | None = None,
    template_confidence: float = 0.0,
) -> list[dict[str, Any]]:
    target = str(issue.get("target") or "")
    legacy = [
        rule for rule in rules
        if isinstance(rule, dict)
        and (str(rule.get("id")) == str(issue.get("rule_id")) or _rule_matches_kind(kind, str(rule.get("target") or target)))
    ]
    effective = _effective_rule_for_issue(kind, target, effective_rules or {}, template_confidence)
    return ([effective] if effective else []) + legacy


def _effective_rule_for_issue(kind: str, target: str, effective_rules: dict[str, Any], confidence: float) -> dict[str, Any] | None:
    if not effective_rules:
        return None
    requested = target.lower()
    keys = {str(key).lower(): str(key) for key in effective_rules}
    scope: str | None = keys.get(requested)
    if scope is None:
        if kind == "paragraph_format_mismatch":
            scope = keys.get("body")
        elif kind == "reference_format_issue":
            scope = keys.get("references")
        elif kind == "heading_mismatch":
            scope = next((original for normalized, original in keys.items() if normalized.startswith("heading:")), None)
    value = effective_rules.get(scope) if scope else None
    if not isinstance(value, dict):
        return None
    return {"id": f"effective-{scope}", "target": scope, "property": "effective", "value": value, "confidence": confidence, "source": "template_effective_rules"}


def _rule_matches_kind(kind: str, target: str) -> bool:
    target = target.lower()
    if kind == "heading_mismatch":
        return target.startswith("heading")
    if kind == "paragraph_format_mismatch":
        return target == "body"
    if kind == "reference_format_issue":
        return target == "references"
    return target in {"figures_tables", "caption:figure", "caption:table"}


def _confidence(analysis: dict[str, Any], issue: dict[str, Any], rules: list[dict[str, Any]], template: dict[str, Any] | None = None) -> float:
    values = [float(analysis.get("confidence") or 0.0)]
    if issue.get("confidence") is not None:
        values.append(float(issue["confidence"]))
    if rules:
        values.append(max(float(rule.get("confidence") or 0.0) for rule in rules))
    if template and template.get("confidence") is not None:
        values.append(float(template.get("confidence") or 0.0))
    return round(max(0.0, min(1.0, sum(values) / len(values))), 4)


def _explain(kind: str, issue: dict[str, Any], score: int | None, rules: list[dict[str, Any]]) -> tuple[str, str, str]:
    rule_text = f"模板规则 {', '.join(str(rule.get('id')) for rule in rules[:2])} 提供了对照基准。" if rules else "当前使用文档分析器识别出的格式证据作为对照。"
    if kind == "heading_mismatch":
        return (f"标题段落的实际样式或层级与预期规则不一致（当前评分 {score if score is not None else '未知'}）。{rule_text}", "检查标题级别、字体、字号、对齐和编号层级；仅对可靠定位的标题执行格式修复。", "warning")
    if kind == "paragraph_format_mismatch":
        return (f"正文段落的字体、字号、行距或缩进至少有一项偏离规则（当前评分 {score if score is not None else '未知'}）。{rule_text}", "统一可靠定位正文的字体、字号、行距和首行缩进，不改写正文语义。", "warning")
    if kind == "reference_format_issue":
        return (f"参考文献存在编号、连续性或引用关系风险（当前评分 {score if score is not None else '未知'}）。这些关系无法仅凭样式安全推断。", "保留为人工复核，检查编号连续性、正文引用与文献条目的对应关系。", "high_risk")
    return (f"图或表的编号、题注或关联结构存在风险（当前评分 {score if score is not None else '未知'}）。题注文本和编号关系需要谨慎保护。", "仅规范可可靠定位的题注样式；编号、题注内容和引用关系建议人工复核。", "high_risk")
