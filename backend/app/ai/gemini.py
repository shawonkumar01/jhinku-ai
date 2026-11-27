
"""Google Gemini provider — free tier via Google AI Studio.

Docs: https://ai.google.dev/gemini-api/docs
Get a free key at https://aistudio.google.com/apikey
"""

import logging

from app.core.config import (
    EMBEDDING_DIMENSIONS,
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    GEMINI_LLM_MODEL,
)

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            return None
        from google import genai

        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def embeddings_available() -> bool:
    return bool(GEMINI_API_KEY)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts with gemini-embedding-001."""
    client = _get_client()
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    response = client.models.embed_content(
        model=GEMINI_EMBEDDING_MODEL,
        contents=texts,
        config={"output_dimensionality": EMBEDDING_DIMENSIONS},
    )
    # Order matches the input order.
    return [embedding.values for embedding in response.embeddings]


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]


def generate_answer(messages: list[dict[str, str]]) -> str:
    """Generate a chat answer. messages uses OpenAI-style roles;
    'system' becomes Gemini's system_instruction."""
    client = _get_client()
    if client is None:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    system_instruction = None
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            system_instruction = msg["content"]
        else:
            # Map OpenAI roles to Gemini roles (user/model).
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                {"role": role, "parts": [{"text": msg["content"]}]}
            )

    response = client.models.generate_content(
        model=GEMINI_LLM_MODEL,
        contents=contents,
        config={
            "system_instruction": system_instruction,
            "temperature": 0.3,
        },
    )
    return response.text or ""
