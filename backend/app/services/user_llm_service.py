"""Benutzer-KI-Einstellungen — Provider/Modell pro User, Credentials nur .env."""

from sqlalchemy.orm import Session

from app import config
from app.core.crypto.classification import DataClassification
from app.core.llm import generate_text
from app.core.llm.errors import LLMError
from app.core.llm.guidance import GUIDANCE
from app.core.llm.token_cost import BILLING_NOTE, TYPICAL_PLANNING_TOKENS, pricing_catalog_for_ui
from app.core.llm.types import LlmRequest, LlmRuntimeConfig
from app.models import User, UserLlmPreference
from app.services.llm_provider_service import (
    default_model_for_provider,
    env_api_key,
    list_providers_for_ui,
    make_runtime_config,
    models_for_provider,
    provider_is_configured,
    resolve_base_url,
)


def _active_preference(db: Session, user: User) -> UserLlmPreference | None:
    return db.query(UserLlmPreference).filter(UserLlmPreference.user_id == user.id).first()


def _fallback_provider_model() -> tuple[str, str]:
    provider = config.settings.llm_provider or "ollama"
    model = config.settings.llm_model or default_model_for_provider(provider)
    return provider, model


def get_user_llm_state(db: Session, user: User) -> dict:
    pref = _active_preference(db, user)
    if pref:
        provider, model, source = pref.provider, pref.model, "user"
    else:
        provider, model = _fallback_provider_model()
        source = "env"

    if not provider_is_configured(provider):
        for p in list_providers_for_ui():
            if p["configured"]:
                provider = p["id"]
                model = default_model_for_provider(provider)
                source = "auto"
                break

    models = models_for_provider(provider)
    if model not in models and models:
        model = models[0]

    return {
        "providers": list_providers_for_ui(),
        "active": {"provider": provider, "model": model, "source": source},
        "guidance": GUIDANCE,
        "billing_note": BILLING_NOTE,
        "pricing_catalog": pricing_catalog_for_ui(),
        "typical_planning_tokens": TYPICAL_PLANNING_TOKENS,
    }


def save_user_llm_preference(
    db: Session,
    user: User,
    *,
    provider: str,
    model: str,
) -> dict:
    from app.core.llm.provider_catalog import PROVIDERS

    if provider not in PROVIDERS:
        raise LLMError("Unbekannter Provider", "invalid_provider")
    if not provider_is_configured(provider):
        raise LLMError(
            f"Provider «{PROVIDERS[provider].label}» ist vom Betreiber nicht konfiguriert.",
            "not_configured",
        )
    models = models_for_provider(provider)
    if models and model not in models:
        raise LLMError("Modell für diesen Provider nicht verfügbar", "invalid_model")

    pref = _active_preference(db, user)
    if pref:
        pref.provider = provider
        pref.model = model
    else:
        db.add(UserLlmPreference(user_id=user.id, provider=provider, model=model))
    db.flush()
    return get_user_llm_state(db, user)


def build_runtime_config(db: Session, user: User) -> LlmRuntimeConfig:
    """Laufzeit-Konfiguration für generate_text — User-Wahl + .env-Credentials."""
    from app.core.llm.provider_catalog import PROVIDERS

    state = get_user_llm_state(db, user)
    provider = state["active"]["provider"]
    model = state["active"]["model"]
    pdef = PROVIDERS[provider]

    base = resolve_base_url(provider)
    api_key = env_api_key(provider) or config.settings.llm_api_key_fallback or None

    if not pdef.is_local and not api_key:
        raise LLMError(
            "Cloud-Provider nicht konfiguriert — Betreiber muss API-Key in .env setzen.",
            "not_configured",
        )
    if pdef.is_local and not base:
        raise LLMError(
            "Ollama nicht konfiguriert — Betreiber muss OLLAMA_BASE_URL in .env setzen.",
            "not_configured",
        )

    if pdef.is_local and base:
        base = f"{base.rstrip('/')}/v1"

    return make_runtime_config(
        provider=provider,
        base_url=base,
        api_key=api_key or "ollama",
        model=model,
        is_local=pdef.is_local,
    )


def test_user_llm_connection(db: Session, user: User, *, provider: str, model: str) -> dict:
    from app.core.llm.provider_catalog import PROVIDERS

    if provider not in PROVIDERS:
        raise LLMError("Unbekannter Provider", "invalid_provider")
    if not provider_is_configured(provider):
        raise LLMError("Provider ist nicht konfiguriert", "not_configured")

    pdef = PROVIDERS[provider]
    if pdef.is_local:
        models = models_for_provider(provider)
        return {"ok": True, "message": f"Ollama erreichbar — {len(models)} Modell(e)", "models": models}

    runtime = make_runtime_config(
        provider=provider,
        base_url=resolve_base_url(provider),
        api_key=env_api_key(provider),
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
    return {"ok": True, "message": f"Verbindung OK — Antwort: {reply.text[:80]}"}
