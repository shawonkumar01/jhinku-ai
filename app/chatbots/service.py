
import secrets

from sqlalchemy.orm import Session

from app import models
from app.chatbots.schemas import ChatbotCreate, ChatbotUpdate


def _generate_widget_id(db: Session) -> str:
    """Generate a unique, unguessable public widget ID."""
    while True:
        widget_id = secrets.token_urlsafe(24)
        exists = (
            db.query(models.Chatbot)
            .filter(models.Chatbot.public_widget_id == widget_id)
            .first()
        )
        if exists is None:
            return widget_id


def list_chatbots(
    db: Session, organization_id: int
) -> list[models.Chatbot]:
    return (
        db.query(models.Chatbot)
        .filter(models.Chatbot.organization_id == organization_id)
        .order_by(models.Chatbot.id)
        .all()
    )


def get_chatbot(
    db: Session, organization_id: int, chatbot_id: int
) -> models.Chatbot | None:
    return (
        db.query(models.Chatbot)
        .filter(
            models.Chatbot.id == chatbot_id,
            models.Chatbot.organization_id == organization_id,
        )
        .first()
    )


def create_chatbot(
    db: Session, organization_id: int, data: ChatbotCreate
) -> models.Chatbot:
    chatbot = models.Chatbot(
        organization_id=organization_id,
        public_widget_id=_generate_widget_id(db),
        **data.model_dump(),
    )
    db.add(chatbot)
    db.commit()
    db.refresh(chatbot)
    return chatbot


def update_chatbot(
    db: Session,
    organization_id: int,
    chatbot_id: int,
    data: ChatbotUpdate,
) -> models.Chatbot | None:
    chatbot = get_chatbot(db, organization_id, chatbot_id)
    if chatbot is None:
        return None

    for field, value in data.model_dump(
        exclude_unset=True
    ).items():
        setattr(chatbot, field, value)

    db.commit()
    db.refresh(chatbot)
    return chatbot


def delete_chatbot(
    db: Session, organization_id: int, chatbot_id: int
) -> bool:
    chatbot = get_chatbot(db, organization_id, chatbot_id)
    if chatbot is None:
        return False

    db.delete(chatbot)
    db.commit()
    return True
