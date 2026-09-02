"""LLM-Provider-Hilfsfunktionen — Credentials nur aus .env, keine URLs in API-Antworten."""

from app import config
from app.core.llm.errors import LLMError
from app.core.llm.model_catalog import (
    DEFAULT_MODELS,
    filter_ollama_models,
    pick_default_from_list,
)
from app.core.llm.ollama_client import fetch_ollama_models, ollama_reachable
from app.core.llm.provider_catalog import PROVIDERS, STATIC_MODELS


def env_api_key(provider_id: str) -> str | None:
    pdef = PROVIDERS.get(provider_id)
    if not pdef or not pdef.env_key_field:
        return None
    value = getattr(config.settings, pdef.env_key_field, "") or ""
    return value.strip() or None


def env_default_model(provider_id: str) -> str:
    mapping = {
        "ollama": config.settings.llm_model_ollama,
        "openai": config.settings.llm_model_openai,
        "anthropic": config.settings.llm_model_anthropic,
    }
    specific = (mapping.get(provider_id) or "").strip()
    if specific:
        return specific
    legacy = (config.settings.llm_model or "").strip()
    if legacy and (config.settings.llm_provider or "ollama") == provider_id:
        return legacy
    return ""


def resolve_base_url(provider_id: str) -> str | None:
    """Interne URL-Auflösung — nie an Clients zurückgeben."""
    pdef = PROVIDERS.get(provider_id)
    if not pdef:
        return None
    if provider_id == "ollama":
        return (config.settings.ollama_base_url or "").strip().rstrip("/") or None
    return pdef.default_base_url


def provider_is_configured(provider_id: str) -> bool:
    pdef = PROVIDERS.get(provider_id)
    if not pdef:
        return False
    if pdef.is_local:
        base = resolve_base_url(provider_id)
        return bool(base) and ollama_reachable(base)
    return bool(env_api_key(provider_id))


def models_for_provider(provider_id: str) -> list[str]:
    if provider_id == "ollama":
        base = resolve_base_url("ollama")
        if not base:
            return []
        try:
            return filter_ollama_models(fetch_ollama_models(base))
        except LLMError:
            return []
    return list(STATIC_MODELS.get(provider_id, []))


def list_providers_for_ui() -> list[dict]:
    out = []
    for pid, pdef in PROVIDERS.items():
        configured = provider_is_configured(pid)
        out.append(
            {
                "id": pid,
                "label": pdef.label,
                "is_local": pdef.is_local,
                "configured": configured,
                "models": models_for_provider(pid) if configured else [],
            }
        )
    return out


def default_model_for_provider(provider_id: str) -> str:
    models = models_for_provider(provider_id)
    env_default = env_default_model(provider_id)
    if models:
        return pick_default_from_list(provider_id, models, env_default)
    if env_default:
        return env_default
    return DEFAULT_MODELS.get(provider_id, "")
