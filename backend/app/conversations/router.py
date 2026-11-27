
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import models
from app.auth.dependencies import get_current_user
from app.conversations import service
from app.conversations.schemas import (
    AgentMessageCreate,
    AgentMessageResponse,
    AssignAgentRequest,
    ConversationDetail,
    ConversationListItem,
    UpdateConversationStatus,
)
from app.database import get_db
from app.memberships.dependencies import (
    get_organization_membership,
    require_min_role,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/conversations",
    tags=["conversations"],
)

# Any org member can view the inbox; agents+ can act on it.
_VIEW = get_organization_membership
_AGENT = require_min_role(models.MemberRole.AGENT)


@router.get("", response_model=list[ConversationListItem])
def list_conversations(
    organization_id: int,
    status_filter: models.ConversationStatus | None = Query(
        default=None, alias="status"
    ),
    chatbot_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(_VIEW),
):
    return service.list_conversations(
        db, organization_id, status_filter, chatbot_id
    )


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    organization_id: int,
    conversation_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(_VIEW),
):
    conversation = service.get_conversation_or_404(
        db, organization_id, conversation_id
    )
    detail = ConversationDetail.model_validate(conversation)
    # Internal notes are included here — this is the agent view.
    detail.messages = [
        AgentMessageResponse.model_validate(m)
        for m in conversation.messages
    ]
    return detail


@router.patch("/{conversation_id}", response_model=ConversationListItem)
def update_status(
    organization_id: int,
    conversation_id: int,
    data: UpdateConversationStatus,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(_AGENT),
):
    conversation = service.get_conversation_or_404(
        db, organization_id, conversation_id
    )
    return service.update_status(db, conversation, data)


@router.post(
    "/{conversation_id}/assign",
    response_model=ConversationListItem,
)
def assign_agent(
    organization_id: int,
    conversation_id: int,
    data: AssignAgentRequest,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(_AGENT),
    current_user: models.User = Depends(get_current_user),
):
    conversation = service.get_conversation_or_404(
        db, organization_id, conversation_id
    )
    return service.assign_agent(
        db, organization_id, conversation, current_user, data.agent_id
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=AgentMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def agent_reply(
    organization_id: int,
    conversation_id: int,
    data: AgentMessageCreate,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(_AGENT),
    current_user: models.User = Depends(get_current_user),
):
    conversation = service.get_conversation_or_404(
        db, organization_id, conversation_id
    )
    message = service.agent_reply(db, conversation, current_user, data)
    return AgentMessageResponse.model_validate(message)
