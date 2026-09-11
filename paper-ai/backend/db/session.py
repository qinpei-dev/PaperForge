from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .base import Base

load_dotenv(override=False)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./paperforge.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}


def _pool_int(name: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(name, str(default)).strip()))
    except ValueError:
        return default


engine_options: dict[str, object] = {"pool_pre_ping": True}
if not DATABASE_URL.startswith("sqlite"):
    engine_options.update(
        pool_size=_pool_int("DATABASE_POOL_SIZE", 5),
        max_overflow=_pool_int("DATABASE_MAX_OVERFLOW", 10),
        pool_timeout=_pool_int("DATABASE_POOL_TIMEOUT_SECONDS", 30),
        pool_recycle=_pool_int("DATABASE_POOL_RECYCLE_SECONDS", 1800),
    )
engine = create_engine(DATABASE_URL, connect_args=connect_args, **engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables for local compatibility mode and lightweight development use."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
