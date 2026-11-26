
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.memberships.schemas import (
    AddMemberRequest,
    UpdateMemberRoleRequest,
)


def _get_membership_or_404(
    db: Session, organization_id: int, membership_id: int
) -> models.OrganizationMembership:
    membership = (
        db.query(models.OrganizationMembership)
        .filter(
            models.OrganizationMembership.id == membership_id,
            models.OrganizationMembership.organization_id
            == organization_id,
        )
        .first()
    )
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this organization",
        )
    return membership


def _check_can_manage(
    actor: models.OrganizationMembership,
    target: models.OrganizationMembership,
) -> None:
    """Actor must outrank the target's role, except owners can
    manage anyone. Nobody can modify another owner unless they
    are an owner themselves."""
    if target.role == models.MemberRole.OWNER:
        if actor.role != models.MemberRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an owner can modify an owner",
            )
        return

    if models.ROLE_ORDER[actor.role] <= models.ROLE_ORDER[target.role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot modify a member with an equal or "
            "higher role",
        )


def _check_not_last_owner(
    db: Session, organization_id: int, target: models.OrganizationMembership
) -> None:
    if target.role != models.MemberRole.OWNER:
        return

    owner_count = (
        db.query(models.OrganizationMembership)
        .filter(
            models.OrganizationMembership.organization_id
            == organization_id,
            models.OrganizationMembership.role
            == models.MemberRole.OWNER,
        )
        .count()
    )
    if owner_count <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organization must keep at least one owner",
        )


def list_members(
    db: Session, organization_id: int
) -> list[models.OrganizationMembership]:
    return (
        db.query(models.OrganizationMembership)
        .filter(
            models.OrganizationMembership.organization_id
            == organization_id
        )
        .order_by(models.OrganizationMembership.id)
        .all()
    )


def add_member(
    db: Session,
    organization_id: int,
    data: AddMemberRequest,
) -> models.OrganizationMembership:
    if data.role == models.MemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ownership cannot be granted through member invites",
        )

    user = (
        db.query(models.User)
        .filter(models.User.email == data.email.lower())
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered user with this email. "
            "The user must register first.",
        )

    existing = (
        db.query(models.OrganizationMembership)
        .filter(
            models.OrganizationMembership.user_id == user.id,
            models.OrganizationMembership.organization_id
            == organization_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this organization",
        )

    membership = models.OrganizationMembership(
        user_id=user.id,
        organization_id=organization_id,
        role=data.role,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def update_member_role(
    db: Session,
    organization_id: int,
    membership_id: int,
    actor: models.OrganizationMembership,
    data: UpdateMemberRoleRequest,
) -> models.OrganizationMembership:
    target = _get_membership_or_404(db, organization_id, membership_id)
    _check_can_manage(actor, target)

    if data.role == models.MemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ownership transfer is not supported yet",
        )

    _check_not_last_owner(db, organization_id, target)

    target.role = data.role
    db.commit()
    db.refresh(target)
    return target


def remove_member(
    db: Session,
    organization_id: int,
    membership_id: int,
    actor: models.OrganizationMembership,
) -> None:
    target = _get_membership_or_404(db, organization_id, membership_id)
    _check_can_manage(actor, target)
    _check_not_last_owner(db, organization_id, target)

    db.delete(target)
    db.commit()
