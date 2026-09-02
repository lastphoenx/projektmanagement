"""Generisches API-Rate-Limiting pro IP (in-memory)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings
from app.core.security.login_protection import get_client_ip

_SKIP_PREFIXES = (
    "/api/v1/health",
    "/api/docs",
    "/api/openapi.json",
)
_AUTH_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/2fa/verify",
}


@dataclass
class _ApiWindow:
    timestamps: list[float] = field(default_factory=list)


_lock = threading.Lock()
_api_windows: dict[str, _ApiWindow] = {}


def _check_api_rate(ip: str) -> bool:
    now = time.time()
    window_seconds = 60
    limit = settings.api_rate_limit_per_minute

    with _lock:
        entry = _api_windows.setdefault(ip, _ApiWindow())
        cutoff = now - window_seconds
        entry.timestamps = [t for t in entry.timestamps if t > cutoff]
        if len(entry.timestamps) >= limit:
            return False
        entry.timestamps.append(now)
    return True


def reset_api_rate_state() -> None:
    with _lock:
        _api_windows.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)

        path = request.url.path
        if path in _AUTH_PATHS or any(path.startswith(p) for p in _SKIP_PREFIXES):
            return await call_next(request)

        if path.startswith("/api/"):
            ip = get_client_ip(request)
            if not _check_api_rate(ip):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Zu viele Anfragen. Bitte kurz warten."},
                )

        return await call_next(request)
