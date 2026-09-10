from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from re import split
from threading import RLock
from typing import Any, Iterable


TEMPLATE_STATUSES = {"active", "deprecated", "disabled"}
TEMPLATE_SCOPES = {"platform", "tenant"}


class TemplateRegistryError(ValueError):
    """Base error for deterministic template registration and resolution failures."""


class TemplateNotFoundError(TemplateRegistryError):
    pass


class TemplateAmbiguousError(TemplateRegistryError):
    pass


class TemplateDisabledError(TemplateRegistryError):
    pass


@dataclass(frozen=True)
class TemplateDefinition:
    template_id: str
    name: str
    school: str
    document_type: str
    version: str
    status: str
    source: str
    scope: str = "platform"
    tenant_id: str | None = None
    template_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.template_id.strip() or not self.version.strip():
            raise TemplateRegistryError("template_id and version are required")
        if self.status not in TEMPLATE_STATUSES:
            raise TemplateRegistryError(f"invalid template status: {self.status}")
        if self.scope not in TEMPLATE_SCOPES:
            raise TemplateRegistryError(f"invalid template scope: {self.scope}")
        if (self.scope == "platform") != (self.tenant_id is None):
            raise TemplateRegistryError("platform templates require tenant_id=null and tenant templates require tenant_id")
        object.__setattr__(self, "metadata", deepcopy(self.metadata))
        if self.template_path is not None:
            object.__setattr__(self, "template_path", Path(self.template_path))

    def clone(self) -> "TemplateDefinition":
        return TemplateDefinition(
            template_id=self.template_id,
            name=self.name,
            school=self.school,
            document_type=self.document_type,
            version=self.version,
            status=self.status,
            source=self.source,
            scope=self.scope,
            tenant_id=self.tenant_id,
            template_path=self.template_path,
            metadata=deepcopy(self.metadata),
        )

    def public_dict(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "name": self.name,
            "school": self.school,
            "document_type": self.document_type,
            "version": self.version,
            "status": self.status,
            "source": self.source,
            "scope": self.scope,
            "tenant_id": self.tenant_id,
            "metadata": deepcopy(self.metadata),
        }


@dataclass(frozen=True)
class ResolvedTemplate:
    definition: TemplateDefinition
    template_path: Path | None
    resolution: str

    def provenance(self) -> dict[str, Any]:
        return {
            "id": self.definition.template_id,
            "version": self.definition.version,
            "name": self.definition.name,
            "school": self.definition.school,
            "document_type": self.definition.document_type,
            "status": self.definition.status,
            "source": self.definition.source,
            "scope": self.definition.scope,
            "tenant_id": self.definition.tenant_id,
            "resolution": self.resolution,
            "metadata": deepcopy(self.definition.metadata),
        }


class TemplateRegistry:
    """Small in-memory registry; definitions are cloned at every boundary."""

    def __init__(self, definitions: Iterable[TemplateDefinition] = (), *, default_template_id: str | None = None) -> None:
        self._definitions: dict[tuple[str, str | None, str, str], TemplateDefinition] = {}
        self._lock = RLock()
        self.default_template_id = default_template_id
        for definition in definitions:
            self.register(definition)

    def register(self, definition: TemplateDefinition) -> TemplateDefinition:
        key = (definition.scope, definition.tenant_id, definition.template_id, definition.version)
        with self._lock:
            if key in self._definitions:
                raise TemplateRegistryError(f"template already registered: {definition.template_id}@{definition.version}")
            stored = definition.clone()
            self._definitions[key] = stored
            return stored.clone()

    def replace(self, definitions: Iterable[TemplateDefinition]) -> None:
        """Atomically replace runtime entries with definitions loaded from persistence."""
        replacement: dict[tuple[str, str | None, str, str], TemplateDefinition] = {}
        for definition in definitions:
            key = (definition.scope, definition.tenant_id, definition.template_id, definition.version)
            if key in replacement:
                raise TemplateRegistryError(f"duplicate template in replacement: {definition.template_id}@{definition.version}")
            replacement[key] = definition.clone()
        with self._lock:
            self._definitions = replacement

    def get(self, template_id: str, version: str | None = None, *, tenant_id: str | None = None) -> TemplateDefinition:
        with self._lock:
            candidates = [
                item
                for item in self._definitions.values()
                if item.template_id == template_id and (item.scope == "platform" or item.tenant_id == tenant_id)
            ]
        if version is not None:
            candidates = [item for item in candidates if item.version == version]
        if not candidates:
            suffix = f"@{version}" if version else ""
            raise TemplateNotFoundError(f"template not found: {template_id}{suffix}")
        if version is None:
            candidates.sort(key=lambda item: _version_key(item.version), reverse=True)
        candidates.sort(key=lambda item: item.scope == "tenant", reverse=True)
        return candidates[0].clone()

    def list(
        self,
        *,
        school: str | None = None,
        document_type: str | None = None,
        status: str | None = None,
        tenant_id: str | None = None,
    ) -> list[TemplateDefinition]:
        with self._lock:
            values = list(self._definitions.values())
        filtered = [
            item
            for item in values
            if (school is None or item.school == school)
            and (document_type is None or item.document_type == document_type)
            and (status is None or item.status == status)
            and (item.scope == "platform" or item.tenant_id == tenant_id)
        ]
        return [item.clone() for item in sorted(filtered, key=lambda item: (item.school, item.name, _version_key(item.version)))]

    def resolve(
        self,
        *,
        template_id: str | None = None,
        version: str | None = None,
        metadata: dict[str, Any] | None = None,
        tenant_id: str | None = None,
    ) -> ResolvedTemplate:
        if template_id:
            definition = self.get(template_id, version, tenant_id=tenant_id)
            if version is None and definition.status == "disabled":
                alternatives = [item for item in self.list(tenant_id=tenant_id) if item.template_id == template_id and item.status != "disabled"]
                if alternatives:
                    definition = max(alternatives, key=lambda item: _version_key(item.version))
            return self._resolved(definition, "template_id_and_version" if version else "template_id")
        if version:
            raise TemplateRegistryError("template_version requires template_id")
        if metadata:
            candidates = [item for item in self.list(status="active", tenant_id=tenant_id) if _matches_metadata(item, metadata)]
            if not candidates:
                raise TemplateNotFoundError("no active template matches the requested metadata")
            if len(candidates) > 1:
                identities = ", ".join(f"{item.template_id}@{item.version}" for item in candidates)
                raise TemplateAmbiguousError(f"multiple templates match the requested metadata: {identities}")
            return self._resolved(candidates[0], "metadata")
        if not self.default_template_id:
            raise TemplateNotFoundError("no default template is configured")
        return self._resolved(self.get(self.default_template_id, tenant_id=tenant_id), "default")

    @staticmethod
    def _resolved(definition: TemplateDefinition, resolution: str) -> ResolvedTemplate:
        if definition.status == "disabled":
            raise TemplateDisabledError(f"template is disabled: {definition.template_id}@{definition.version}")
        if definition.template_path is not None and not definition.template_path.is_file():
            raise TemplateNotFoundError(f"template locator is unavailable: {definition.template_id}@{definition.version}")
        return ResolvedTemplate(definition, definition.template_path, resolution)


