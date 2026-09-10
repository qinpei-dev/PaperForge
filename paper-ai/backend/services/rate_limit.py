"""Small single-process abuse guard; deliberately not presented as distributed protection."""

from __future__ import annotations

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request


_hits: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


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
