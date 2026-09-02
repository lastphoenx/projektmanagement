"""LLM-Zugriff — nur über dispatch, nie direkt aus services/."""

from app.core.llm.dispatch import generate_text
from app.core.llm.errors import LLMError
from app.core.llm.types import LlmResult

__all__ = ["LLMError", "LlmResult", "generate_text"]
