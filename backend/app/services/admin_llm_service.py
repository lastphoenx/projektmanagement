"""Admin: LLM-Konfiguration pro Tenant."""

from sqlalchemy.orm import Session

from app import config
from app.core.crypto import decrypt_text_master, encrypt_text_master
from app.core.llm.errors import LLMError
from app.core.llm.ollama_client import fetch_ollama_models, ollama_reachable
from app.core.llm.provider_catalog import PROVIDERS, STATIC_MODELS
from app.core.llm.types import LlmRequest, LlmRuntimeConfig
from app.core.llm import generate_text
from app.core.crypto.classification import DataClassification
from app.models import TenantLlmConfig, User


def _env_api_key(provider_id: str) -> str | None:
    pdef = PROVIDERS.get(provider_id)
    if not pdef or not pdef.env_key_field:
        return None
    value = getattr(config.settings, pdef.env_key_field, "") or ""
    return value.strip() or None


def _resolve_base_url(provider_id: str, override: str | None) -> str | None:
    if override and override.strip():
        return override.strip().rstrip("/")
    pdef = PROVIDERS.get(provider_id)
    if not pdef:
        return None
    if provider_id == "ollama":
        return (config.settings.ollama_base_url or pdef.default_base_url or "").rstrip("/")
    return pdef.default_base_url


def _models_for_provider(provider_id: str, base_url: str | None) -> list[str]:
    if provider_id == "ollama":
        url = base_url or config.settings.ollama_base_url
        if not url:
            return []
        try:
            return fetch_ollama_models(url)
        except LLMError:
            return []
    return list(STATIC_MODELS.get(provider_id, []))


def get_admin_llm_state(db: Session, user: User) -> dict:
    active = (
        db.query(TenantLlmConfig)
        .filter(TenantLlmConfig.tenant_id == user.tenant_id, TenantLlmConfig.is_active.is_(True))
        .first()
    )

    providers_out = []
    for pid, pdef in PROVIDERS.items():
        base = _resolve_base_url(pid, active.base_url if active and active.provider == pid else None)
        env_key = _env_api_key(pid)
        configured = pdef.is_local or bool(env_key) or bool(
            active and active.provider == pid and active.api_key_encrypted
        )
        if pid == "ollama":
            configured = configured and bool(base) and ollama_reachable(base)
        providers_out.append(
            {
                "id": pid,
                "label": pdef.label,
                "is_local": pdef.is_local,
                "configured": configured,
                "base_url": base,
                "models": _models_for_provider(pid, base) if configured else [],
            }
        )

    active_provider = active.provider if active else config.settings.llm_provider
    active_model = active.model if active else (config.settings.llm_model or "")
    active_base = active.base_url if active else _resolve_base_url(active_provider, None)

    if not active_model:
        models = _models_for_provider(active_provider, active_base)
        active_model = models[0] if models else ""

    return {
        "providers": providers_out,
        "active": {
            "provider": active_provider,
            "model": active_model,
            "base_url": active_base,
            "source": "database" if active else "env",
        },
    }


def save_admin_llm_config(
    db: Session,
    user: User,
    *,
    provider: str,
    model: str,
    base_url: str | None = None,
    api_key: str | None = None,
) -> dict:
    if provider not in PROVIDERS:
        raise LLMError("Unbekannter Provider", "invalid_provider")

    db.query(TenantLlmConfig).filter(TenantLlmConfig.tenant_id == user.tenant_id).update(
        {"is_active": False}
    )

    row = (
        db.query(TenantLlmConfig)
        .filter(TenantLlmConfig.tenant_id == user.tenant_id, TenantLlmConfig.provider == provider)
        .first()
    )
    key_encrypted = None
    if api_key and api_key.strip():
        key_encrypted = encrypt_text_master(api_key.strip())
    elif row and row.api_key_encrypted:
        key_encrypted = row.api_key_encrypted
    else:
        env_key = _env_api_key(provider)
        if env_key:
            key_encrypted = encrypt_text_master(env_key)

    if row:
        row.model = model
        row.base_url = base_url
        row.api_key_encrypted = key_encrypted
        row.is_active = True
    else:
        row = TenantLlmConfig(
            tenant_id=user.tenant_id,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key_encrypted=key_encrypted,
            is_active=True,
        )
        db.add(row)
    db.flush()
    return get_admin_llm_state(db, user)


def test_admin_llm_connection(
    db: Session,
    user: User,
    *,
    provider: str,
    model: str,
    base_url: str | None = None,
) -> dict:
    pdef = PROVIDERS.get(provider)
    if not pdef:
        raise LLMError("Unbekannter Provider", "invalid_provider")

    api_key = _env_api_key(provider)
    active = (
        db.query(TenantLlmConfig)
        .filter(TenantLlmConfig.tenant_id == user.tenant_id, TenantLlmConfig.provider == provider)
        .first()
    )
    if active and active.api_key_encrypted:
        api_key = decrypt_text_master(active.api_key_encrypted)

    resolved_base = _resolve_base_url(provider, base_url)
    if provider == "ollama":
        models = fetch_ollama_models(resolved_base or config.settings.ollama_base_url)
        return {"ok": True, "message": f"Ollama OK — {len(models)} Modelle", "models": models}

    if provider not in ("openai",):
        return {"ok": False, "message": "Verbindungstest für diesen Provider noch nicht implementiert"}

    runtime = LlmRuntimeConfig(
        provider=provider,
        base_url=resolved_base,
        api_key=api_key,
        model=model,
        is_local=False,
    )
    reply = generate_text(
        runtime,
        LlmRequest(
            system_prompt="Du antwortest kurz.",
            user_prompt="Antworte nur mit: OK",
            model=model,
            max_tokens=16,
        ),
        data_classification=DataClassification.PUBLIC,
    )
    return {"ok": True, "message": f"Antwort: {reply[:80]}"}
