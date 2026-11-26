
from pydantic import BaseModel, ConfigDict, Field


class FAQCreate(BaseModel):
    question: str = Field(min_length=5, max_length=200)
    answer: str = Field(min_length=10, max_length=1000)


class FAQUpdate(BaseModel):
    question: str = Field(min_length=5, max_length=200)
    answer: str = Field(min_length=10, max_length=1000)


class FAQPatch(BaseModel):
    question: str | None = Field(
        default=None,
        min_length=5,
        max_length=200
    )
    answer: str | None = Field(
        default=None,
        min_length=10,
        max_length=1000
    )


class FAQResponse(BaseModel):
    id: int
    question: str
    answer: str

    model_config = ConfigDict(from_attributes=True)


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)


class OrganizationResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)

