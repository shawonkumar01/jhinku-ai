
"""Embedding provider dispatcher.

Selects OpenAI or Gemini based on AI_PROVIDER in config. The API
key never leaves the backend. If no key is configured, embeddings
are unavailable and callers degrade gracefully.
"""

import logging

from app.core.config import AI_PROVIDER
from app.ai import gemini

logger = logging.getLogger(__name__)


def _openai():
    from app.ai import openai_provider

    return openai_provider


def _provider():
    if AI_PROVIDER == "gemini":
        return gemini
    return _openai()


def embeddings_available() -> bool:
    try:
        return _provider().embeddings_available()
    except Exception:
        return False


def embed_texts(texts: list[str]) -> list[list[float]]:
    return _provider().embed_texts(texts)


def embed_query(text: str) -> list[float]:
    return _provider().embed_query(text)
