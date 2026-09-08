from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

from docx import Document

from .docx_formatter import apply_low_risk_body_rule, apply_low_risk_page_rule, clean_document_text, describe_low_risk_page_rule, describe_low_risk_paragraph_property, split_mixed_heading_paragraphs
from .planner import ExecutionPlan, PlanStep
from .rule_engine import Rule


SUPPORTED_ACTIONS = {"apply_document_hygiene", "apply_page_margin", "apply_body_font", "apply_body_paragraph_format", "apply_body_format", "apply_heading_format", "apply_caption_format"}


@dataclass
class ExecutionResult:
    output_path: str
    executed_step_ids: list[str]
    unsupported_step_ids: list[str]
    format_log: list[str]
    changes: list[dict[str, Any]] = field(default_factory=list)
    step_statuses: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def execute_plan(plan: ExecutionPlan, source: Path, output: Path, template_path: Path | None, rules: list[Rule] | None = None) -> ExecutionResult:
    """Execute only local body-format rules; never invoke structural formatter work."""
    rule_by_id = {rule.id: rule for rule in rules or []}
    document = Document(source)
    executed: list[str] = []
    unsupported: list[str] = []
    changes: list[dict[str, Any]] = []
    statuses: dict[str, str] = {}
    format_log: list[str] = []
    for step in plan.steps:
        rule = rule_by_id.get(step.rule_id)
        locator = step.target_locator or {}
        indices = locator.get("indices")
        if step.action == "apply_document_hygiene" and step.auto_fixable:
            started = perf_counter()
            before_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            logs = [*clean_document_text(document), *split_mixed_heading_paragraphs(document)]
            after_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
            duration_ms = max(0, round((perf_counter() - started) * 1000))
            if logs:
                executed.append(step.id); statuses[step.id] = "executed"; format_log.extend(logs)
                changes.append({"change_id": f"chg-{uuid4().hex[:12]}", "document_id": plan.document_id, "rule_id": step.rule_id, "rule_type": "template_hygiene", "plan_id": plan.plan_id, "plan_step_id": step.id, "action": step.action, "target": {"semantic_role": "template_hygiene"}, "before": before_text, "after": after_text, "executor": "executor_adapter.document_hygiene", "status": "executed", "verification_status": "pending", "verification_scope": "document", "timestamp": datetime.now(timezone.utc).isoformat(), "duration_ms": duration_ms})
            else:
                statuses[step.id] = "skipped"
            continue
        if not step.auto_fixable or step.action not in SUPPORTED_ACTIONS or not rule or not isinstance(indices, list) or not indices:
            unsupported.append(step.id)
            statuses[step.id] = "unsupported"
            if rule and rule.target == "body":
                changes.append(unsupported_body_change_record(plan, step, rule, locator, "missing or invalid paragraph locator"))
            continue
        started = perf_counter()
        if rule.target in {"body", "heading", "caption:figure", "caption:table"} or rule.target.startswith("heading:"):
            if locator.get("kind") != "paragraph_indices":
                unsupported.append(step.id); statuses[step.id] = "unsupported"; continue
            before = {index: describe_low_risk_paragraph_property(document.paragraphs[index], rule.property) for index in indices if isinstance(index, int) and 0 <= index < len(document.paragraphs)}
            changed_indices = apply_low_risk_body_rule(document, indices, rule.property, rule.expected)
            after_value = lambda index: describe_low_risk_paragraph_property(document.paragraphs[index], rule.property)
            target_key = "paragraph_index"
        elif rule.target == "page" and locator.get("kind") == "section_indices":
            before = {index: describe_low_risk_page_rule(document.sections[index], rule.property) for index in indices if isinstance(index, int) and 0 <= index < len(document.sections)}
            changed_indices = apply_low_risk_page_rule(document, indices, rule.property, rule.expected)
            after_value = lambda index: describe_low_risk_page_rule(document.sections[index], rule.property)
            target_key = "section_index"
        else:
            unsupported.append(step.id); statuses[step.id] = "unsupported"; continue
        duration_ms = max(0, round((perf_counter() - started) * 1000))
        if not changed_indices:
            statuses[step.id] = "skipped"
            format_log.append(f"{step.id} 未找到可安全修改的目标。")
            if rule.target == "body":
                changes.append(unsupported_body_change_record(plan, step, rule, locator, "no in-range non-empty paragraph target"))
            continue
        executed.append(step.id)
        statuses[step.id] = "executed"
        for index in changed_indices:
            changes.append(change_record(plan, step, rule, index, target_key, locator, before.get(index), after_value(index), duration_ms))
        format_log.append(f"{step.id} 已对 {len(changed_indices)} 个 {locator.get('semantic_role', rule.target)} 目标应用 {rule.property}。")
    document.save(output)
    return ExecutionResult(str(output), executed, unsupported, format_log, changes, statuses)


def change_record(plan: ExecutionPlan, step: PlanStep, rule: Rule, index: int, target_key: str, locator: dict[str, Any], before: Any, after: Any, duration_ms: int) -> dict[str, Any]:
    target = {target_key: index, "semantic_role": locator.get("semantic_role", rule.target), "target_type": locator.get("target_type", "body_paragraph" if rule.target == "body" else None), "locator": locator}
    scope = "target" if locator.get("semantic_role") in {"body", "heading", "figure_caption", "table_caption"} else "rule"
    return {"change_id": f"chg-{uuid4().hex[:12]}", "document_id": plan.document_id, "rule_id": rule.id, "rule_type": rule.property, "plan_id": plan.plan_id, "plan_step_id": step.id, "action": step.action, "target": target, "before": before, "expected": after, "after": after, "executor": "executor_adapter.low_risk_format_rule", "status": "executed", "verification_status": "pending", "verification_scope": scope, "timestamp": datetime.now(timezone.utc).isoformat(), "duration_ms": duration_ms}


def unsupported_body_change_record(plan: ExecutionPlan, step: PlanStep, rule: Rule, locator: dict[str, Any], reason: str) -> dict[str, Any]:
    return {"change_id": f"chg-{uuid4().hex[:12]}", "document_id": plan.document_id, "rule_id": rule.id, "rule_type": rule.property, "plan_id": plan.plan_id, "plan_step_id": step.id, "action": step.action, "target": {"semantic_role": "body", "target_type": "body_paragraph", "locator": locator}, "before": None, "expected": None, "after": None, "executor": "executor_adapter.low_risk_format_rule", "status": "unsupported", "verification_status": "unsupported", "verification_scope": "target", "verification_evidence": {"reason": reason}, "timestamp": datetime.now(timezone.utc).isoformat(), "duration_ms": 0}
