"""Kuratierte Modelllisten und Ollama-Filter für Planungs-KI (Chat/Markdown)."""

from __future__ import annotations

import re

# Nur Chat-/Instruct-Modelle — keine Embeddings, Vision, Reranker, Klassifikatoren
OLLAMA_EXCLUDE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"(^|[-_/])embed",
        r"bge-",
        r"nomic-embed",
        r"mxbai-embed",
        r"paraphrase",
        r"rerank",
        r"doctype-classifier",
        r"classifier",
        r"[-:]vl",
        r"vision",
        r"mmproj",
        r"codellama",
        r"(-coder|:coder)",
        r"coder-next",
    )
)

# Bevorzugte Reihenfolge in der UI (erstes vorhandenes = Default ohne .env)
OLLAMA_PREFERRED_ORDER: tuple[str, ...] = (
    "llama3.3:70b",
    "llama3.3",
    "llama3:latest",
    "llama3:8b",
    "llama3.2",
    "qwen3:32b",
    "qwen3:8b",
    "qwen2.5:32b",
    "qwen2.5:7b-instruct",
    "qwen2.5:7b",
    "gpt-oss",
    "mistral",
    "mixtral",
)

STATIC_MODELS: dict[str, list[str]] = {
    # gpt-4o-mini: schnell/günstig; gpt-4o: Qualität; gpt-4.1-mini: neuerer Kompakt-Typ
    "openai": ["gpt-4o-mini", "gpt-4.1-mini", "gpt-4o"],
    # Haiku: Entwürfe; Sonnet 3.5/4: lange Planungstexte
    "anthropic": [
        "claude-3-5-haiku-latest",
        "claude-3-5-sonnet-latest",
        "claude-sonnet-4-20250514",
    ],
    "ollama": [],
}

DEFAULT_MODELS: dict[str, str] = {
    "ollama": "llama3.3:70b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-haiku-latest",
}


def is_ollama_planning_model(name: str) -> bool:
    return not any(pattern.search(name) for pattern in OLLAMA_EXCLUDE_PATTERNS)


def filter_ollama_models(names: list[str]) -> list[str]:
    filtered = [n for n in names if is_ollama_planning_model(n)]
    return sort_ollama_models(filtered)


def sort_ollama_models(names: list[str]) -> list[str]:
    order_index = {pref: i for i, pref in enumerate(OLLAMA_PREFERRED_ORDER)}

    def sort_key(name: str) -> tuple[int, int, str]:
        lower = name.lower()
        for pref, idx in order_index.items():
            if lower == pref.lower() or lower.startswith(pref.lower()):
                return (0, idx, name)
        return (1, 999, name)

    return sorted(names, key=sort_key)


def pick_default_from_list(provider_id: str, models: list[str], env_default: str) -> str:
    if env_default and env_default in models:
        return env_default
    for candidate in STATIC_MODELS.get(provider_id, []):
        if candidate in models:
            return candidate
    for candidate in OLLAMA_PREFERRED_ORDER if provider_id == "ollama" else ():
        for model in models:
            if model.lower().startswith(candidate.lower()):
                return model
    if models:
        return models[0]
    return DEFAULT_MODELS.get(provider_id, "")
