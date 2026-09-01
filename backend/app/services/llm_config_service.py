"""LLM-Konfiguration — liest Tenant-DB oder .env-Fallback."""

from sqlalchemy.orm import Session

from app import config
from app.core.crypto import decrypt_text_master
from app.core.llm.errors import LLMError
from app.core.llm.provider_catalog import PROVIDERS
from app.core.llm.types import LlmRuntimeConfig
from app.models import TenantLlmConfig, User
from app.services.admin_llm_service import _env_api_key, _resolve_base_url


def get_runtime_config(db: Session, user: User) -> LlmRuntimeConfig:
    row = (
        db.query(TenantLlmConfig)
        .filter(TenantLlmConfig.tenant_id == user.tenant_id, TenantLlmConfig.is_active.is_(True))
        .first()
    )

    if row:
        pdef = PROVIDERS.get(row.provider)
        is_local = bool(pdef and pdef.is_local)
        api_key = decrypt_text_master(row.api_key_encrypted) if row.api_key_encrypted else _env_api_key(row.provider)
        base = _resolve_base_url(row.provider, row.base_url)
        if is_local:
            base = f"{base.rstrip('/')}/v1" if base and not base.endswith("/v1") else base
        return LlmRuntimeConfig(
            provider=row.provider,
            base_url=base,
            api_key=api_key or "ollama",
            model=row.model,
            is_local=is_local,
        )

    provider = config.settings.llm_provider or "ollama"
    pdef = PROVIDERS.get(provider)
    if not pdef:
        raise LLMError("Unbekannter LLM-Provider in .env", "not_configured")

    base = _resolve_base_url(provider, config.settings.llm_base_url or None)
    api_key = _env_api_key(provider) or config.settings.llm_api_key_fallback or None
    if not pdef.is_local and not api_key:
        raise LLMError("Kein LLM konfiguriert — Admin → KI-Einstellungen oder .env", "not_configured")

    if pdef.is_local and base:
        base = f"{base.rstrip('/')}/v1"

    model = config.settings.llm_model
    if not model and provider == "ollama":
        from app.core.llm.ollama_client import fetch_ollama_models

        models = fetch_ollama_models(config.settings.ollama_base_url)
        model = models[0] if models else "llama3"

    return LlmRuntimeConfig(
        provider=provider,
        base_url=base,
        api_key=api_key or "ollama",
        model=model or "gpt-4o-mini",
        is_local=pdef.is_local,
    )
