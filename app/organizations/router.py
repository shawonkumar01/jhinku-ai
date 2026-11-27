
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.memberships.dependencies import get_organization_membership
from app.organizations import service
from app.organizations.schemas import (
    MyOrganizationResponse,
    OrganizationCreate,
    OrganizationResponse,
)

router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_organization(
    data: OrganizationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return service.create_organization(db, data, current_user)


@router.get("", response_model=list[MyOrganizationResponse])
def get_organizations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return service.list_my_organizations(db, current_user)


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    organization = service.get_organization(db, organization_id)
    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )
    return organization