def _version_key(version: str) -> tuple[tuple[int, Any], ...]:
    return tuple((0, int(part)) if part.isdigit() else (1, part.lower()) for part in split(r"([0-9]+)", version) if part)


def _matches_metadata(definition: TemplateDefinition, requested: dict[str, Any]) -> bool:
    searchable = {
        "school": definition.school,
        "document_type": definition.document_type,
        "status": definition.status,
        **definition.metadata,
    }
    return all(searchable.get(key) == value for key, value in requested.items())


_BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_TEMPLATE_ID = "paperforge-general-academic"

BUILTIN_TEMPLATE_DEFINITIONS = (
        TemplateDefinition(
            template_id=DEFAULT_TEMPLATE_ID,
            name="PaperForge 通用学术论文规范",
            school="通用",
            document_type="academic_paper",
            version="2026.1",
            status="active",
            source="built_in_rules",
            metadata={"is_default": True, "family": "paperforge-general-academic"},
        ),
        TemplateDefinition(
            template_id="paperforge-standard-thesis",
            name="PaperForge 标准毕业论文模板",
            school="通用",
            document_type="undergraduate_thesis",
            version="2026.1",
            status="active",
            source="bundled_docx",
            template_path=_BACKEND_DIR / "templates" / "template.docx",
            metadata={"family": "paperforge-standard-thesis"},
        ),
        TemplateDefinition(
            template_id="paperforge-standard-thesis",
            name="PaperForge 标准毕业论文模板",
            school="通用",
            document_type="undergraduate_thesis",
            version="2025.1",
            status="deprecated",
            source="bundled_docx",
            template_path=_BACKEND_DIR / "templates" / "template_sample.docx",
            metadata={"family": "paperforge-standard-thesis"},
        ),
    )
template_registry = TemplateRegistry(
    BUILTIN_TEMPLATE_DEFINITIONS,
    default_template_id=DEFAULT_TEMPLATE_ID,
)


def resolve_template_request(
    *,
    template_path: Path | None = None,
    template_id: str | None = None,
    template_version: str | None = None,
    metadata: dict[str, Any] | None = None,
    tenant_id: str | None = None,
) -> ResolvedTemplate:
    if template_id:
        return template_registry.resolve(template_id=template_id, version=template_version, tenant_id=tenant_id)
    if template_path is not None:
        uploaded = TemplateDefinition(
            template_id="legacy-uploaded-template",
            name=template_path.name,
            school="用户提供",
            document_type="academic_document",
            version="unversioned",
            status="active",
            source="legacy_upload",
            scope="tenant" if tenant_id else "platform",
            tenant_id=tenant_id,
            template_path=template_path,
            metadata={"compatibility_mode": True},
        )
        return TemplateRegistry._resolved(uploaded, "legacy_upload")
    return template_registry.resolve(version=template_version, metadata=metadata, tenant_id=tenant_id)
