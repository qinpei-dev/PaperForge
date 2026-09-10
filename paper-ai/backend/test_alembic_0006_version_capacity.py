from __future__ import annotations

import importlib.util
from pathlib import Path


MIGRATION_PATH = Path(__file__).parent / "alembic" / "versions" / "0006_day9_tenant_template_management.py"


def load_migration():
    spec = importlib.util.spec_from_file_location("migration_0006", MIGRATION_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeBind:
    def __init__(self, dialect_name: str) -> None:
        self.dialect = type("Dialect", (), {"name": dialect_name})()


class FakeOperations:
    def __init__(self, dialect_name: str) -> None:
        self.bind = FakeBind(dialect_name)
        self.statements: list[str] = []

    def get_bind(self):
        return self.bind

    def execute(self, statement) -> None:
        self.statements.append(str(statement))

    def batch_alter_table(self, _table_name: str):
        return FakeBatchAlter()

    def create_index(self, name: str, *_args, **_kwargs) -> None:
        self.statements.append(f"CREATE INDEX {name}")


class FakeBatchAlter:
    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def add_column(self, _column) -> None:
        return None

    def create_foreign_key(self, *_args, **_kwargs) -> None:
        return None


def test_0006_identity_is_stable_and_postgresql_expands_version_capacity(monkeypatch) -> None:
    migration = load_migration()
    operations = FakeOperations("postgresql")
    monkeypatch.setattr(migration, "op", operations)

    migration._ensure_postgresql_alembic_version_capacity()

    assert migration.revision == "0006_day9_tenant_template_management"
    assert migration.down_revision == "0005_day9_tenant_isolation"
    assert operations.statements == ["ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)"]


def test_0006_upgrade_expands_postgresql_version_capacity_before_schema_changes(monkeypatch) -> None:
    migration = load_migration()
    operations = FakeOperations("postgresql")
    monkeypatch.setattr(migration, "op", operations)

    migration.upgrade()

    assert operations.statements[0] == "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)"


def test_0006_leaves_sqlite_alembic_version_unchanged(monkeypatch) -> None:
    migration = load_migration()
    operations = FakeOperations("sqlite")
    monkeypatch.setattr(migration, "op", operations)

    migration._ensure_postgresql_alembic_version_capacity()

    assert operations.statements == []
