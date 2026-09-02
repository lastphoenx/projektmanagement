"""Login rate limiting and account lockout (in-memory, single-server)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from app.config import settings


@dataclass
class _AttemptWindow:
    timestamps: list[float] = field(default_factory=list)


@dataclass
class _UserLockout:
    failures: int = 0
    locked_until: float = 0.0


_lock = threading.Lock()
_ip_windows: dict[str, _AttemptWindow] = {}
_user_state: dict[str, _UserLockout] = {}


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _prune_window(window: _AttemptWindow, now: float, window_seconds: int) -> None:
    cutoff = now - window_seconds
    window.timestamps = [t for t in window.timestamps if t > cutoff]


def get_client_ip(request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client_ip = request.headers.get("x-client-ip")
    if client_ip:
        return client_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def check_login_allowed(ip: str, username: str) -> str | None:
    if not settings.rate_limit_enabled:
        return None

    now = time.time()
    user_key = _normalize_username(username)

    with _lock:
        user = _user_state.get(user_key)
        if user and user.locked_until > now:
            remaining = int(user.locked_until - now)
            minutes = max(1, (remaining + 59) // 60)
            return f"Konto vorübergehend gesperrt. Bitte in {minutes} Min. erneut versuchen."

        ip_entry = _ip_windows.setdefault(ip, _AttemptWindow())
        _prune_window(ip_entry, now, settings.login_ip_window_seconds)
        if len(ip_entry.timestamps) >= settings.login_max_attempts_per_ip:
            return "Zu viele Anmeldeversuche von dieser Verbindung. Bitte später erneut versuchen."

    return None


def record_login_failure(ip: str, username: str) -> None:
    if not settings.rate_limit_enabled:
        return

    now = time.time()
    user_key = _normalize_username(username)

    with _lock:
        ip_entry = _ip_windows.setdefault(ip, _AttemptWindow())
        _prune_window(ip_entry, now, settings.login_ip_window_seconds)
        ip_entry.timestamps.append(now)

        user = _user_state.setdefault(user_key, _UserLockout())
        user.failures += 1
        if user.failures >= settings.login_max_failures_per_user:
            user.locked_until = now + settings.login_lockout_seconds


def record_login_success(username: str) -> None:
    user_key = _normalize_username(username)
    with _lock:
        _user_state.pop(user_key, None)


def reset_login_protection_state() -> None:
    with _lock:
        _ip_windows.clear()
        _user_state.clear()
