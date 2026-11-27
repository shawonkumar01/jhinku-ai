
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.knowledge import service
from app.knowledge.schemas import KnowledgeSourceResponse
from app.memberships.dependencies import get_organization_membership

router = APIRouter(
    prefix="/organizations/{organization_id}/knowledge-sources",
    tags=["knowledge"],
)


@router.post(
    "",
    response_model=KnowledgeSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_source(
    organization_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    chatbot_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    source = service.create_source(
        db, organization_id, file, title, chatbot_id
    )
    # Process extraction/chunking after the response is sent.
    # Later this becomes a Celery/Redis task with the same signature.
    background_tasks.add_task(service.process_source, source.id)
    return source


@router.get("", response_model=list[KnowledgeSourceResponse])
def list_sources(
    organization_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    return service.list_sources(db, organization_id)


@router.get("/{source_id}", response_model=KnowledgeSourceResponse)
def get_source(
    organization_id: int,
    source_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    source = service.get_source(db, organization_id, source_id)
    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge source not found",
        )
    return source


@router.delete(
    "/{source_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_source(
    organization_id: int,
    source_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    if not service.delete_source(db, organization_id, source_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge source not found",
        )
