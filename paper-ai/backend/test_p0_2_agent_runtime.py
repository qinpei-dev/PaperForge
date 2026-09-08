from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from services.agent_runtime import run_runtime
from services.document_classifier import classify_document
from services.document_model import build_document_model
from services.docx_analyzer import analyze_docx
from services.governance import compare_structure
from services.planner import ExecutionPlan, PlanStep
from services.rule_engine import Rule, RuleSource


BASE_DIR = Path(__file__).resolve().parent
SAMPLE = BASE_DIR / "test_documents" / "clean" / "clean_001.docx"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(f"{name} FAIL")
    print(f"{name} PASS")


def make_plan(*, review: bool = False) -> tuple[Rule, ExecutionPlan]:
    rule = Rule("body-font_size", "body", "font_size", 12, RuleSource.DEFAULT, "test", 0.9, "low", True)
    step = PlanStep("step-body", "apply_body_format", "body", rule.id, rule.evidence, "low", True, [], "planned", "test", target_locator={"kind": "paragraph_indices", "indices": [4], "semantic_role": "body"})
    if review:
        step = PlanStep("review-reference", "human_review", "references", "reference-risk", "test", "high_risk", False, [], "human_review_required", "test")
    return rule, ExecutionPlan("plan-test", "doc", [step], [], review)


class Result:
    def __init__(self, data): self.data = data
    def to_dict(self): return self.data


def main() -> None:
    model = build_document_model(SAMPLE, classification=classify_document(SAMPLE))
    before = analyze_docx(SAMPLE)
    rule, plan = make_plan()
    plan.steps[0].target_locator["indices"] = model.body_paragraph_indices
    with TemporaryDirectory() as directory:
        output = lambda suffix: Path(directory) / f"{suffix}.docx"
        runtime = run_runtime(source=SAMPLE, output_factory=output, template_path=None, model=model, rules=[rule], plan=plan, before_analysis=before)
    states = [item["state"] for item in runtime["runtime_trace"]]
    check("workflow_state_path", all(state in states for state in ["ANALYZING", "PLANNING", "EXECUTING", "VERIFYING", "COMPLETED"]))
    check("verification_real_document", "structural_integrity" in runtime["verification"] and "after_document_model" in runtime["verification"])
    check("trace_components", all(component in [item["component"] for item in runtime["runtime_trace"]] for component in ["planner", "executor_adapter", "verifier", "decision_engine"]))

    calls = {"value": 0}
    def recoverable_verifier(*args):
        calls["value"] += 1
        passed = calls["value"] == 2
        return Result({"passed": passed, "failed_rules": [] if passed else [rule.id], "verified_rules": [rule.id] if passed else [], "structural_integrity": {"status": "SAFE"}, "new_issues": [], "unresolved_issues": [], "risk_level": "low", "fixable": not passed, "unsupported_step_ids": []})
    with TemporaryDirectory() as directory:
        replan_runtime = run_runtime(source=SAMPLE, output_factory=lambda suffix: Path(directory) / f"{suffix}.docx", template_path=None, model=model, rules=[rule], plan=plan, before_analysis=before, verifier=recoverable_verifier)
    check("replan_count", replan_runtime["workflow"]["replan_count"] == 1)
    check("replan_new_plan", replan_runtime["replan_history"][0]["plan"]["plan_id"] != replan_runtime["execution_plan"]["plan_id"])
    check("replan_trace", any(item["state"] == "REPLANNING" for item in replan_runtime["runtime_trace"]))

    _, high_risk_plan = make_plan(review=True)
    with TemporaryDirectory() as directory:
        hitl_runtime = run_runtime(source=SAMPLE, output_factory=lambda suffix: Path(directory) / f"{suffix}.docx", template_path=None, model=model, rules=[rule], plan=high_risk_plan, before_analysis=before)
    check("hitl_no_replan", hitl_runtime["workflow"]["current_state"] == "HUMAN_REVIEW_REQUIRED" and hitl_runtime["workflow"]["replan_count"] == 0)
    changed = model.to_dict(); changed["structural_fingerprint"] = {**changed["structural_fingerprint"], "table_count": model.table_count + 1}; changed["references"] = []
    guard = compare_structure(model.to_dict(), changed)
    check("structure_guard", guard["status"] == "UNSAFE")
    print("P0_2_AGENT_RUNTIME PASS")


if __name__ == "__main__":
    main()
