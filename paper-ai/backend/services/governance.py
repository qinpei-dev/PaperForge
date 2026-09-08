from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class HumanReviewRequest:
    reason: str
    severity: str
    affected_targets: list[str]
    evidence: list[str]
    related_rule_ids: list[str]
    suggested_action: str
    can_resume: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compare_structure(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_fp = before["structural_fingerprint"]
    after_fp = after["structural_fingerprint"]
    checks = []
    for key in ("paragraph_count", "table_count", "image_count", "section_count"):
        left, right = before_fp.get(key, 0), after_fp.get(key, 0)
        checks.append({"field": key, "before": left, "after": right, "changed": left != right})
    before_headings = len(before.get("headings") or [])
    after_headings = len(after.get("headings") or [])
    checks.append({"field": "heading_count", "before": before_headings, "after": after_headings, "changed": before_headings != after_headings})
    before_refs, after_refs = bool(before.get("references")), bool(after.get("references"))
    checks.append({"field": "reference_section", "before": before_refs, "after": after_refs, "changed": before_refs != after_refs})
    unsafe = [item for item in checks if (item["field"] in {"table_count", "image_count", "reference_section"} and item["changed"] and (item["after"] == 0 or item["field"] != "reference_section"))]
    # Paragraph additions can be a legitimate heading/body split; a large loss is not.
    paragraph_delta = after_fp.get("paragraph_count", 0) - before_fp.get("paragraph_count", 0)
    if paragraph_delta < -max(2, round(before_fp.get("paragraph_count", 0) * 0.05)):
        unsafe.append({"field": "paragraph_count", "reason": "unexpected_large_loss", "delta": paragraph_delta})
    status = "UNSAFE" if unsafe else ("WARNING" if any(item["changed"] for item in checks) else "SAFE")
    return {"status": status, "checks": checks, "unsafe_reasons": unsafe}


def decide(verification: dict[str, Any], *, replan_count: int, max_replans: int, plan_requires_review: bool) -> dict[str, Any]:
    integrity = (verification.get("structural_integrity") or {}).get("status")
    if integrity == "UNSAFE":
        return {"action": "HUMAN_REVIEW", "reason": "结构保护检测到不安全变化。", "risk": "high_risk", "evidence": verification.get("new_issues", [])}
    if plan_requires_review or verification.get("unsupported_step_ids"):
        return {"action": "HUMAN_REVIEW", "reason": "计划包含高风险或当前不支持的步骤。", "risk": "high_risk", "evidence": verification.get("failed_rules", [])}
    if verification.get("passed"):
        return {"action": "COMPLETE", "reason": "独立验证通过。", "risk": verification.get("risk_level", "low"), "evidence": verification.get("verified_rules", [])}
    if verification.get("fixable") and replan_count < max_replans:
        return {"action": "REPLAN", "reason": "存在明确的低风险格式未满足规则。", "risk": "low", "evidence": verification.get("failed_rules", [])}
    if verification.get("fixable"):
        return {"action": "HUMAN_REVIEW", "reason": "已达到自动重规划上限。", "risk": "medium", "evidence": verification.get("failed_rules", [])}
    return {"action": "FAIL", "reason": "验证失败且不能安全自动修复。", "risk": "high_risk", "evidence": verification.get("failed_rules", [])}


def human_review_from_decision(decision: dict[str, Any], plan: Any) -> HumanReviewRequest:
    return HumanReviewRequest(
        reason=decision["reason"], severity=decision["risk"],
        affected_targets=[step.target for step in plan.steps if not step.auto_fixable],
        evidence=[str(item) for item in decision.get("evidence") or []],
        related_rule_ids=[step.rule_id for step in plan.steps if not step.auto_fixable],
        suggested_action="由人工确认高风险结构、引用或不支持的格式修改后再恢复运行。",
        can_resume=True,
    )
