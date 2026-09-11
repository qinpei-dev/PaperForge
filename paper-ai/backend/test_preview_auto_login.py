from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

import main
from db.base import Base
from db.models import User
from db.session import get_db
from services.task_worker import TaskWorker


@pytest.fixture
def preview_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[tuple[TestClient, sessionmaker[Session]], None, None]:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("PAPERFORGE_PREVIEW_AUTO_LOGIN", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    engine = create_engine(f"sqlite:///{(tmp_path / 'preview.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(main, "SessionLocal", sessions)
    worker = TaskWorker()
    monkeypatch.setattr(main, "task_worker", worker)
    with TestClient(main.app) as client:
        try:
            yield client, sessions
        finally:
            worker.shutdown()
    main.app.dependency_overrides.clear()
    engine.dispose()


def test_preview_login_creates_reserved_user_and_returns_normal_jwt(
    preview_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, sessions = preview_client

    response = client.post("/auth/preview-login")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["user"]["email"] == "preview@paperforge.local"
    assert payload["access_token"]
    assert payload["workspace_id"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "preview@paperforge.local"

    repeat = client.post("/auth/preview-login")
    assert repeat.status_code == 200
    assert repeat.json()["user"]["id"] == payload["user"]["id"]

    db = sessions()
    try:
        users = list(db.scalars(select(User).where(User.email == "preview@paperforge.local")).all())
        assert len(users) == 1
        assert users[0].password_hash.startswith("scrypt$")
    finally:
        db.close()


def test_preview_login_is_unavailable_in_production(preview_client: tuple[TestClient, sessionmaker[Session]], monkeypatch: pytest.MonkeyPatch) -> None:
    client, _ = preview_client
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "a" * 32)
    response = client.post("/auth/preview-login")
    assert response.status_code == 404
