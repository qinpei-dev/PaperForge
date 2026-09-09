from __future__ import annotations

import json
from pathlib import Path

from services.ai_reasoning import generate_reasoning
from services.document_model import build_document_model
from services.planner import build_execution_plan
from services.rule_engine import normalize_rules
from services.task_state import init_task_state


def _issues() -> list[dict[str, object]]:
    return [
        {"issue_id": "heading-1", "issue_type": "heading_mismatch", "score": 70, "confidence": 0.9},
        {"issue_id": "body-1", "issue_type": "paragraph_format_mismatch", "score": 80},
        {"issue_id": "reference-1", "issue_type": "reference_format_issue", "risk_level": "high_risk"},
        {"issue_id": "figure-1", "issue_type": "figure_table_issue", "risk_level": "high_risk"},
    ]


def test_reasoning_generates_explanations_and_confidence() -> None:
    results = generate_reasoning({"confidence": 0.9}, _issues(), [{"id": "body-font", "target": "body", "confidence": 0.8}])
    assert len(results) == 4
    assert all(item["reason"] and item["recommendation"] for item in results)
    assert all(0 <= item["confidence"] <= 1 for item in results)
    assert {item["context"]["issue_type"] for item in results} == {"heading_mismatch", "paragraph_format_mismatch", "reference_format_issue", "figure_table_issue"}


def test_planner_attaches_reasoning_to_plan_steps() -> None:
    sample = Path(__file__).parent / "test_documents" / "clean" / "clean_001.docx"
    model = build_document_model(sample, classification={"document_type": "academic_paper"})
    rules = normalize_rules(None)
    reasoning = generate_reasoning({"confidence": 0.9}, [{"issue_id": "body-1", "issue_type": "paragraph_format_mismatch", "score": 70}], [rule.to_dict() for rule in rules])
    plan = build_execution_plan(model, rules, {"report": {"breakdown": [{"key": "body_font", "score": 70}]}}, reasoning)
    assert any(step.reasoning and step.reasoning["issue_id"] == "body-1" for step in plan.steps if step.target == "body")


def test_reasoning_task_state_and_legacy_init_compatibility(tmp_path: Path) -> None:
    path = tmp_path / "task.json"
    state, started = init_task_state(path, task_id="legacy", mode="local", paper_path=tmp_path / "paper.docx", template_path=None)
    assert state["reasoning_results"] == []
    assert json.loads(path.read_text(encoding="utf-8"))["reasoning_results"] == []
