from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from services.document_classifier import classify_document
from services.document_model import build_document_model
from services.docx_analyzer import analyze_docx
from services.planner import build_execution_plan
from services.paper_agent import run_paper_agent
from services.rule_engine import RuleSource, normalize_rules
from services.template_extractor import extract_template_profile


BASE_DIR = Path(__file__).resolve().parent
SAMPLE = BASE_DIR / "test_documents" / "clean" / "clean_001.docx"
TEMPLATE = BASE_DIR.parent.parent / "demo_inputs" / "template_sample.docx"
RISK_SAMPLE = BASE_DIR / "test_documents" / "references" / "references_001.docx"


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(f"{name} FAIL")
    print(f"{name} PASS")


def main() -> None:
    classification = classify_document(SAMPLE)
    model = build_document_model(SAMPLE, classification=classification)
    check("document_model_id", model.document_id.startswith("docx-"))
    check("document_model_paragraphs", model.paragraph_count > 0)
    check("document_model_headings", len(model.headings) > 0)
    check("document_model_fingerprint", bool(model.structural_fingerprint.get("signature")))
    check("document_model_tables", model.table_count >= 0)

    profile = extract_template_profile(TEMPLATE)
    rules = normalize_rules(profile, template_uploaded=True)
    template_rules = [rule for rule in rules if rule.source is RuleSource.TEMPLATE]
    check("rules_nonempty", bool(rules))
    check("rules_template_source", bool(template_rules))
    check("rules_expected_value", any(rule.expected is not None for rule in template_rules))
    check("rules_evidence", all(rule.evidence for rule in rules))
    check("rules_confidence_risk", all(0 <= rule.confidence <= 1 and rule.risk_level for rule in rules))

    clean_analysis = analyze_docx(SAMPLE, template_path=TEMPLATE)
    clean_plan = build_execution_plan(model, rules, clean_analysis)
    check("plan_document_link", clean_plan.document_id == model.document_id)
    check("plan_no_satisfied_page_step", not any(step.action == "apply_page_layout" for step in clean_plan.steps))

    risk_model = build_document_model(RISK_SAMPLE, classification=classify_document(RISK_SAMPLE))
    risk_analysis = analyze_docx(RISK_SAMPLE)
    risk_plan = build_execution_plan(risk_model, normalize_rules(None), risk_analysis)
    review_steps = [step for step in risk_plan.steps if step.action == "human_review"]
    check("plan_unsatisfied_rule_step", bool(risk_plan.steps))
    check("plan_rule_evidence_chain", all(step.rule_id and step.evidence for step in risk_plan.steps))
    check("plan_high_risk_not_autofix", bool(review_steps) and all(not step.auto_fixable for step in review_steps))
    check("plan_human_review_flag", risk_plan.requires_human_review)

    # The artifacts are not standalone display models: the existing Agent
    # constructs and exposes them from the same live paper/template inputs.
    with TemporaryDirectory() as directory:
        result = run_paper_agent(SAMPLE, Path(directory), template_path=TEMPLATE, mode="local")
    check("agent_builds_document_model", result.get("status") == "ok" and bool(result.get("document_model")))
    check("agent_builds_rules", bool(result.get("rules")))
    check("agent_builds_execution_plan", result.get("execution_plan", {}).get("document_id") == result.get("document_model", {}).get("document_id"))
    print("P0_1_PLANNING_FOUNDATION PASS")


if __name__ == "__main__":
    main()
