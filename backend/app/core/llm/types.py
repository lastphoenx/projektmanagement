from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LlmRequest:
    system_prompt: str
    user_prompt: str
    model: str
    temperature: float = 0.4
    max_tokens: int = 4096


@dataclass(frozen=True, slots=True)
class LlmRuntimeConfig:
    provider: str  # openai | local
    base_url: str | None
    api_key: str | None
    model: str
    is_local: bool
