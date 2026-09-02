"""LLM-Provider-Katalog — statische Metadaten, keine SDK-Imports."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderDefinition:
    id: str
    label: str
    is_local: bool
    env_key_field: str | None  # Settings-Attribut für API-Key-Fallback
    default_base_url: str | None


PROVIDERS: dict[str, ProviderDefinition] = {
    "ollama": ProviderDefinition(
        id="ollama",
        label="Lokal (Ollama)",
        is_local=True,
        env_key_field=None,
        default_base_url=None,
    ),
    "openai": ProviderDefinition(
        id="openai",
        label="OpenAI",
        is_local=False,
        env_key_field="openai_api_key",
        default_base_url="https://api.openai.com/v1",
    ),
    "anthropic": ProviderDefinition(
        id="anthropic",
        label="Anthropic",
        is_local=False,
        env_key_field="anthropic_api_key",
        default_base_url="https://api.anthropic.com/v1",
    ),
}

STATIC_MODELS: dict[str, list[str]] = {
    "openai": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"],
    "anthropic": [
        "claude-3-5-haiku-latest",
        "claude-3-5-sonnet-latest",
        "claude-sonnet-4-20250514",
    ],
    "ollama": [],  # live von /api/tags, gefiltert in model_catalog
}

OPENAI_COMPAT_PROVIDERS = frozenset({"ollama", "openai", "anthropic"})
