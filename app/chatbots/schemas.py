
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatbotCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    welcome_message: str | None = Field(default=None, max_length=2000)
    system_prompt: str | None = Field(default=None, max_length=8000)
    is_active: bool = True
    branding: dict[str, Any] | None = None
    allowed_domains: list[str] | None = None


class ChatbotUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    welcome_message: str | None = Field(default=None, max_length=2000)
    system_prompt: str | None = Field(default=None, max_length=8000)
    is_active: bool | None = None
    branding: dict[str, Any] | None = None
    allowed_domains: list[str] | None = None


class ChatbotResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    public_widget_id: str
    welcome_message: str | None
    system_prompt: str | None
    is_active: bool
    branding: dict[str, Any] | None
    allowed_domains: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
