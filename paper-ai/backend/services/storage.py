"""Small storage boundary for local development and future object storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4


class StorageService(ABC):
    """Storage contract used by the API without changing existing file paths."""

    @abstractmethod
    def path_for(self, collection: str) -> Path:
        raise NotImplementedError

    @abstractmethod
    def open(self, path: Path, mode: str = "rb") -> BinaryIO:
        raise NotImplementedError


class LocalStorage(StorageService):
    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, collection: str) -> Path:
        path = self.root / collection
        path.mkdir(parents=True, exist_ok=True)
        return path

    def open(self, path: Path, mode: str = "rb") -> BinaryIO:
        return path.open(mode)


class S3Storage(StorageService):
    """Reserved adapter surface for a future S3-compatible implementation."""

    def __init__(self, bucket: str, prefix: str = "") -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")

    def path_for(self, collection: str) -> Path:
        raise NotImplementedError("S3Storage is an extension point; LocalStorage is the default.")

    def open(self, path: Path, mode: str = "rb") -> BinaryIO:
        raise NotImplementedError("S3Storage is an extension point; LocalStorage is the default.")


class TemplateStorage(ABC):
    """Stable locator boundary for managed template binaries."""

    @abstractmethod
    def save(self, tenant_id: str, resource_id: str, version: str, source: BinaryIO) -> str:
        raise NotImplementedError

    @abstractmethod
    def open(self, locator: str, mode: str = "rb") -> BinaryIO:
        raise NotImplementedError

    @abstractmethod
    def exists(self, locator: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete(self, locator: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def resolve_local_path(self, locator: str) -> Path:
        raise NotImplementedError


class LocalTemplateStorage(TemplateStorage):
    """Tenant-isolated local implementation; callers persist only its locator."""

    scheme = "local://tenant-templates/"

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, tenant_id: str, resource_id: str, version: str, source: BinaryIO) -> str:
        if not all(self._safe_segment(value) for value in (tenant_id, resource_id, version)):
            raise ValueError("invalid template storage identity")
        filename = f"{uuid4().hex}.docx"
        relative = Path(tenant_id) / resource_id / version / filename
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
        return f"{self.scheme}{relative.as_posix()}"

    def open(self, locator: str, mode: str = "rb") -> BinaryIO:
        return self.resolve_local_path(locator).open(mode)

    def exists(self, locator: str) -> bool:
        return self.resolve_local_path(locator).is_file()

    def delete(self, locator: str) -> None:
        path = self.resolve_local_path(locator)
        if path.exists():
            path.unlink()

    def resolve_local_path(self, locator: str) -> Path:
        if not locator.startswith(self.scheme):
            raise ValueError("unsupported template storage locator")
        relative = Path(locator.removeprefix(self.scheme))
        if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 4 or relative.suffix.lower() != ".docx":
            raise ValueError("invalid template storage locator")
        target = (self.root / relative).resolve()
        if self.root not in target.parents:
            raise ValueError("template storage locator escapes root")
        return target

    @staticmethod
    def _safe_segment(value: str) -> bool:
        return bool(value) and len(value) <= 200 and value == Path(value).name and "/" not in value and "\\" not in value and ".." not in value
