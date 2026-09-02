"""Benutzer-API — persönliche KI-Einstellungen (ohne Credentials)."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth.dependencies import get_current_user
from app.core.db import get_db
from app.core.llm.errors import LLMError
from app.models import User
from app.services.user_llm_service import get_user_llm_state, save_user_llm_preference, test_user_llm_connection

settings_router = APIRouter(prefix="/settings", tags=["settings"])


class UserLlmSaveRequest(BaseModel):
    provider: str = Field(max_length=32)
    model: str = Field(max_length=128)


class UserLlmTestRequest(BaseModel):
    provider: str = Field(max_length=32)
    model: str = Field(max_length=128)


@settings_router.get("/llm")
def user_llm_get(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_llm_state(db, user)


@settings_router.put("/llm")
def user_llm_save(
    body: UserLlmSaveRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = save_user_llm_preference(db, user, provider=body.provider, model=body.model)
        db.commit()
        return result
    except LLMError as exc:
        db.rollback()
        code = status.HTTP_400_BAD_REQUEST
        if exc.code == "not_configured":
            code = status.HTTP_503_SERVICE_UNAVAILABLE
        raise HTTPException(status_code=code, detail=exc.message) from exc


@settings_router.post("/llm/test")
def user_llm_test(
    body: UserLlmTestRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return test_user_llm_connection(db, user, provider=body.provider, model=body.model)
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY if exc.code != "invalid_provider" else 400,
            detail=exc.message,
        ) from exc
