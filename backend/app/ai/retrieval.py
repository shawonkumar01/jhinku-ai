
"""Tenant-scoped vector similarity search using pgvector."""

from sqlalchemy.orm import Session

from app import models
from app.core.config import RAG_TOP_K


def search_chunks(
    db: Session,
    organization_id: int,
    query_embedding: list[float],
    chatbot_id: int | None = None,
    top_k: int = RAG_TOP_K,
) -> list[tuple[models.KnowledgeChunk, float]]:
    """Return the most similar chunks with their cosine distance.

    CRITICAL: every query is filtered by organization_id (and chatbot
    scope when given) so one tenant can never retrieve another
    tenant's knowledge.
    """
    query = (
        db.query(
            models.KnowledgeChunk,
            models.KnowledgeChunk.embedding.cosine_distance(
                query_embedding
            ).label("distance"),
        )
        .filter(
            models.KnowledgeChunk.organization_id == organization_id,
            models.KnowledgeChunk.embedding.isnot(None),
        )
    )

    if chatbot_id is not None:
        # Chatbot-scoped sources plus org-wide sources (chatbot_id NULL)
        # — but NEVER another chatbot's private sources... actually a
        # source scoped to chatbot A must not leak to chatbot B, so we
        # include only NULL or this chatbot's sources.
        from sqlalchemy import or_

        query = query.filter(
            or_(
                models.KnowledgeChunk.chatbot_id == chatbot_id,
                models.KnowledgeChunk.chatbot_id.is_(None),
            )
        )
    else:
        # Org-wide retrieval: exclude chatbot-private chunks.
        query = query.filter(models.KnowledgeChunk.chatbot_id.is_(None))

    results = (
        query.order_by("distance")
        .limit(top_k)
        .all()
    )
    return [(chunk, float(distance)) for chunk, distance in results]
