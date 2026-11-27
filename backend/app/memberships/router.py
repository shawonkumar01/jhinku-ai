
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.memberships import service
from app.memberships.dependencies import (
    get_organization_membership,
    require_min_role,
)
from app.memberships.schemas import (
    AddMemberRequest,
    MemberResponse,
    UpdateMemberRoleRequest,
)

router = APIRouter(
    prefix="/organizations/{organization_id}/members",
    tags=["members"],
)


@router.get("", response_model=list[MemberResponse])
def list_members(
    organization_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    return service.list_members(db, organization_id)


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    organization_id: int,
    data: AddMemberRequest,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        require_min_role(models.MemberRole.ADMIN)
    ),
):
    return service.add_member(db, organization_id, data)


@router.patch(
    "/{membership_id}", response_model=MemberResponse
)
def update_member_role(
    organization_id: int,
    membership_id: int,
    data: UpdateMemberRoleRequest,
    db: Session = Depends(get_db),
    actor: models.OrganizationMembership = Depends(
        require_min_role(models.MemberRole.ADMIN)
    ),
):
    return service.update_member_role(
        db, organization_id, membership_id, actor, data
    )


@router.delete(
    "/{membership_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_member(
    organization_id: int,
    membership_id: int,
    db: Session = Depends(get_db),
    actor: models.OrganizationMembership = Depends(
        require_min_role(models.MemberRole.ADMIN)
    ),
):
    service.remove_member(
        db, organization_id, membership_id, actor
    )
