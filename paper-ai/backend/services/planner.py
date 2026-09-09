from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any

from .document_model import DocumentModel
from .rule_engine import Rule


@dataclass
class PlanStep:
    id: str
    action: str
    target: str
    rule_id: str
    evidence: str
    risk_level: str
    auto_fixable: bool
    dependencies: list[str]
    status: str
    reason: str
    related_rule_ids: list[str] = field(default_factory=list)
    target_locator: dict[str, Any] = field(default_factory=dict)
    original_step_id: str | None = None
    normalization_status: str = "canonical"
    conflict_reason: str | None = None
    expected: Any = None
    field: str | None = None
    reasoning: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionPlan:
    plan_id: str
    document_id: str
    steps: list[PlanStep]
    warnings: list[str]
    requires_human_review: bool
    conflict_summary: dict[str, Any] = field(default_factory=dict)
    execution_order: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {**asdict(self), "steps": [step.to_dict() for step in self.steps]}


def target_key(step: PlanStep) -> str:
    """Stable target identity for the locators currently emitted by Planner."""
    locator = step.target_locator or {}
    return f"{step.target}|{locator.get('kind')}|{locator.get('semantic_role')}|{locator.get('target_type')}|{locator.get('indices')}|{locator.get('role')}"


def normalize_execution_plan(plan: ExecutionPlan) -> tuple[ExecutionPlan, dict[str, Any]]:
    """Deduplicate and audit conflicts without hiding original provenance."""
    canonical: list[PlanStep] = []
    by_field: dict[tuple[str, str], PlanStep] = {}
    duplicates: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    for step in plan.steps:
        key = (target_key(step), _step_field(step))
        existing = by_field.get(key)
        if existing is None:
            normalized = PlanStep(**{**step.to_dict(), "original_step_id": step.original_step_id or step.id})
            by_field[key] = normalized
            canonical.append(normalized)
            continue
        if _same_expected(existing, step):
            duplicates.append({"duplicate_step_id": step.id, "canonical_step_id": existing.id, "target": target_key(step), "field": _step_field(step), "reason": "same target, field and expected value"})
            continue
        conflict = {"target": target_key(step), "field": _step_field(step), "step_ids": [existing.id, step.id], "candidate_values": [existing.expected, step.expected], "reason": "same target and field have different expected values"}
        conflicts.append(conflict)
        existing.normalization_status = "conflict"
        existing.conflict_reason = conflict["reason"]
        existing.auto_fixable = False
        existing.status = "conflict"
        canonical.append(PlanStep(**{**step.to_dict(), "original_step_id": step.original_step_id or step.id, "normalization_status": "conflict", "conflict_reason": conflict["reason"], "auto_fixable": False, "status": "conflict"}))
    ordered = sorted(enumerate(canonical), key=lambda pair: (_order_rank(pair[1]), pair[0]))
    steps = [step for _, step in ordered]
    execution_order = [step.id for step in steps]
    summary = {"total_steps": len(plan.steps), "canonical_steps": len(steps), "duplicates": len(duplicates), "conflicts": len(conflicts), "duplicate_items": duplicates, "conflict_items": conflicts}
    normalized = ExecutionPlan(plan.plan_id, plan.document_id, steps, plan.warnings, plan.requires_human_review or bool(conflicts), summary, execution_order)
    return normalized, summary


def _step_field(step: PlanStep) -> str:
    return step.field or (str(step.rule_id.rsplit("-", 1)[-1]) if step.rule_id else step.action)


def _same_expected(left: PlanStep, right: PlanStep) -> bool:
    return left.expected == right.expected and left.action == right.action


def _order_rank(step: PlanStep) -> int:
    if step.action == "apply_document_hygiene": return 0
    if step.target == "page": return 1
    if step.target == "body": return 2
    if step.target.startswith("heading:") or step.target in {"heading", "caption:figure", "caption:table"}: return 3
    if step.action == "human_review" or step.normalization_status == "conflict": return 4
    return 5


ANALYSIS_KEY_BY_TARGET = {
    "page": "page_margin",
    "body": "body_font",
    "references": "references",
}


