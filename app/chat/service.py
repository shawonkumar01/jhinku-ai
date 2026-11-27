
import secrets
from urllib.parse import urlparse

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app import models
from app.ai import rag


def get_active_chatbot_by_widget_id(
    db: Session, public_widget_id: str
) -> models.Chatbot:
    chatbot = (
        db.query(models.Chatbot)
        .filter(models.Chatbot.public_widget_id == public_widget_id)
        .first()
    )
    if chatbot is None or not chatbot.is_active:
        # Same 404 for missing and inactive — don't reveal which.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found",
        )
    return chatbot


def validate_origin(chatbot: models.Chatbot, request: Request) -> None:
    """Enforce the chatbot's allowed_domains against the request's
    Origin (or Referer) header. Empty list = any domain allowed."""
    allowed = chatbot.allowed_domains or []
    if not allowed:
        return

    origin = request.headers.get("origin") or request.headers.get(
        "referer"
    )
    host = urlparse(origin).hostname if origin else None

    if host is None or not any(
        host == domain or host.endswith(f".{domain}")
        for domain in allowed
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This chatbot is not allowed to run on this domain",
        )


def to_message_response(message: models.Message):
    from app.chat.schemas import MessageResponse

    return MessageResponse(
        id=message.id,
        sender_type=message.sender_type.value,
        content=message.content,
        metadata=message.metadata_,
        created_at=message.created_at,
    )


def create_conversation(
    db: Session, chatbot: models.Chatbot, customer_identifier: str
) -> models.Conversation:
    conversation = models.Conversation(
        public_id=secrets.token_urlsafe(16),
        organization_id=chatbot.organization_id,
        chatbot_id=chatbot.id,
        customer_identifier=customer_identifier,
        status=models.ConversationStatus.ACTIVE,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_conversation_or_404(
    db: Session, public_id: str, customer_identifier: str
) -> models.Conversation:
    conversation = (
        db.query(models.Conversation)
        .filter(models.Conversation.public_id == public_id)
        .first()
    )
    # Require the customer identifier too — public_id alone is not
    # enough to read someone else's conversation.
    if (
        conversation is None
        or conversation.customer_identifier != customer_identifier
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


def send_message(
    db: Session, conversation: models.Conversation, content: str
) -> models.Message:
    """Store the customer message, generate an AI reply, store it."""
    customer_msg = models.Message(
        conversation_id=conversation.id,
        sender_type=models.SenderType.CUSTOMER,
        content=content,
    )
    db.add(customer_msg)
    db.commit()

    result = rag.answer_question(
        db, conversation.chatbot, content
    )

    ai_msg = models.Message(
        conversation_id=conversation.id,
        sender_type=models.SenderType.AI,
        content=result.answer,
        metadata_={
            "sources": result.sources,
            "used_fallback": result.used_fallback,
        },
    )
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    return ai_msg


def list_messages(
    db: Session, conversation: models.Conversation
) -> list[models.Message]:
    return (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation.id)
        .order_by(models.Message.id)
        .all()
    )
