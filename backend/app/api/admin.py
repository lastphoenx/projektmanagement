"""Admin-API — KI, Sicherheitskatalog und DSGVO."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth.admin import require_admin
from app.core.db import get_db
from app.core.llm.errors import LLMError
from app.core.privacy import (
    ErasureError,
    PrivacyError,
    erase_user_data,
    export_user_data,
    purge_expired_data,
)
from app.models import User
from app.services.admin_llm_service import get_admin_llm_state, test_admin_llm_connection
from app.services.admin_security_service import get_security_catalog_state

admin_router = APIRouter(prefix="/admin", tags=["admin"])


class AdminLlmTestRequest(BaseModel):
    provider: str
    model: str


@admin_router.get("/llm")
def admin_llm_get(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Infrastruktur-Status — Credentials nur in .env."""
    return get_admin_llm_state(db, user)


@admin_router.post("/llm/test")
def admin_llm_test(
    body: AdminLlmTestRequest,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        return test_admin_llm_connection(
            db,
            user,
            provider=body.provider,
            model=body.model,
        )
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY if exc.code != "invalid_provider" else 400,
            detail=exc.message,
        ) from exc


@admin_router.get("/security/catalog")
def admin_security_catalog(user: User = Depends(require_admin)):
    return get_security_catalog_state()


class PrivacyUserSummary(BaseModel):
    id: str
    is_active: bool
    is_admin: bool
    totp_enabled: bool
    created_at: str


@admin_router.get("/privacy/users", response_model=list[PrivacyUserSummary])
def admin_privacy_users(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    rows = (
        db.query(User)
        .filter(User.tenant_id == user.tenant_id)
        .order_by(User.created_at.desc())
        .all()
    )
    return [
        PrivacyUserSummary(
            id=str(u.id),
            is_active=u.is_active,
            is_admin=u.is_admin,
            totp_enabled=u.totp_enabled,
            created_at=u.created_at.isoformat(),
        )
        for u in rows
    ]


@admin_router.get("/privacy/users/{user_id}/export")
def admin_privacy_export(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        payload = export_user_data(db, user_id)
        return JSONResponse(
            content=payload,
            headers={
                "Content-Disposition": f'attachment; filename="gdpr-export-{user_id}.json"'
            },
        )
    except PrivacyError as exc:
        code = status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=exc.message) from exc


@admin_router.post("/privacy/users/{user_id}/erase")
def admin_privacy_erase(
    user_id: uuid.UUID,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        result = erase_user_data(db, admin, user_id)
        db.commit()
        return result
    except ErasureError as exc:
        db.rollback()
        code = status.HTTP_404_NOT_FOUND if exc.code == "not_found" else status.HTTP_400_BAD_REQUEST
        if exc.code == "forbidden":
            code = status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=code, detail=exc.message) from exc


@admin_router.post("/privacy/retention/purge")
def admin_privacy_purge(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    counts = purge_expired_data(db)
    db.commit()
    return {"purged": counts}
