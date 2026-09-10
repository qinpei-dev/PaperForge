"""Small, dependency-free production diagnostics helpers."""

from __future__ import annotations

import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any


_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_tenant_id: ContextVar[str | None] = ContextVar("tenant_id", default=None)
_user_id: ContextVar[str | None] = ContextVar("user_id", default=None)
_task_id: ContextVar[str | None] = ContextVar("task_id", default=None)
SENSITIVE_FIELD_PARTS = ("authorization", "token", "password", "secret", "api_key", "apikey", "paper_text", "raw_text", "file_content", "content")


def bind_context(*, request_id: str | None = None, tenant_id: str | None = None, user_id: str | None = None, task_id: str | None = None) -> None:
    if request_id is not None: _request_id.set(str(request_id))
    if tenant_id is not None: _tenant_id.set(str(tenant_id))
    if user_id is not None: _user_id.set(str(user_id))
    if task_id is not None: _task_id.set(str(task_id))


def clear_context() -> None:
    _request_id.set(None); _tenant_id.set(None); _user_id.set(None); _task_id.set(None)


def context_fields() -> dict[str, str | None]:
    return {"request_id": _request_id.get(), "tenant_id": _tenant_id.get(), "user_id": _user_id.get(), "task_id": _task_id.get()}


def is_sensitive_field(name: str) -> bool:
    return any(part in name.lower() for part in SENSITIVE_FIELD_PARTS)


def safe_value(value: Any, *, field_name: str = "") -> Any:
    if is_sensitive_field(field_name): return "[REDACTED]"
    if isinstance(value, dict): return {str(key): safe_value(item, field_name=str(key)) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)): return [safe_value(item, field_name=field_name) for item in value]
    if isinstance(value, str): return value[:512]
    return value


class StructuredJsonFormatter(logging.Formatter):
    """Emit a stable JSON-per-line record without request payloads."""
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname, **context_fields(), "event": getattr(record, "event", record.name), "duration_ms": getattr(record, "duration_ms", None), "message": safe_value(record.getMessage(), field_name="message")}
        for key in ("request_id", "tenant_id", "user_id", "task_id", "event", "duration_ms", "error_code", "status_code", "method", "path"):
            if hasattr(record, key): payload[key] = safe_value(getattr(record, key), field_name=key)
        return json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":"))


def configure_structured_logging() -> None:
    root = logging.getLogger()
    if any(isinstance(handler.formatter, StructuredJsonFormatter) for handler in root.handlers): return
    handler = logging.StreamHandler(); handler.setFormatter(StructuredJsonFormatter())
    root.handlers.clear(); root.addHandler(handler); root.setLevel(logging.INFO)


def log_event(logger: logging.Logger, level: int, event: str, *, duration_ms: int | None = None, **fields: Any) -> None:
    logger.log(level, event, extra={"event": event, "duration_ms": duration_ms, **safe_value(fields)})
