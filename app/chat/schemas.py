
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PublicChatbotResponse(BaseModel):
    """Safe public view of a chatbot — no org ids or internals."""

    name: str
    welcome_message: str | None
    branding: dict[str, Any] | None

    model_config = ConfigDict(from_attributes=True)


class CreateConversationRequest(BaseModel):
    customer_identifier: str = Field(min_length=1, max_length=255)


class ConversationResponse(BaseModel):
    public_id: str
    welcome_message: str | None


class HandoffRequest(BaseModel):
    customer_identifier: str = Field(min_length=1, max_length=255)


class HandoffResponse(BaseModel):
    status: str
    message: str


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    customer_identifier: str = Field(min_length=1, max_length=255)


class MessageResponse(BaseModel):
    id: int
    sender_type: str
    content: str
    metadata: dict[str, Any] | None = None
    created_at: datetime
