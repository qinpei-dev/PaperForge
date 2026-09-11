from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import User
from db.session import get_db

JWT_ALGORITHM = "HS256"
MIN_PRODUCTION_JWT_SECRET_LENGTH = 32
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _jwt_secret() -> str:
    configured = os.getenv("JWT_SECRET_KEY", "").strip()
    production = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "local")).strip().lower() in {"production", "prod"}
    if configured:
        if production and (len(configured) < MIN_PRODUCTION_JWT_SECRET_LENGTH or "replace-with" in configured.lower()):
            raise RuntimeError("JWT_SECRET_KEY must be a non-placeholder secret of at least 32 characters in production.")
        return configured
    if production:
        raise RuntimeError("JWT_SECRET_KEY must be configured in production.")
    return "paperforge-local-development-secret-change-me"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$16384$8$1${}${}".format(salt.hex(), digest.hex())


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        scheme, n, r, p, salt_hex, digest_hex = encoded_hash.split("$", 5)
        if scheme != "scrypt":
            return False
        actual = hashlib.scrypt(password.encode("utf-8"), salt=bytes.fromhex(salt_hex), n=int(n), r=int(r), p=int(p))
        return hmac.compare_digest(actual.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not EMAIL_PATTERN.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="请输入有效的邮箱地址。")
    return normalized


def create_access_token(user_id: str, token_version: int = 0) -> str:
    try:
        lifetime_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    except ValueError as exc:
        raise RuntimeError("JWT_EXPIRE_MINUTES must be an integer.") from exc
    if not 5 <= lifetime_minutes <= 1440:
        raise RuntimeError("JWT_EXPIRE_MINUTES must be between 5 and 1440.")
    expires = datetime.now(timezone.utc) + timedelta(minutes=lifetime_minutes)
    return jwt.encode({"sub": user_id, "ver": token_version, "exp": expires}, _jwt_secret(), algorithm=JWT_ALGORITHM)


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录后访问。", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        token_version = payload.get("ver")
        if not isinstance(user_id, str) or not isinstance(token_version, int) or isinstance(token_version, bool):
            raise ValueError("missing token claims")
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录凭证无效或已过期。", headers={"WWW-Authenticate": "Bearer"})
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在。", headers={"WWW-Authenticate": "Bearer"})
    if not hmac.compare_digest(str(token_version), str(user.token_version)):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录凭证已撤销，请重新登录。", headers={"WWW-Authenticate": "Bearer"})
    return user


def get_optional_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User | None:
    if not token:
        return None
    return get_current_user(token=token, db=db)


def auth_is_required() -> bool:
    return os.getenv("AUTH_REQUIRED", "false").strip().lower() == "true"


def configured_admin_emails() -> frozenset[str]:
    """Return the explicitly configured platform-admin email allowlist."""
    return frozenset(
        item.strip().lower()
        for item in os.getenv("ADMIN_EMAILS", "").split(",")
        if item.strip()
    )


def is_platform_admin(user: User) -> bool:
    return user.email.strip().lower() in configured_admin_emails()


def require_platform_admin(user: User = Depends(get_current_user)) -> User:
    """Authenticate and authorize a platform-admin-only endpoint."""
    if not is_platform_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要平台管理员权限。")
    return user
