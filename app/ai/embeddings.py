
"""Thin wrapper around the OpenAI embeddings API.

The API key never leaves the backend. If no key is configured,
embeddings are unavailable and callers should degrade gracefully.
"""

import logging

from app.core.config import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    OPENAI_API_KEY,
)

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        if not OPENAI_API_KEY:
            return None
        from openai import OpenAI

        _client = OpenAI(api_key=OPENAI_API_KEY)
    return _client


def embeddings_available() -> bool:
    return bool(OPENAI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return one embedding vector per input text."""
    client = _get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    # The embeddings API accepts batches; chunk into safe sizes.
    results: list[list[float]] = []
    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
            dimensions=EMBEDDING_DIMENSIONS,
        )
        results.extend(item.embedding for item in response.data)
    return results


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
