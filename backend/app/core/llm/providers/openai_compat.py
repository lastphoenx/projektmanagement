"""OpenAI-kompatibler Chat-Adapter (OpenAI, Ollama, Anthropic)."""

from openai import OpenAI

from app.core.llm.errors import LLMError
from app.core.llm.types import LlmRequest, LlmResult, LlmRuntimeConfig


def generate(config: LlmRuntimeConfig, request: LlmRequest) -> LlmResult:
    if not config.api_key and not config.is_local:
        raise LLMError("LLM API-Key fehlt", "missing_api_key")

    base_url = config.base_url or "https://api.openai.com/v1"
    client_kwargs: dict = {
        "api_key": config.api_key or "not-needed",
        "base_url": base_url,
    }
    if config.extra_headers:
        client_kwargs["default_headers"] = dict(config.extra_headers)
    client = OpenAI(**client_kwargs)

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
        msg = str(exc)
        if config.provider == "anthropic" and "anthropic-workspace-id" in msg:
            raise LLMError(
                "Anthropic identity-linked API-Key: ANTHROPIC_WORKSPACE_ID in .env setzen "
                "(wrkspc_… — Claude Console → Settings → Workspaces, Spalte ID). "
                f"Original: {msg}",
                "missing_workspace_id",
            ) from exc
        raise LLMError(f"LLM-Aufruf fehlgeschlagen: {exc}", "provider_error") from exc

    content = response.choices[0].message.content
    if not content:
        raise LLMError("Leere LLM-Antwort", "empty_response")

    usage = response.usage
    return LlmResult(
        text=content.strip(),
        input_tokens=usage.prompt_tokens if usage else None,
        output_tokens=usage.completion_tokens if usage else None,
    )
