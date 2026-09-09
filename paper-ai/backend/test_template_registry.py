from __future__ import annotations

import json
from pathlib import Path

import pytest
from docx import Document
from docx.shared import Pt
from fastapi.testclient import TestClient

from main import app
from services.agent_pipeline import run_agent_pipeline
from services.template_extractor import extract_template_profile
from services.template_registry import (
    TemplateAmbiguousError,
    TemplateDefinition,
    TemplateDisabledError,
    TemplateNotFoundError,
    TemplateRegistry,
    TemplateRegistryError,
)


def definition(path: Path, template_id: str, version: str, **overrides: object) -> TemplateDefinition:
    values = {
        "template_id": template_id,
        "name": f"Template {template_id}",
        "school": "Test University",
        "document_type": "academic_paper",
        "version": version,
        "status": "active",
        "source": "test",
        "template_path": path,
        "metadata": {"campus": "main"},
    }
    values.update(overrides)
    return TemplateDefinition(**values)  # type: ignore[arg-type]


def test_register_get_list_and_duplicate_behavior(tmp_path: Path) -> None:
    a = tmp_path / "a.docx"
    b = tmp_path / "b.docx"
    a.write_bytes(b"a")
    b.write_bytes(b"b")
    registry = TemplateRegistry(default_template_id="family-a")
    registry.register(definition(a, "family-a", "2025.1"))
    registry.register(definition(b, "family-a", "2026.1"))
    registry.register(definition(b, "family-b", "2026.1", school="Other University"))

    assert registry.get("family-a", "2025.1").template_path == a
    assert registry.get("family-a").version == "2026.1"
    assert len(registry.list(status="active")) == 3
    assert len(registry.list(school="Other University")) == 1
    with pytest.raises(TemplateRegistryError, match="already registered"):
        registry.register(definition(a, "family-a", "2025.1"))


def test_resolution_is_exact_versioned_and_never_random(tmp_path: Path) -> None:
    first = tmp_path / "first.docx"
    second = tmp_path / "second.docx"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    registry = TemplateRegistry(
        (
            definition(first, "thesis", "2025.1", metadata={"campus": "main"}),
            definition(second, "thesis", "2026.1", metadata={"campus": "east"}),
            definition(second, "report", "2026.1", metadata={"campus": "east"}),
        ),
        default_template_id="thesis",
    )

    assert registry.resolve(template_id="thesis").definition.version == "2026.1"
    assert registry.resolve(template_id="thesis", version="2025.1").template_path == first
    with pytest.raises(TemplateNotFoundError, match="not found"):
        registry.resolve(template_id="missing")
    with pytest.raises(TemplateAmbiguousError, match="multiple templates"):
        registry.resolve(metadata={"campus": "east"})


def test_disabled_template_cannot_resolve(tmp_path: Path) -> None:
    path = tmp_path / "disabled.docx"
    path.write_bytes(b"disabled")
    registry = TemplateRegistry((definition(path, "disabled", "1", status="disabled"),))
    with pytest.raises(TemplateDisabledError, match="disabled"):
        registry.resolve(template_id="disabled")


def test_registry_and_parser_results_are_isolated(tmp_path: Path) -> None:
    paths = [tmp_path / "a.docx", tmp_path / "b.docx"]
    for path, font_size in zip(paths, (10, 16), strict=True):
        document = Document()
        document.styles["Normal"].font.size = Pt(font_size)
        document.add_paragraph(f"Template {font_size}")
        document.save(path)
    registry = TemplateRegistry((definition(paths[0], "a", "1"), definition(paths[1], "b", "1")))

    fetched_a = registry.get("a", "1")
    fetched_a.metadata["mutated"] = True
    assert "mutated" not in registry.get("a", "1").metadata
    assert "mutated" not in registry.get("b", "1").metadata

    profile_a = extract_template_profile(paths[0])
    profile_b = extract_template_profile(paths[1])
    assert profile_a is not profile_b
    assert profile_a["normal"]["font_size"] != profile_b["normal"]["font_size"]
    profile_a["normal"]["font_size"] = 99
    assert extract_template_profile(paths[1])["normal"]["font_size"] == profile_b["normal"]["font_size"]


def test_legacy_pipeline_defaults_and_records_identity(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paper = tmp_path / "paper.docx"
    paper.write_bytes(b"paper")
    output = tmp_path / "outputs"
    output.mkdir()

    def fake_agent(**kwargs: object) -> dict[str, object]:
        assert kwargs["template_path"] is None
        identity = kwargs["template_identity"]
        assert isinstance(identity, dict)
        return {"status": "ok", "steps": [], "template": identity}

    monkeypatch.setattr("services.agent_pipeline.run_paper_agent", fake_agent)
    result = run_agent_pipeline(paper, output, mode="local")
    assert result["status"] == "ok"
    assert result["resolved_template_id"] == "paperforge-general-academic"
    assert result["resolved_template_version"] == "2026.1"
    assert result["agent_trace"][0]["step"] == "resolve_template"
    state = json.loads(Path(result["task_state_path"]).read_text(encoding="utf-8"))
    assert state["template"]["id"] == "paperforge-general-academic"
    assert state["template"]["version"] == "2026.1"


def test_pipeline_resolves_requested_version_to_its_own_locator(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paper = tmp_path / "paper.docx"
    paper.write_bytes(b"paper")
    output = tmp_path / "outputs"
    output.mkdir()
    captured: dict[str, object] = {}

    def fake_agent(**kwargs: object) -> dict[str, object]:
        captured.update(kwargs)
        return {"status": "ok", "steps": []}

    monkeypatch.setattr("services.agent_pipeline.run_paper_agent", fake_agent)
    result = run_agent_pipeline(
        paper,
        output,
        mode="local",
        template_id="paperforge-standard-thesis",
        template_version="2025.1",
    )
    assert result["resolved_template_id"] == "paperforge-standard-thesis"
    assert result["resolved_template_version"] == "2025.1"
    assert Path(captured["template_path"]).name == "template_sample.docx"


def test_templates_api_lists_multiple_active_templates() -> None:
    with TestClient(app) as client:
        response = client.get("/templates")
    assert response.status_code == 200
    payload = response.json()
    assert payload["default_template_id"] == "paperforge-general-academic"
    assert payload["default_template_version"] == "2026.1"
    assert len(payload["templates"]) >= 2
    assert all(item["status"] == "active" for item in payload["templates"])
