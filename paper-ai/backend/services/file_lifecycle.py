"""Small, conservative local-file lifecycle helpers.

Only files that are not referenced by durable Task/Artifact rows are eligible
for cleanup.  Formal output artifacts are therefore never removed by this
module.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Artifact, Task


@dataclass(frozen=True)
class CleanupCandidate:
    path: Path
    reason: str


def retention_days(default: int = 30) -> int:
    """Read the configured retention window without allowing unsafe values."""
    import os

    try:
        value = int(os.getenv("PAPERFORGE_RETENTION_DAYS", str(default)))
    except ValueError:
        value = default
    return max(1, min(value, 3650))


def _referenced_paths(db: Session) -> set[Path]:
    referenced: set[Path] = set()
    for path in db.scalars(select(Task.uploaded_file).where(Task.uploaded_file.is_not(None))).all():
        if path:
            referenced.add(Path(path).resolve())
    for task in db.scalars(select(Task)).all():
        metadata = task.input_metadata if isinstance(task.input_metadata, dict) else {}
        template_path = metadata.get("template_upload_path")
        if isinstance(template_path, str) and template_path:
            referenced.add(Path(template_path).resolve())
    for path in db.scalars(select(Artifact.file_path)).all():
        if path:
            referenced.add(Path(path).resolve())
    return referenced


def find_orphan_files(
    db: Session,
    *,
    roots: Iterable[Path],
    older_than_days: int | None = None,
    now: datetime | None = None,
) -> list[CleanupCandidate]:
    """Return old unreferenced files; no filesystem mutation is performed."""
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=older_than_days or retention_days())
    referenced = _referenced_paths(db)
    candidates: list[CleanupCandidate] = []
    for root in roots:
        root = root.resolve()
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.resolve() in referenced:
                continue
            modified = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            if modified < cutoff:
                candidates.append(CleanupCandidate(path=path, reason="unreferenced_and_expired"))
    return sorted(candidates, key=lambda item: str(item.path))


def delete_candidates(candidates: Iterable[CleanupCandidate]) -> int:
    deleted = 0
    for candidate in candidates:
        candidate.path.unlink(missing_ok=True)
        deleted += 1
    return deleted
