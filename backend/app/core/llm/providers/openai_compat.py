"""OpenAI-kompatibler Chat-Adapter (OpenAI, Ollama, lokale Proxies)."""

from openai import OpenAI

from app.core.llm.errors import LLMError
from app.core.llm.types import LlmRequest, LlmRuntimeConfig


def generate(config: LlmRuntimeConfig, request: LlmRequest) -> str:
    if not config.api_key and not config.is_local:
        raise LLMError("LLM API-Key fehlt", "missing_api_key")

    base_url = config.base_url or "https://api.openai.com/v1"
    client = OpenAI(api_key=config.api_key or "not-needed", base_url=base_url)

    try:
        response = client.chat.completions.create(
            model=request.model or config.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            messages=[
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        )
    except Exception as exc:
        raise LLMError(f"LLM-Aufruf fehlgeschlagen: {exc}", "provider_error") from exc

    content = response.choices[0].message.content
    if not content:
        raise LLMError("Leere LLM-Antwort", "empty_response")
    return content.strip()
