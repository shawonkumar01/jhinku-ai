
from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)


class OrganizationResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class MyOrganizationResponse(BaseModel):
    id: int
    name: str
    role: str

    model_config = ConfigDict(from_attributes=True)
