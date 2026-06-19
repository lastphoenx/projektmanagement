"""FastAPI-Dependencies für authentifizierte Requests."""

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.auth.sessions import get_valid_session
from app.core.db import get_db
from app.models import User


def get_current_user(
    db: Session = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=settings.cookie_name),
) -> User:
    session = get_valid_session(db, session_token or "")
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nicht angemeldet")
    user = db.get(User, session.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Benutzer inaktiv")
    return user


def get_challenge_token(
    challenge_token: str | None = Cookie(default=None, alias=settings.challenge_cookie_name),
) -> str:
    if not challenge_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="2FA-Challenge fehlt")
    return challenge_token
