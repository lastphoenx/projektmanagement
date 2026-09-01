"""Admin-Dependency."""

from fastapi import Depends, HTTPException, status

from app.core.auth.dependencies import get_current_user
from app.models import User


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nur für Administratoren")
    return user
