"""LLM-Konfiguration — User-Präferenz + .env-Credentials."""

from sqlalchemy.orm import Session

from app.core.llm.types import LlmRuntimeConfig
from app.models import User
from app.services.user_llm_service import build_runtime_config


def get_runtime_config(db: Session, user: User) -> LlmRuntimeConfig:
    return build_runtime_config(db, user)
