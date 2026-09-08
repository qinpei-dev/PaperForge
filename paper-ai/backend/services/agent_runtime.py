from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Callable
from uuid import uuid4

from .executor_adapter import execute_plan
from .governance import decide, human_review_from_decision
from .planner import ExecutionPlan, PlanStep
from .verifier import verify_output


WORKFLOW_STATES = {"INITIALIZED", "ANALYZING", "PLANNING", "EXECUTING", "VERIFYING", "REPLANNING", "HUMAN_REVIEW_REQUIRED", "COMPLETED", "FAILED"}

@dataclass
class RuntimeContext:
    run_id: str = field(default_factory=lambda: f"run-{uuid4().hex[:12]}")
    current_state: str = "INITIALIZED"
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    iteration: int = 0
    replan_count: int = 0
    max_replans: int = 1
    warnings: list[str] = field(default_factory=list)
    failure_reason: str | None = None
    human_review_reason: str | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)

    def transition(self, state: str, component: str, action: str, status: str, **details: Any) -> None:
        if state not in WORKFLOW_STATES: raise ValueError(f"invalid workflow state: {state}")
        self.current_state, self.updated_at = state, datetime.now(timezone.utc).isoformat()
        self.trace.append({"event_id": f"evt-{len(self.trace)+1:02d}", "run_id": self.run_id, "timestamp": self.updated_at, "state": state, "component": component, "action": action, "step": f"{component}:{action}", "status": status, "duration_ms": details.pop("duration_ms", 0), "fallback_used": False, "message": str(details.get("decision_reason") or action), **details})

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self); data.pop("trace"); return data

def replan(previous: ExecutionPlan, failed_rules: list[str], iteration: int) -> ExecutionPlan:
    steps = [PlanStep(**{**step.to_dict(), "id": f"{step.id}-r{iteration}", "status": "replanned", "reason": f"Replan after verification failure: {', '.join(failed_rules)}"}) for step in previous.steps if step.rule_id in failed_rules or any(rule in failed_rules for rule in step.related_rule_ids)]
    return ExecutionPlan(plan_id=f"{previous.plan_id}-r{iteration}", document_id=previous.document_id, steps=steps, warnings=previous.warnings, requires_human_review=False)

def run_runtime(*, source: Path, output_factory: Callable[[str], Path], template_path: Path | None, model: Any, rules: list[Any], plan: ExecutionPlan, before_analysis: dict[str, Any], verifier: Callable[..., Any] = verify_output) -> dict[str, Any]:
    ctx = RuntimeContext(); ctx.transition("ANALYZING", "runtime", "accept_document_intelligence", "PASS")
    ctx.transition("PLANNING", "planner", "accept_execution_plan", "PASS", rule_ids=[rule.id for rule in rules])
    current_plan, execution = plan, None
    history = []
    while True:
        ctx.iteration += 1; started = perf_counter(); ctx.transition("EXECUTING", "executor_adapter", "execute_plan", "RUNNING", input_summary={"plan_id": current_plan.plan_id})
        output = output_factory("formatted" if ctx.iteration == 1 else f"replanned_{ctx.iteration}")
        execution = execute_plan(current_plan, source, output, template_path, rules)
        ctx.trace[-1].update(status="PASS", duration_ms=round((perf_counter()-started)*1000), output_summary=execution.to_dict(), rule_ids=[step.rule_id for step in current_plan.steps])
        ctx.transition("VERIFYING", "verifier", "verify_output", "RUNNING")
        verification = verifier(model, before_analysis, output, template_path, rules, current_plan, execution.unsupported_step_ids, execution.changes).to_dict()
        ctx.trace[-1].update(status="PASS" if verification["passed"] else "WARNING", output_summary={"passed": verification["passed"], "integrity": verification["structural_integrity"]["status"]}, rule_ids=verification["failed_rules"])
        decision = decide(verification, replan_count=ctx.replan_count, max_replans=ctx.max_replans, plan_requires_review=current_plan.requires_human_review)
        ctx.transition(ctx.current_state, "decision_engine", decision["action"], "PASS", decision_reason=decision["reason"], evidence=decision["evidence"])
        history.append({"plan": current_plan.to_dict(), "verification": verification, "decision": decision})
        if decision["action"] == "COMPLETE":
            ctx.transition("COMPLETED", "runtime", "complete", "PASS"); break
        if decision["action"] == "REPLAN":
            ctx.replan_count += 1; ctx.transition("REPLANNING", "replanner", "build_replan", "PASS", decision_reason=decision["reason"])
            current_plan = replan(current_plan, verification["failed_rules"], ctx.iteration + 1); continue
        if decision["action"] == "HUMAN_REVIEW":
            ctx.human_review_reason = decision["reason"]; ctx.transition("HUMAN_REVIEW_REQUIRED", "governance", "create_human_review_request", "WARNING", decision_reason=decision["reason"]); break
        ctx.failure_reason = decision["reason"]; ctx.transition("FAILED", "runtime", "fail", "ERROR", decision_reason=decision["reason"]); break
    final = history[-1]
    provenance = {"changes": final["verification"].get("provenance_changes", execution.changes), "summary": {"planned_steps": len(current_plan.steps), "executed_steps": len(execution.executed_step_ids), "unsupported_steps": len(execution.unsupported_step_ids), "change_count": len(execution.changes)}}
    return {"workflow": ctx.to_dict(), "verification": final["verification"], "decision": final["decision"], "replan_history": history[:-1], "human_review": human_review_from_decision(final["decision"], current_plan).to_dict() if ctx.current_state == "HUMAN_REVIEW_REQUIRED" else None, "provenance": provenance, "runtime_trace": ctx.trace, "runtime_metrics": {"scope": "internal regression metrics", "planning_coverage": round(len(plan.steps) / max(len(rules), 1), 2), "auto_fix_success_rate": 1.0 if final["verification"]["passed"] else 0.0, "verification_pass_rate": 1.0 if final["verification"]["passed"] else 0.0, "replan_trigger_count": ctx.replan_count, "replan_success_rate": 1.0 if ctx.replan_count and final["verification"]["passed"] else 0.0, "hitl_trigger_count": int(ctx.current_state == "HUMAN_REVIEW_REQUIRED"), "structural_preservation_rate": 1.0 if final["verification"]["structural_integrity"]["status"] != "UNSAFE" else 0.0}, "execution": execution.to_dict(), "formatted_path": execution.output_path, "execution_plan": current_plan.to_dict()}
