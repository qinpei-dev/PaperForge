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
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _jwt_secret() -> str:
    configured = os.getenv("JWT_SECRET_KEY", "").strip()
    if configured:
        return configured
    if os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "local")).strip().lower() in {"production", "prod"}:
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


def create_access_token(user_id: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "1440")))
    return jwt.encode({"sub": user_id, "exp": expires}, _jwt_secret(), algorithm=JWT_ALGORITHM)


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="需要登录后访问。", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise ValueError("missing subject")
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录凭证无效或已过期。", headers={"WWW-Authenticate": "Bearer"})
    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在。", headers={"WWW-Authenticate": "Bearer"})
    return user


def get_optional_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User | None:
    if not token:
        return None
    return get_current_user(token=token, db=db)


def auth_is_required() -> bool:
    return os.getenv("AUTH_REQUIRED", "false").strip().lower() == "true"