def build_execution_plan(document: DocumentModel, rules: list[Rule], analysis: dict[str, Any], reasoning_results: list[dict[str, Any]] | None = None) -> ExecutionPlan:
    """Create a conservative plan from measured analysis, not a rule dump."""
    breakdown = {item.get("key"): item for item in ((analysis.get("report") or {}).get("breakdown") or [])}
    review_steps: list[PlanStep] = []
    steps: list[PlanStep] = []
    warnings = list(document.warnings)

    for rule in rules:
        if rule.target == "figures_tables":
            if has_figure_table_risk(analysis):
                review_steps.append(review_step(rule, "图表编号或题注存在高风险，当前阶段仅进入人工复核。"))
            continue
        if rule.target == "references":
            if has_reference_risk(analysis):
                review_steps.append(review_step(rule, "参考文献编号或引用关系异常，不能安全自动改写。"))
            continue
        if rule.target.startswith("heading:"):
            locators = reliable_heading_locator(document, rule.target)
            if locators:
                steps.append(local_format_step(len(steps), rule, "apply_heading_format", "heading", locators, "仅修改样式明确且置信度足够的标题段落。"))
            continue
        if rule.target.startswith("caption:"):
            kind = rule.target.split(":", 1)[1]
            locators = reliable_caption_locator(document, kind)
            if locators:
                steps.append(local_format_step(len(steps), rule, "apply_caption_format", rule.target, locators, "仅修改编号语法明确的图题/表题段落格式，不改写题注文本或编号。"))
            continue
        analysis_key = "heading_format" if rule.target.startswith("heading:") else ANALYSIS_KEY_BY_TARGET.get(rule.target)
        item = breakdown.get(analysis_key) if analysis_key else None
        if item is None:
            warnings.append(f"无法用现有 Analyzer 判断规则 {rule.id} 是否满足。")
            continue
        if int(item.get("score", 0)) >= 90:
            continue
    for rule in rules:
        if rule.target != "page" or not rule.auto_fixable:
            continue
        item = breakdown.get("page_margin")
        if item is None or int(item.get("score", 0)) >= 90:
            continue
        steps.append(PlanStep(
            id=f"step-{len(steps) + 1}-{rule.id}", action="apply_page_margin", target="page", rule_id=rule.id,
            evidence=rule.evidence, risk_level="low", auto_fixable=True, dependencies=["document_analysis"], status="planned",
            reason=f"Analyzer 的 page_margin 评分为 {item.get('score')}，低于 90；仅修改文档节页边距。", related_rule_ids=[rule.id],
            target_locator={"kind": "section_indices", "indices": list(range(document.section_count)), "semantic_role": "page"}, expected=rule.expected, field=rule.property,
        ))
    for rule in rules:
        if not (rule.target == "body" and rule.auto_fixable):
            continue
        analysis_key = "body_font" if rule.property in {"font_name", "font_size"} else "spacing_indent"
        item = breakdown.get(analysis_key)
        if item is None or int(item.get("score", 0)) >= 90:
            continue
        action = "apply_body_font" if rule.property in {"font_name", "font_size"} else "apply_body_paragraph_format"
        steps.append(PlanStep(
            id=f"step-{len(steps) + 1}-{rule.id}", action=action, target="body", rule_id=rule.id,
            evidence=rule.evidence, risk_level="low", auto_fixable=True, dependencies=["document_analysis"],
            status="planned", reason=f"Analyzer 的 {analysis_key} 评分为 {item.get('score')}，低于 90；仅修改可靠定位的正文段落。",
            related_rule_ids=[rule.id], target_locator={"kind": "paragraph_indices", "indices": document.body_paragraph_indices, "semantic_role": "body", "target_type": "body_paragraph"}, expected=rule.expected, field=rule.property,
        ))
    # The established formatter has a safe baseline body-normalization pass.
    # Keep it explicit in the plan even when the score already looks healthy:
    # this preserves the prior formatter contract without hiding execution in
    # the adapter, while reference/figure risks remain review-only.
    if not any(step.auto_fixable for step in steps):
        body_rule = next((rule for rule in rules if rule.target == "body" and rule.auto_fixable), None)
        if body_rule and document.paragraph_count:
            steps.append(
                PlanStep(
                    id=f"step-{len(steps) + 1}-body-baseline",
                    action="apply_body_font" if body_rule.property in {"font_name", "font_size"} else "apply_body_paragraph_format",
                    target="body",
                    rule_id=body_rule.id,
                    evidence=body_rule.evidence,
                    risk_level="low",
                    auto_fixable=True,
                    dependencies=["document_analysis"],
                    status="planned",
                    reason="保留既有稳定 formatter 的低风险正文规范化基线，并作为显式 PlanStep 执行。",
                    related_rule_ids=[rule.id for rule in rules if rule.target == "body" and rule.auto_fixable], expected=body_rule.expected, field=body_rule.property,
                    target_locator={"kind": "paragraph_indices", "indices": document.body_paragraph_indices, "semantic_role": "body", "target_type": "body_paragraph"},
                )
            )
    # Preserve established, narrowly scoped template-residual cleanup. It is
    # explicit rather than hidden inside any body-format action.
    steps.append(PlanStep(
        id=f"step-{len(steps) + 1}-document-hygiene", action="apply_document_hygiene", target="document",
        rule_id="legacy-document-hygiene", evidence="docx_formatter.clean_document_text/split_mixed_heading_paragraphs",
        risk_level="low", auto_fixable=True, dependencies=["document_analysis"], status="planned",
        reason="保留既有 C-51 模板残留清理和标题正文混排拆分，内容文本不做语义改写。", related_rule_ids=[],
        target_locator={"kind": "document", "semantic_role": "template_hygiene"}, expected=None,
    ))
    steps.extend(review_steps)
    requires_human_review = any(not step.auto_fixable for step in steps)
    plan_seed = document.document_id + "|" + "|".join(step.id + step.rule_id for step in steps)
    if reasoning_results:
        for step in steps:
            step.reasoning = _reasoning_for_step(step, reasoning_results)
    return ExecutionPlan(
        plan_id=f"plan-{sha256(plan_seed.encode('utf-8')).hexdigest()[:12]}",
        document_id=document.document_id,
        steps=steps,
        warnings=list(dict.fromkeys(warnings)),
        requires_human_review=requires_human_review,
    )


