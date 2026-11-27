
from sqlalchemy.orm import Session

from app import models
from app.organizations.schemas import (
    MyOrganizationResponse,
    OrganizationCreate,
)


def create_organization(
    db: Session, data: OrganizationCreate, user: models.User
) -> models.Organization:
    organization = models.Organization(name=data.name)
    db.add(organization)
    db.flush()

    # The creator automatically becomes the organization owner.
    db.add(
        models.OrganizationMembership(
            user_id=user.id,
            organization_id=organization.id,
            role=models.MemberRole.OWNER,
        )
    )

    db.commit()
    db.refresh(organization)
    return organization


def list_my_organizations(
    db: Session, user: models.User
) -> list[MyOrganizationResponse]:
    memberships = (
        db.query(models.OrganizationMembership)
        .filter(models.OrganizationMembership.user_id == user.id)
        .all()
    )

    return [
        MyOrganizationResponse(
            id=membership.organization.id,
            name=membership.organization.name,
            role=membership.role.value,
        )
        for membership in memberships
    ]


def get_organization(
    db: Session, organization_id: int
) -> models.Organization | None:
    return db.get(models.Organization, organization_id)
