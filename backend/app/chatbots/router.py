
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.chatbots import service
from app.chatbots.schemas import (
    ChatbotCreate,
    ChatbotResponse,
    ChatbotUpdate,
)
from app.database import get_db
from app.memberships.dependencies import get_organization_membership

router = APIRouter(
    prefix="/organizations/{organization_id}/chatbots",
    tags=["chatbots"],
)


@router.get("", response_model=list[ChatbotResponse])
def list_chatbots(
    organization_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    return service.list_chatbots(db, organization_id)


@router.post(
    "",
    response_model=ChatbotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_chatbot(
    organization_id: int,
    data: ChatbotCreate,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    return service.create_chatbot(db, organization_id, data)


@router.get("/{chatbot_id}", response_model=ChatbotResponse)
def get_chatbot(
    organization_id: int,
    chatbot_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    chatbot = service.get_chatbot(db, organization_id, chatbot_id)
    if chatbot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found",
        )
    return chatbot


@router.patch("/{chatbot_id}", response_model=ChatbotResponse)
def update_chatbot(
    organization_id: int,
    chatbot_id: int,
    data: ChatbotUpdate,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    chatbot = service.update_chatbot(
        db, organization_id, chatbot_id, data
    )
    if chatbot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found",
        )
    return chatbot


@router.delete(
    "/{chatbot_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_chatbot(
    organization_id: int,
    chatbot_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    if not service.delete_chatbot(db, organization_id, chatbot_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chatbot not found",
        )
