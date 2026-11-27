
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import ProcessingStatus


class KnowledgeSourceResponse(BaseModel):
    id: int
    organization_id: int
    chatbot_id: int | None
    title: str
    original_filename: str
    file_size: int
    content_type: str | None
    processing_status: ProcessingStatus
    chunk_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeChunkResponse(BaseModel):
    id: int
    chunk_index: int
    content: str

    model_config = ConfigDict(from_attributes=True)
