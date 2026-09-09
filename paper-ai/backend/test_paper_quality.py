from __future__ import annotations

import json
from pathlib import Path

from services.paper_quality import analyze_paper_quality
from services.agent_pipeline import run_agent_pipeline
from services.task_state import init_task_state, update_task_state


def _inputs() -> tuple[dict, list[dict], dict]:
    analysis = {"confidence": 0.9, "sections": [{"type": "introduction"}], "elements": [{"semantic_type": "body"}], "metadata": {"reference_count": 3, "figure_count": 1, "table_count": 1}}
    reasoning = [{"issue_id": "ref-1", "context": {"issue_type": "reference_format_issue"}, "confidence": 0.8, "recommendation": "review"}]
    verification = {"passed": True, "verification_summary": {"total": 4, "verified": 3, "failed": 1}, "structural_integrity": {"status": "SAFE"}}
    return analysis, reasoning, verification


def test_quality_scores_dimensions_and_links_evidence() -> None:
    report = analyze_paper_quality(*_inputs())
    assert 0 <= report["overall_score"] <= 100
    assert set(report["dimensions"]) == {"format", "structure", "reference", "visual"}
    assert report["dimensions"]["format"]["evidence"]["verified"] == 3
    assert report["dimensions"]["reference"]["evidence"]["issue_ids"] == ["ref-1"]
    assert 0 <= report["confidence"] <= 1


def test_quality_report_task_state_is_backward_compatible(tmp_path: Path) -> None:
    path = tmp_path / "task.json"
    state, started = init_task_state(path, task_id="quality", mode="local", paper_path=tmp_path / "paper.docx", template_path=None)
    assert state["quality_report"] is None
    updated = update_task_state(path, state, status="succeeded", started_at=started, result={"status": "ok"}, output_dir=tmp_path)
    assert updated["quality_report"] is None
    assert json.loads(path.read_text(encoding="utf-8"))["quality_report"] is None


def test_pipeline_persists_quality_report(tmp_path: Path) -> None:
    sample = Path(__file__).parent / "test_documents" / "clean" / "clean_001.docx"
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    result = run_agent_pipeline(sample, output_dir, mode="local")
    assert result["status"] == "ok"
    assert set(result["quality_report"]["dimensions"]) == {"format", "structure", "reference", "visual"}
    state = json.loads(Path(result["task_state_path"]).read_text(encoding="utf-8"))
    assert state["quality_report"]["overall_score"] == result["quality_report"]["overall_score"]
