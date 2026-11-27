
"""OpenAI provider — embeddings + chat completions.

The API key never leaves the backend.
"""

from app.core.config import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL,
    LLM_MODEL,
    OPENAI_API_KEY,
)

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
    client = _get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")

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


def generate_answer(messages: list[dict[str, str]]) -> str:
    client = _get_client()
    if client is None:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content or ""
