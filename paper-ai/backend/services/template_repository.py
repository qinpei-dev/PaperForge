from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Template


class TemplateRepository:
    """Small data-access boundary for persisted platform templates."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, template_id: str, version: str, name: str, school: str, document_type: str, status: str, source: str, template_path: str | None, metadata: dict[str, Any]) -> Template:
        template = Template(
            template_id=template_id,
            version=version,
            name=name,
            school=school,
            document_type=document_type,
            status=status,
            source=source,
            template_path=template_path,
            template_metadata=metadata,
        )
        self.session.add(template)
        self.session.flush()
        return template

    def get_by_id_and_version(self, template_id: str, version: str) -> Template | None:
        return self.session.scalar(select(Template).where(Template.template_id == template_id, Template.version == version))

    def get_versions(self, template_id: str) -> list[Template]:
        return list(self.session.scalars(select(Template).where(Template.template_id == template_id).order_by(Template.version.desc())).all())

    def list(self, *, school: str | None = None, document_type: str | None = None, status: str | None = None) -> list[Template]:
        statement = select(Template)
        if school is not None:
            statement = statement.where(Template.school == school)
        if document_type is not None:
            statement = statement.where(Template.document_type == document_type)
        if status is not None:
            statement = statement.where(Template.status == status)
        return list(self.session.scalars(statement.order_by(Template.school, Template.name, Template.version)).all())

    def update_status(self, template_id: str, version: str, status: str) -> Template | None:
        template = self.get_by_id_and_version(template_id, version)
        if template is None:
            return None
        template.status = status
        self.session.flush()
        return template

    def exists(self, template_id: str, version: str) -> bool:
        return self.get_by_id_and_version(template_id, version) is not None

    def resolve_candidates(self, *, template_id: str | None = None, version: str | None = None, metadata: dict[str, Any] | None = None) -> list[Template]:
        candidates = self.list()
        if template_id is not None:
            candidates = [item for item in candidates if item.template_id == template_id]
        if version is not None:
            candidates = [item for item in candidates if item.version == version]
        if metadata:
            candidates = [item for item in candidates if all((item.template_metadata or {}).get(key) == value for key, value in metadata.items())]
        return candidates
