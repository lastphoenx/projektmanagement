"""Ollama-Status — einziger Ort für HTTP zu Ollama (kein openai-SDK)."""

import httpx

from app.core.llm.errors import LLMError


def fetch_ollama_models(base_url: str, *, timeout: float = 10.0) -> list[str]:
    root = base_url.rstrip("/").removesuffix("/v1")
    try:
        response = httpx.get(f"{root}/api/tags", timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        raise LLMError(f"Ollama nicht erreichbar ({root}): {exc}", "provider_unreachable") from exc

    models: list[str] = []
    for item in data.get("models", []):
        name = item.get("name")
        if isinstance(name, str) and name.strip():
            models.append(name.strip())
    return sorted(models)


def ollama_reachable(base_url: str) -> bool:
    try:
        fetch_ollama_models(base_url, timeout=5.0)
        return True
    except LLMError:
        return False
