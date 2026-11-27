
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ConversationStatus, SenderType


class ConversationListItem(BaseModel):
    id: int
    public_id: str
    customer_identifier: str
    status: ConversationStatus
    chatbot_id: int
    assigned_agent_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentMessageResponse(BaseModel):
    id: int
    sender_type: SenderType
    content: str
    is_internal: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationDetail(ConversationListItem):
    messages: list[AgentMessageResponse] = []


class AgentMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    is_internal: bool = False


class UpdateConversationStatus(BaseModel):
    status: ConversationStatus


class AssignAgentRequest(BaseModel):
    # None = assign to the current user.
    agent_id: int | None = None
