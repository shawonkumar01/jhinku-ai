
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app import models


def get_organization_membership(
    organization_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.OrganizationMembership:
    """Verify the current user belongs to the organization.

    Returns 404 (not 403) for non-members so the existence of
    other organizations is not revealed.
    """
    membership = (
        db.query(models.OrganizationMembership)
        .filter(
            models.OrganizationMembership.user_id == current_user.id,
            models.OrganizationMembership.organization_id
            == organization_id,
        )
        .first()
    )

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return membership


def require_min_role(min_role: models.MemberRole):
    """Dependency factory: membership + minimum role check."""

    def dependency(
        membership: models.OrganizationMembership = Depends(
            get_organization_membership
        ),
    ) -> models.OrganizationMembership:
        actor_role = models.ROLE_ORDER[membership.role]
        required = models.ROLE_ORDER[min_role]

        if actor_role < required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action",
            )

        return membership

    return dependency
