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
    provider: str
    base_url: str | None
    api_key: str | None
    model: str
    is_local: bool
    extra_headers: dict[str, str] | None = None


@dataclass(frozen=True, slots=True)
class LlmResult:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
