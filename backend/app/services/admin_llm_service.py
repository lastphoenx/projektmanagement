"""Admin: LLM-Infrastruktur-Status (ohne Credentials/URLs in der Antwort)."""

from sqlalchemy.orm import Session

from app import config
from app.core.crypto.classification import DataClassification
from app.core.llm import generate_text
from app.core.llm.errors import LLMError
from app.core.llm.types import LlmRequest, LlmRuntimeConfig
from app.models import User
from app.services.llm_provider_service import (
    env_api_key,
    list_providers_for_ui,
    models_for_provider,
    provider_is_configured,
    resolve_base_url,
)


def get_admin_llm_state(db: Session, user: User) -> dict:
    del user
    providers = list_providers_for_ui()
    default_provider = config.settings.llm_provider or "ollama"
    default_model = config.settings.llm_model or ""
    if not default_model:
        models = models_for_provider(default_provider)
        default_model = models[0] if models else ""

    return {
        "providers": providers,
        "env_defaults": {
            "provider": default_provider,
            "model": default_model,
        },
        "note": "Benutzer wählen Provider/Modell unter Einstellungen → KI. API-Keys und Ollama-URL nur in .env.",
    }


def test_admin_llm_connection(
    db: Session,
    user: User,
    *,
    provider: str,
    model: str,
) -> dict:
    del db, user
    from app.core.llm.provider_catalog import PROVIDERS

    pdef = PROVIDERS.get(provider)
    if not pdef:
        raise LLMError("Unbekannter Provider", "invalid_provider")
    if not provider_is_configured(provider):
        raise LLMError("Provider ist nicht konfiguriert (.env prüfen)", "not_configured")

    if pdef.is_local:
        models = models_for_provider(provider)
        return {"ok": True, "message": f"Ollama erreichbar — {len(models)} Modell(e)", "models": models}

    if provider not in ("openai",):
        return {"ok": False, "message": "Verbindungstest für diesen Provider noch nicht implementiert"}

    runtime = LlmRuntimeConfig(
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
    return {"ok": True, "message": f"Antwort: {reply[:80]}"}
