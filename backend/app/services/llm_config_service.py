"""LLM-Konfiguration pro Tenant (DB, verschlüsselter API-Key)."""

import uuid

from sqlalchemy.orm import Session

from app import config
from app.core.crypto import decrypt_text_master, encrypt_text_master
from app.core.llm.errors import LLMError
from app.core.llm.types import LlmRuntimeConfig
from app.models import TenantLlmConfig, User


def get_runtime_config(db: Session, user: User) -> LlmRuntimeConfig:
    row = (
        db.query(TenantLlmConfig)
        .filter(TenantLlmConfig.tenant_id == user.tenant_id, TenantLlmConfig.is_active.is_(True))
        .first()
    )

    if row:
        provider = row.provider
        model = row.model
        base_url = row.base_url
        api_key = decrypt_text_master(row.api_key_encrypted) if row.api_key_encrypted else None
        is_local = provider == "local"
        if not api_key and not is_local:
            api_key = config.settings.llm_api_key_fallback or None
        return LlmRuntimeConfig(
            provider=provider,
            base_url=base_url,
            api_key=api_key,
            model=model,
            is_local=is_local,
        )

    # Fallback: .env (Self-Host Single-Tenant)
    provider = config.settings.llm_provider
    is_local = provider == "local"
    api_key = config.settings.llm_api_key_fallback or None
    if not api_key and not is_local:
        raise LLMError("Kein LLM konfiguriert (weder DB noch .env)", "not_configured")

    return LlmRuntimeConfig(
        provider=provider,
        base_url=config.settings.llm_base_url or None,
        api_key=api_key,
        model=config.settings.llm_model,
        is_local=is_local,
    )
