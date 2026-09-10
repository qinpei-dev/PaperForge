from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from db.models import Template

from .template_registry import BUILTIN_TEMPLATE_DEFINITIONS, TemplateDefinition, TemplateRegistry, template_registry
from .template_repository import TemplateRepository


def definition_from_model(model: Template) -> TemplateDefinition:
    return TemplateDefinition(
        template_id=model.template_id,
        version=model.version,
        name=model.name,
        school=model.school,
        document_type=model.document_type,
        status=model.status,
        source=model.source,
        scope=model.scope,
        tenant_id=model.tenant_id,
        template_path=Path(model.template_path) if model.template_path else None,
        metadata=model.template_metadata or {},
    )


class TemplatePersistenceService:
    """Seeds durable built-ins and makes the P0 Registry read database state."""

    def __init__(self, repository: TemplateRepository, registry: TemplateRegistry = template_registry) -> None:
        self.repository = repository
        self.registry = registry

    def bootstrap(self) -> int:
        inserted = 0
        for definition in BUILTIN_TEMPLATE_DEFINITIONS:
            if self.repository.exists(definition.template_id, definition.version):
                continue
            self.repository.create(
                template_id=definition.template_id,
                version=definition.version,
                name=definition.name,
                school=definition.school,
                document_type=definition.document_type,
                status=definition.status,
                source=definition.source,
                scope="platform",
                tenant_id=None,
                template_path=str(definition.template_path) if definition.template_path else None,
                metadata=definition.metadata,
            )
            inserted += 1
        self.repository.session.commit()
        self.refresh_registry()
        return inserted

    def refresh_registry(self) -> TemplateRegistry:
        self.registry.replace(definition_from_model(item) for item in self.repository.list_all())
        return self.registry


def bootstrap_template_registry(session: Session) -> int:
    return TemplatePersistenceService(TemplateRepository(session)).bootstrap()


def refresh_template_registry(session: Session) -> TemplateRegistry:
    return TemplatePersistenceService(TemplateRepository(session)).refresh_registry()
