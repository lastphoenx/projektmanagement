"""Session-Verwaltung mit HttpOnly-Cookie."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from starlette.requests import Request

from app.config import settings
from app.models import UserSession


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def cookie_secure_for_request(request: Request | None) -> bool:
    """Secure-Flag nur bei COOKIE_SECURE=true und erkanntem HTTPS (inkl. X-Forwarded-Proto)."""
    if not settings.cookie_secure:
        return False
    if request is None:
        return settings.cookie_secure
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "http").split(",")[0].strip()
    return proto == "https"


def _cookie_kwargs(*, secure: bool) -> dict:
    return {
        "httponly": True,
        "secure": secure,
        "samesite": settings.cookie_samesite,
        "path": "/",
    }


def generate_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(db: Session, user_id) -> tuple[str, UserSession]:
    token = generate_session_token()
    session = UserSession(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=_utcnow() + timedelta(seconds=settings.session_ttl_sec),
    )
    db.add(session)
    db.flush()
    return token, session


def get_valid_session(db: Session, token: str) -> UserSession | None:
    if not token:
        return None
    session = (
        db.query(UserSession)
        .filter(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > _utcnow(),
        )
        .first()
    )
    return session


def revoke_session(db: Session, token: str) -> None:
    session = get_valid_session(db, token)
    if session:
        session.revoked_at = _utcnow()


def revoke_all_user_sessions(db: Session, user_id) -> None:
    now = _utcnow()
    for session in (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))
        .all()
    ):
        session.revoked_at = now


def set_session_cookie(response, token: str, *, request: Request | None = None) -> None:
    secure = cookie_secure_for_request(request)
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=settings.session_ttl_sec,
        **_cookie_kwargs(secure=secure),
    )


def clear_session_cookie(response, *, request: Request | None = None) -> None:
    secure = cookie_secure_for_request(request)
    response.delete_cookie(key=settings.cookie_name, **_cookie_kwargs(secure=secure))


def set_challenge_cookie(response, token: str, *, request: Request | None = None) -> None:
    secure = cookie_secure_for_request(request)
    response.set_cookie(
        key=settings.challenge_cookie_name,
        value=token,
        max_age=settings.login_challenge_ttl_sec,
        **_cookie_kwargs(secure=secure),
    )


def clear_challenge_cookie(response, *, request: Request | None = None) -> None:
    secure = cookie_secure_for_request(request)
    response.delete_cookie(key=settings.challenge_cookie_name, **_cookie_kwargs(secure=secure))