def local_format_step(sequence: int, rule: Rule, action: str, target: str, locator: dict[str, Any], reason: str) -> PlanStep:
    return PlanStep(
        id=f"step-{sequence + 1}-{rule.id}", action=action, target=target, rule_id=rule.id,
        evidence=rule.evidence, risk_level="low", auto_fixable=True, dependencies=["document_analysis"],
        status="planned", reason=reason, related_rule_ids=[rule.id], target_locator=locator, expected=rule.expected, field=rule.property,
    )


def _reasoning_for_step(step: PlanStep, reasoning_results: list[dict[str, Any]]) -> dict[str, Any] | None:
    for result in reasoning_results:
        if not isinstance(result, dict):
            continue
        context = result.get("context") or {}
        if result.get("issue_id") == step.rule_id or step.rule_id in (context.get("rule_ids") or []):
            return result
        issue_type = context.get("issue_type")
        if (step.target.startswith("heading") and issue_type == "heading_mismatch") or (step.target == "body" and issue_type == "paragraph_format_mismatch") or (step.target == "references" and issue_type == "reference_format_issue") or (step.target in {"figures_tables", "caption:figure", "caption:table"} and issue_type == "figure_table_issue"):
            return result
    return None


def reliable_heading_locator(document: DocumentModel, target: str) -> dict[str, Any] | None:
    style_name = target.split(":", 1)[1]
    indices = [node.paragraph_index for node in document.headings if node.style == style_name and node.confidence >= 0.9]
    if not indices:
        return None
    return {"kind": "paragraph_indices", "indices": indices, "semantic_role": "heading", "confidence": 0.95, "evidence": "Word heading style matched template heading rule"}


def reliable_caption_locator(document: DocumentModel, kind: str) -> dict[str, Any] | None:
    indices = [node.paragraph_index for node in document.captions if node.kind == kind and node.confidence >= 0.9]
    if not indices:
        return None
    return {"kind": "paragraph_indices", "indices": indices, "semantic_role": f"{kind}_caption", "confidence": 0.95, "evidence": "deterministic caption number parse"}


def review_step(rule: Rule, reason: str, related_rules: list[Rule] | None = None) -> PlanStep:
    related_rules = related_rules or [rule]
    return PlanStep(
        id=f"review-{rule.id}",
        action="human_review",
        target=rule.target,
        rule_id=rule.id,
        evidence=rule.evidence,
        risk_level="high_risk",
        auto_fixable=False,
        dependencies=["document_analysis"],
        status="human_review_required",
        reason=reason,
        related_rule_ids=[item.id for item in related_rules],
        target_locator={"kind": "semantic_role", "role": rule.target},
    )


def has_reference_risk(analysis: dict[str, Any]) -> bool:
    return bool(((analysis.get("reference_check") or {}).get("risk_items") or []))


def has_figure_table_risk(analysis: dict[str, Any]) -> bool:
    return bool(((analysis.get("figure_table_check") or {}).get("risk_items") or []))
