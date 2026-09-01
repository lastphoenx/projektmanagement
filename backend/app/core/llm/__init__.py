"""LLM-Zugriff — nur über dispatch, nie direkt aus services/."""

from app.core.llm.dispatch import generate_text
from app.core.llm.errors import LLMError

__all__ = ["LLMError", "generate_text"]
