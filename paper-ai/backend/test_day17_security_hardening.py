from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

import main
from db.base import Base
from db.session import get_db


@pytest.fixture
def security_client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTO_CREATE_DB", "false")
    engine = create_engine(f"sqlite:///{(tmp_path / 'day17.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override() -> Generator[Session, None, None]:
        db = sessions()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override
    monkeypatch.setattr(main, "SessionLocal", sessions)
    with TestClient(main.app) as client:
        yield client
    main.app.dependency_overrides.clear()
    engine.dispose()


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_token_version_revokes_existing_tokens_and_login_mints_a_current_version(security_client: TestClient) -> None:
    registered = security_client.post("/auth/register", json={"email": "day17@example.com", "password": "password123"})
    assert registered.status_code == 201, registered.text
    original_token = registered.json()["access_token"]
    assert security_client.get("/auth/me", headers=auth(original_token)).status_code == 200

    revoked = security_client.post("/auth/revoke-sessions", headers=auth(original_token))
    assert revoked.status_code == 200
    assert revoked.json() == {"revoked": True}
    rejected = security_client.get("/auth/me", headers=auth(original_token))
    assert rejected.status_code == 401
    assert "撤销" in rejected.json()["error"]["message"]

    login = security_client.post("/auth/login", json={"email": "day17@example.com", "password": "password123"})
    assert login.status_code == 200, login.text
    assert security_client.get("/auth/me", headers=auth(login.json()["access_token"])).status_code == 200


def test_edge_configuration_has_csp_rate_limit_and_development_compose_marker() -> None:
    root = Path(__file__).resolve().parents[2]
    nginx = (root / "deploy" / "nginx" / "paperforge.conf").read_text(encoding="utf-8")
    compose = (root / "docker-compose.yml").read_text(encoding="utf-8")

    assert "Content-Security-Policy" in nginx
    assert "limit_req_zone" in nginx
    assert "limit_req zone=paperforge_api_per_ip" in nginx
    assert "Development-only Compose stack" in compose
    assert "name: paperforge-dev" in compose
