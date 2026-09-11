"""Small single-process abuse guard; deliberately not presented as distributed protection."""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request


_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()
DEFAULT_API_RATE_LIMIT_PER_MINUTE = 600


def api_rate_limit_per_minute() -> int:
    """Return the process-local baseline limit; edge infrastructure remains required."""
    import os

    raw = os.getenv("API_RATE_LIMIT_PER_MINUTE", str(DEFAULT_API_RATE_LIMIT_PER_MINUTE)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_API_RATE_LIMIT_PER_MINUTE


def reset_rate_limits() -> None:
    """Clear in-process state for deterministic tests and local rehearsal."""
    with _lock:
        _hits.clear()


def enforce_rate_limit(request: Request, *, bucket: str, limit: int, window_seconds: int = 60) -> None:
    """Bound requests per process/client IP. Reverse proxies must rate-limit too."""
    client = request.client.host if request.client else "unknown"
    now = monotonic()
    key = f"{bucket}:{client}"
    with _lock:
        history = _hits[key]
        while history and history[0] <= now - window_seconds:
            history.popleft()
        if len(history) >= limit:
            raise HTTPException(status_code=429, detail="请求过于频繁，请稍后重试。", headers={"Retry-After": str(window_seconds)})
        history.append(now)
