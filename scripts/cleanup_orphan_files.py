"""List or remove expired, unreferenced local PaperForge files.

The command is intentionally dry-run by default.  Use ``--apply`` only in a
maintenance window after reviewing the printed candidates.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = SCRIPT_ROOT / "paper-ai" / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from db.session import SessionLocal  # noqa: E402
from services.file_lifecycle import delete_candidates, find_orphan_files, retention_days  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="delete the listed candidates")
    parser.add_argument("--retention-days", type=int, default=None, help="override PAPERFORGE_RETENTION_DAYS")
    args = parser.parse_args()
    days = args.retention_days if args.retention_days is not None else retention_days()
    if days < 1:
        parser.error("--retention-days must be at least 1")

    roots = [BACKEND_ROOT / "uploads", BACKEND_ROOT / "outputs", BACKEND_ROOT / "task_states"]
    db = SessionLocal()
    try:
        candidates = find_orphan_files(db, roots=roots, older_than_days=days)
        for candidate in candidates:
            print(f"{'DELETE' if args.apply else 'CANDIDATE'} {candidate.path} ({candidate.reason})")
        if args.apply:
            print(f"CLEANUP PASS: deleted={delete_candidates(candidates)} retention_days={days}")
        else:
            print(f"CLEANUP DRY-RUN PASS: candidates={len(candidates)} retention_days={days}")
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError) as exc:
        print(f"CLEANUP FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
