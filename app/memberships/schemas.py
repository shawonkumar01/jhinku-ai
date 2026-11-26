
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models import MemberRole


class AddMemberRequest(BaseModel):
    email: EmailStr
    role: MemberRole = MemberRole.MEMBER


class UpdateMemberRoleRequest(BaseModel):
    role: MemberRole


class MemberResponse(BaseModel):
    id: int
    user_id: int
    email: str
    full_name: str | None
    role: MemberRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
