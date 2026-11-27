
"""LLM provider dispatcher (chat completions)."""

from app.core.config import AI_PROVIDER
from app.ai import gemini, openai_provider


def generate_answer(messages: list[dict[str, str]]) -> str:
    if AI_PROVIDER == "gemini":
        return gemini.generate_answer(messages)
    return openai_provider.generate_answer(messages)
