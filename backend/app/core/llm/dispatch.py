"""Zentraler LLM-Dispatch — PII-Gate vor externen Providern."""

from app.core.anonymization.pii_gate import PIIGateError, gate_text
from app.core.crypto.classification import DataClassification
from app.core.llm.errors import LLMError
from app.core.llm.providers import openai_compat
from app.core.llm.types import LlmRequest, LlmRuntimeConfig


def generate_text(
    config: LlmRuntimeConfig,
    request: LlmRequest,
    *,
    data_classification: DataClassification = DataClassification.CONFIDENTIAL,
) -> str:
    try:
        safe_system = gate_text(
            request.system_prompt,
            data_classification,
            provider_is_local=config.is_local,
        )
        safe_user = gate_text(
            request.user_prompt,
            data_classification,
            provider_is_local=config.is_local,
        )
    except PIIGateError as exc:
        raise LLMError(exc.message, "pii_blocked") from exc

    safe_request = LlmRequest(
        system_prompt=safe_system,
        user_prompt=safe_user,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    return openai_compat.generate(config, safe_request)
