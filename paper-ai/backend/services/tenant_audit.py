from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from db.models import TenantAuditEvent

FORBIDDEN_METADATA_KEYS = frozenset({"token", "token_hash", "password", "secret", "access_token"})

def record_audit_event(db: Session, *, tenant_id: str, actor_user_id: str | None, event_type: str, target_type: str | None = None, target_id: str | None = None, metadata: dict[str, Any] | None = None) -> TenantAuditEvent:
    safe_metadata = {key: value for key, value in (metadata or {}).items() if key.lower() not in FORBIDDEN_METADATA_KEYS}
    event = TenantAuditEvent(tenant_id=tenant_id, actor_user_id=actor_user_id, event_type=event_type, target_type=target_type, target_id=target_id, metadata_json=safe_metadata)
    db.add(event)
    return event
