
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.conversations.schemas import (
    AgentMessageCreate,
    UpdateConversationStatus,
)


def list_conversations(
    db: Session,
    organization_id: int,
    status_filter: models.ConversationStatus | None = None,
    chatbot_id: int | None = None,
) -> list[models.Conversation]:
    query = db.query(models.Conversation).filter(
        models.Conversation.organization_id == organization_id
    )
    if status_filter is not None:
        query = query.filter(
            models.Conversation.status == status_filter
        )
    if chatbot_id is not None:
        query = query.filter(
            models.Conversation.chatbot_id == chatbot_id
        )
    return query.order_by(models.Conversation.updated_at.desc()).all()


def get_conversation(
    db: Session, organization_id: int, conversation_id: int
) -> models.Conversation | None:
    return (
        db.query(models.Conversation)
        .filter(
            models.Conversation.id == conversation_id,
            models.Conversation.organization_id == organization_id,
        )
        .first()
    )


def get_conversation_or_404(
    db: Session, organization_id: int, conversation_id: int
) -> models.Conversation:
    conversation = get_conversation(db, organization_id, conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


def update_status(
    db: Session,
    conversation: models.Conversation,
    data: UpdateConversationStatus,
) -> models.Conversation:
    conversation.status = data.status
    db.commit()
    db.refresh(conversation)
    return conversation


def assign_agent(
    db: Session,
    organization_id: int,
    conversation: models.Conversation,
    actor: models.User,
    agent_id: int | None,
) -> models.Conversation:
    target_id = agent_id if agent_id is not None else actor.id

    # The assignee must be a member of this organization.
    is_member = (
        db.query(models.OrganizationMembership)
        .filter(
            models.OrganizationMembership.user_id == target_id,
            models.OrganizationMembership.organization_id
            == organization_id,
        )
        .first()
    )
    if is_member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent is not a member of this organization",
        )

    conversation.assigned_agent_id = target_id
    if conversation.status in (
        models.ConversationStatus.ACTIVE,
        models.ConversationStatus.WAITING_HUMAN,
    ):
        conversation.status = models.ConversationStatus.HUMAN
    db.commit()
    db.refresh(conversation)
    return conversation


def agent_reply(
    db: Session,
    conversation: models.Conversation,
    actor: models.User,
    data: AgentMessageCreate,
) -> models.Message:
    message = models.Message(
        conversation_id=conversation.id,
        sender_type=models.SenderType.AGENT,
        content=data.content,
        is_internal=data.is_internal,
        metadata_={"agent_id": actor.id},
    )
    db.add(message)

    # A visible agent reply moves the conversation into human care.
    if not data.is_internal and conversation.status in (
        models.ConversationStatus.ACTIVE,
        models.ConversationStatus.WAITING_HUMAN,
    ):
        conversation.status = models.ConversationStatus.HUMAN
        if conversation.assigned_agent_id is None:
            conversation.assigned_agent_id = actor.id

    db.commit()
    db.refresh(message)
    return message


def request_human(
    db: Session, conversation: models.Conversation
) -> models.Conversation:
    """Customer-facing handoff: flag the conversation for agents."""
    if conversation.status == models.ConversationStatus.ACTIVE:
        conversation.status = models.ConversationStatus.WAITING_HUMAN

    db.add(
        models.Message(
            conversation_id=conversation.id,
            sender_type=models.SenderType.SYSTEM,
            content="The customer requested to speak with a human agent.",
        )
    )
    db.commit()
    db.refresh(conversation)
    return conversation
