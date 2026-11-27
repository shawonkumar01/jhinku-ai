
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import models
from app.chat import service
from app.chat.schemas import (
    ConversationResponse,
    CreateConversationRequest,
    HandoffRequest,
    HandoffResponse,
    MessageResponse,
    PublicChatbotResponse,
    SendMessageRequest,
)
from app.conversations import service as conv_service
from app.core.ratelimit import rate_limit
from app.database import get_db

router = APIRouter(prefix="/public", tags=["public-chat"])


def _rate_limit_dep(request: Request):
    rate_limit(request)


@router.get(
    "/chatbots/{public_widget_id}",
    response_model=PublicChatbotResponse,
    dependencies=[Depends(_rate_limit_dep)],
)
def get_public_chatbot(
    public_widget_id: str,
    request: Request,
    db: Session = Depends(get_db),
):
    chatbot = service.get_active_chatbot_by_widget_id(
        db, public_widget_id
    )
    service.validate_origin(chatbot, request)
    return chatbot


@router.post(
    "/chatbots/{public_widget_id}/conversations",
    response_model=ConversationResponse,
    status_code=201,
    dependencies=[Depends(_rate_limit_dep)],
)
def create_conversation(
    public_widget_id: str,
    data: CreateConversationRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    chatbot = service.get_active_chatbot_by_widget_id(
        db, public_widget_id
    )
    service.validate_origin(chatbot, request)

    conversation = service.create_conversation(
        db, chatbot, data.customer_identifier
    )
    return ConversationResponse(
        public_id=conversation.public_id,
        welcome_message=chatbot.welcome_message,
    )


@router.post(
    "/conversations/{public_id}/messages",
    response_model=MessageResponse,
    dependencies=[Depends(_rate_limit_dep)],
)
def send_message(
    public_id: str,
    data: SendMessageRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    conversation = service.get_conversation_or_404(
        db, public_id, data.customer_identifier
    )
    service.validate_origin(conversation.chatbot, request)

    if conversation.status == models.ConversationStatus.CLOSED:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This conversation is closed",
        )

    ai_message = service.send_message(db, conversation, data.content)
    return service.to_message_response(ai_message)


@router.post(
    "/conversations/{public_id}/handoff",
    response_model=HandoffResponse,
    dependencies=[Depends(_rate_limit_dep)],
)
def request_human(
    public_id: str,
    data: HandoffRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Customer asks for a human agent."""
    conversation = service.get_conversation_or_404(
        db, public_id, data.customer_identifier
    )
    service.validate_origin(conversation.chatbot, request)

    conv_service.request_human(db, conversation)
    return HandoffResponse(
        status=conversation.status.value,
        message="A human agent has been notified.",
    )


@router.get(
    "/conversations/{public_id}/messages",
    response_model=list[MessageResponse],
    dependencies=[Depends(_rate_limit_dep)],
)
def get_messages(
    public_id: str,
    request: Request,
    customer_identifier: str,
    db: Session = Depends(get_db),
):
    conversation = service.get_conversation_or_404(
        db, public_id, customer_identifier
    )
    service.validate_origin(conversation.chatbot, request)

    return [
        service.to_message_response(m)
        for m in service.list_messages(db, conversation)
    ]
