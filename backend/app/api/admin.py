"""Admin-API — KI und Sicherheitskatalog."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth.admin import require_admin
from app.core.db import get_db
from app.core.llm.errors import LLMError
from app.models import User
from app.services.admin_llm_service import get_admin_llm_state, save_admin_llm_config, test_admin_llm_connection
from app.services.admin_security_service import get_security_catalog_state

admin_router = APIRouter(prefix="/admin", tags=["admin"])


class AdminLlmSaveRequest(BaseModel):
    provider: str
    model: str
    base_url: str | None = None
    api_key: str | None = Field(default=None, max_length=512)


class AdminLlmTestRequest(BaseModel):
    provider: str
    model: str
    base_url: str | None = None


@admin_router.get("/security/catalog")
def admin_security_catalog(user: User = Depends(require_admin)):
    return get_security_catalog_state()


@admin_router.get("/llm")
def admin_llm_get(user: User = Depends(require_admin), db: Session = Depends(get_db)):
    return get_admin_llm_state(db, user)


@admin_router.put("/llm")
def admin_llm_save(
    body: AdminLlmSaveRequest,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        result = save_admin_llm_config(
            db,
            user,
            provider=body.provider,
            model=body.model,
            base_url=body.base_url,
            api_key=body.api_key,
        )
        db.commit()
        return result
    except LLMError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


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
            base_url=body.base_url,
        )
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY if exc.code != "invalid_provider" else 400,
            detail=exc.message,
        ) from exc
