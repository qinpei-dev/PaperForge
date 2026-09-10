from __future__ import annotations

from collections.abc import Generator
import io
from pathlib import Path
import zipfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from db.base import Base
from db.session import get_db
from main import app
from services.template_persistence import TemplatePersistenceService, refresh_template_registry
from services.template_registry import (
    BUILTIN_TEMPLATE_DEFINITIONS,
    DEFAULT_TEMPLATE_ID,
    TemplateDefinition,
    TemplateDisabledError,
    TemplateRegistry,
    template_registry,
)
from services.template_repository import TemplateRepository


def valid_docx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>"); archive.writestr("word/document.xml", "<w:document/>")
    return buffer.getvalue()


@pytest.fixture(autouse=True)
def reset_global_registry() -> Generator[None, None, None]:
    template_registry.replace(BUILTIN_TEMPLATE_DEFINITIONS)
    yield
    template_registry.replace(BUILTIN_TEMPLATE_DEFINITIONS)


@pytest.fixture
def session(tmp_path: Path) -> Generator[Session, None, None]:
    engine = create_engine(f"sqlite:///{(tmp_path / 'templates.db').as_posix()}")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def create_template(repository: TemplateRepository, *, template_id: str = "test-university-thesis", version: str = "2030.1", status: str = "active", metadata: dict | None = None):
    return repository.create(
        template_id=template_id,
        version=version,
        name="Test University Thesis",
        school="Test University",
        document_type="undergraduate_thesis",
        status=status,
        source="test",
        template_path=None,
        metadata=metadata or {"nested": {"department": "Engineering", "levels": [1, 2]}},
    )


def test_model_unique_constraint_metadata_and_status_round_trip(session: Session) -> None:
    repository = TemplateRepository(session)
    created = create_template(repository, status="deprecated")
    session.commit()
    fetched = repository.get_by_id_and_version(created.template_id, created.version)
    assert fetched is not None
    assert fetched.status == "deprecated"
    assert fetched.template_metadata == {"nested": {"department": "Engineering", "levels": [1, 2]}}

    with pytest.raises(IntegrityError):
        create_template(repository, status="active")
    session.rollback()


def test_repository_create_get_list_filter_versions_and_update_status(session: Session) -> None:
    repository = TemplateRepository(session)
    create_template(repository, version="2029.1")
    create_template(repository, version="2030.1")
    create_template(repository, template_id="other-template", version="1", metadata={"campus": "east"})
    session.commit()
    assert repository.exists("test-university-thesis", "2029.1")
    assert len(repository.get_versions("test-university-thesis")) == 2
    assert len(repository.list(school="Test University")) == 3
    assert len(repository.resolve_candidates(metadata={"campus": "east"})) == 1
    updated = repository.update_status("test-university-thesis", "2030.1", "disabled")
    session.commit()
    assert updated is not None and updated.status == "disabled"


def test_bootstrap_is_idempotent_and_never_overwrites_existing_status(session: Session) -> None:
    registry = TemplateRegistry(default_template_id=DEFAULT_TEMPLATE_ID)
    service = TemplatePersistenceService(TemplateRepository(session), registry)
    assert service.bootstrap() == 3
    assert service.bootstrap() == 0
    changed = service.repository.update_status("paperforge-standard-thesis", "2026.1", "disabled")
    assert changed is not None
    session.commit()
    assert service.bootstrap() == 0
    assert service.repository.get_by_id_and_version("paperforge-standard-thesis", "2026.1").status == "disabled"


def test_registry_rebuilds_from_db_and_resolves_dynamic_template(session: Session) -> None:
    registry = TemplateRegistry(default_template_id=DEFAULT_TEMPLATE_ID)
    service = TemplatePersistenceService(TemplateRepository(session), registry)
    service.bootstrap()
    create_template(service.repository)
    session.commit()
    service.refresh_registry()
    assert registry.resolve(template_id="test-university-thesis", version="2030.1").definition.name == "Test University Thesis"

    rebuilt = TemplateRegistry(default_template_id=DEFAULT_TEMPLATE_ID)
    TemplatePersistenceService(TemplateRepository(session), rebuilt).refresh_registry()
    assert rebuilt.resolve(template_id="test-university-thesis", version="2030.1").definition.version == "2030.1"
    service.repository.update_status("test-university-thesis", "2030.1", "disabled")
    session.commit()
    service.refresh_registry()
    with pytest.raises(TemplateDisabledError):
        registry.resolve(template_id="test-university-thesis", version="2030.1")


def test_templates_api_and_task_routes_use_persisted_registry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    engine = create_engine(f"sqlite:///{(tmp_path / 'api.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("main.SessionLocal", sessions)
    monkeypatch.setattr("main.run_agent_pipeline", lambda **_: {"status": "ok", "agent_trace": []})
    try:
        with TestClient(app) as client:
            db = sessions()
            repository = TemplateRepository(db)
            create_template(repository)
            db.commit()
            db.close()
            templates = client.get("/templates")
            assert templates.status_code == 200
            assert any(item["template_id"] == "test-university-thesis" for item in templates.json()["templates"])

            registration = client.post("/auth/register", json={"email": "template-api@example.com", "password": "password123"}).json()
            headers = {"Authorization": f"Bearer {registration['access_token']}"}
            files = {"paper": ("paper.docx", valid_docx_bytes(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            data = {"mode": "local", "allow_non_paper": "true", "template_id": "test-university-thesis", "template_version": "2030.1"}
            assert client.post("/tasks", headers=headers, files=files, data=data).status_code == 201
            missing = client.post("/tasks", headers=headers, files=files, data={**data, "template_id": "missing"})
            assert missing.status_code == 404

            db = sessions()
            TemplateRepository(db).update_status("test-university-thesis", "2030.1", "disabled")
            db.commit()
            db.close()
            disabled = client.post("/tasks", headers=headers, files=files, data=data)
            assert disabled.status_code == 422
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
