from __future__ import annotations

from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from db.models import Template


class TemplateRepository:
    """Small data-access boundary for persisted platform templates."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, template_id: str, version: str, name: str, school: str, document_type: str, status: str, source: str, template_path: str | None, metadata: dict[str, Any], scope: str = "platform", tenant_id: str | None = None, resource_id: str | None = None, storage_locator: str | None = None, original_filename: str | None = None, file_size: int | None = None, content_type: str | None = None, checksum: str | None = None, uploaded_by: str | None = None) -> Template:
        if scope not in {"platform", "tenant"}:
            raise ValueError("scope must be platform or tenant")
        if (scope == "platform") != (tenant_id is None):
            raise ValueError("platform templates require tenant_id=None and tenant templates require tenant_id")
        template = Template(
            **({"id": resource_id} if resource_id else {}),
            scope=scope,
            tenant_id=tenant_id,
            template_id=template_id,
            version=version,
            name=name,
            school=school,
            document_type=document_type,
            status=status,
            source=source,
            storage_locator=storage_locator,
            template_path=template_path,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            checksum=checksum,
            uploaded_by=uploaded_by,
            template_metadata=metadata,
        )
        self.session.add(template)
        self.session.flush()
        return template

    def get_resource(self, resource_id: str) -> Template | None:
        return self.session.get(Template, resource_id)

    def get_visible_resource(self, tenant_id: str | None, resource_id: str) -> Template | None:
        item = self.get_resource(resource_id)
        if item is None or (item.scope == "tenant" and item.tenant_id != tenant_id):
            return None
        return item

    def delete(self, template: Template) -> None:
        self.session.delete(template)
        self.session.flush()

    def get_by_id_and_version(self, template_id: str, version: str, *, scope: str = "platform", tenant_id: str | None = None) -> Template | None:
        return self.session.scalar(
            select(Template).where(
                Template.template_id == template_id,
                Template.version == version,
                Template.scope == scope,
                Template.tenant_id.is_(None) if scope == "platform" else Template.tenant_id == tenant_id,
            )
        )

    def get_versions(self, template_id: str, *, scope: str = "platform", tenant_id: str | None = None) -> list[Template]:
        statement = select(Template).where(Template.template_id == template_id, Template.scope == scope)
        statement = statement.where(Template.tenant_id.is_(None) if scope == "platform" else Template.tenant_id == tenant_id)
        return list(self.session.scalars(statement.order_by(Template.version.desc())).all())

    def list(self, *, school: str | None = None, document_type: str | None = None, status: str | None = None) -> list[Template]:
        statement = select(Template).where(Template.scope == "platform", Template.tenant_id.is_(None))
        if school is not None:
            statement = statement.where(Template.school == school)
        if document_type is not None:
            statement = statement.where(Template.document_type == document_type)
        if status is not None:
            statement = statement.where(Template.status == status)
        return list(self.session.scalars(statement.order_by(Template.school, Template.name, Template.version)).all())

    def list_all(self) -> list[Template]:
        """Internal persistence/bootstrap read; request paths must use list_visible."""
        return list(self.session.scalars(select(Template).order_by(Template.school, Template.name, Template.version)).all())

    def list_visible(self, tenant_id: str | None, *, school: str | None = None, document_type: str | None = None, status: str | None = None) -> list[Template]:
        statement = select(Template).where(
            or_(
                Template.scope == "platform",
                (Template.scope == "tenant") & (Template.tenant_id == tenant_id),
            )
        )
        if school is not None:
            statement = statement.where(Template.school == school)
        if document_type is not None:
            statement = statement.where(Template.document_type == document_type)
        if status is not None:
            statement = statement.where(Template.status == status)
        return list(self.session.scalars(statement.order_by(Template.school, Template.name, Template.version)).all())

    def get_visible(self, tenant_id: str | None, template_id: str, version: str) -> Template | None:
        candidates = self.resolve_visible(tenant_id, template_id=template_id, version=version)
        return candidates[0] if candidates else None

    def update_status(self, template_id: str, version: str, status: str, *, scope: str = "platform", tenant_id: str | None = None) -> Template | None:
        template = self.get_by_id_and_version(template_id, version, scope=scope, tenant_id=tenant_id)
        if template is None:
            return None
        template.status = status
        self.session.flush()
        return template

    def exists(self, template_id: str, version: str, *, scope: str = "platform", tenant_id: str | None = None) -> bool:
        return self.get_by_id_and_version(template_id, version, scope=scope, tenant_id=tenant_id) is not None

    def resolve_candidates(self, *, template_id: str | None = None, version: str | None = None, metadata: dict[str, Any] | None = None) -> list[Template]:
        candidates = self.list()
        if template_id is not None:
            candidates = [item for item in candidates if item.template_id == template_id]
        if version is not None:
            candidates = [item for item in candidates if item.version == version]
        if metadata:
            candidates = [item for item in candidates if all((item.template_metadata or {}).get(key) == value for key, value in metadata.items())]
        return candidates

    def resolve_visible(self, tenant_id: str | None, *, template_id: str | None = None, version: str | None = None, metadata: dict[str, Any] | None = None) -> list[Template]:
        candidates = self.list_visible(tenant_id)
        if template_id is not None:
            candidates = [item for item in candidates if item.template_id == template_id]
        if version is not None:
            candidates = [item for item in candidates if item.version == version]
        if metadata:
            candidates = [item for item in candidates if all((item.template_metadata or {}).get(key) == value for key, value in metadata.items())]
        return sorted(candidates, key=lambda item: item.scope == "tenant", reverse=True)
