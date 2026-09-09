"""Small storage boundary for local development and future object storage."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO


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
