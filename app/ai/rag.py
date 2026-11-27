
"""Retrieval-Augmented Generation: answer questions using only the
organization's own knowledge base.

Flow: embed question -> tenant-scoped vector search -> build prompt
-> LLM -> answer + source references. Falls back honestly when the
retrieved context is insufficient.
"""

import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app import models
from app.ai import embeddings, llm, prompts, retrieval
from app.core.config import RAG_MAX_DISTANCE

logger = logging.getLogger(__name__)


@dataclass
class RagResult:
    answer: str
    sources: list[dict] = field(default_factory=list)
    used_fallback: bool = False


def _generate_answer(messages: list[dict[str, str]]) -> str:
    """Call the chat LLM via the configured provider."""
    if not embeddings.embeddings_available():
        raise RuntimeError("No AI API key configured")
    return llm.generate_answer(messages)


def answer_question(
    db: Session,
    chatbot: models.Chatbot,
    question: str,
) -> RagResult:
    """Answer a customer question grounded in org knowledge."""
    org_id = chatbot.organization_id

    # 1. Embed the question
    try:
        query_embedding = embeddings.embed_query(question)
    except Exception:
        logger.exception("Embedding failed for chatbot %s", chatbot.id)
        return RagResult(
            answer=prompts.FALLBACK_ANSWER, used_fallback=True
        )

    # 2. Tenant + chatbot scoped retrieval
    matches = retrieval.search_chunks(
        db,
        organization_id=org_id,
        query_embedding=query_embedding,
        chatbot_id=chatbot.id,
    )

    # 3. Guardrail: drop matches that are not similar enough
    relevant = [
        (chunk, dist) for chunk, dist in matches if dist <= RAG_MAX_DISTANCE
    ]

    if not relevant:
        return RagResult(
            answer=prompts.FALLBACK_ANSWER, used_fallback=True
        )

    contexts = [chunk.content for chunk, _ in relevant]
    sources = [
        {
            "knowledge_source_id": chunk.knowledge_source_id,
            "chunk_index": chunk.chunk_index,
            "title": chunk.source.title if chunk.source else None,
            "distance": round(dist, 4),
        }
        for chunk, dist in relevant
    ]

    # 4. Generate the answer
    messages = prompts.build_messages(
        question, contexts, chatbot.system_prompt
    )
    try:
        answer = _generate_answer(messages)
    except Exception:
        logger.exception("LLM generation failed")
        return RagResult(
            answer=prompts.FALLBACK_ANSWER,
            sources=sources,
            used_fallback=True,
        )

    return RagResult(answer=answer, sources=sources)
