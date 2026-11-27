
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.database import get_db
from app.faqs import service
from app.faqs.schemas import (
    FAQCreate,
    FAQPatch,
    FAQResponse,
    FAQUpdate,
)
from app.memberships.dependencies import get_organization_membership

router = APIRouter(
    prefix="/organizations/{organization_id}/faqs",
    tags=["faqs"],
)


@router.post(
    "",
    response_model=FAQResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_faq(
    organization_id: int,
    data: FAQCreate,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    return service.create_faq(db, organization_id, data)


@router.get("")
def list_faqs(
    organization_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    organization = db.get(models.Organization, organization_id)
    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found",
        )
    faqs = service.list_faqs(db, organization_id)

    return {
        "organization_id": organization_id,
        "organization_name": organization.name,
        "total": len(faqs),
        "data": faqs,
    }


@router.get("/{faq_id}", response_model=FAQResponse)
def get_faq(
    organization_id: int,
    faq_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    faq = service.get_faq(db, organization_id, faq_id)
    if faq is None:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found in this organization",
        )
    return faq


@router.put("/{faq_id}", response_model=FAQResponse)
def update_faq(
    organization_id: int,
    faq_id: int,
    data: FAQUpdate,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    faq = service.update_faq(db, organization_id, faq_id, data)
    if faq is None:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found in this organization",
        )
    return faq


@router.patch("/{faq_id}", response_model=FAQResponse)
def patch_faq(
    organization_id: int,
    faq_id: int,
    data: FAQPatch,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    faq = service.patch_faq(db, organization_id, faq_id, data)
    if faq is None:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found in this organization",
        )
    return faq


@router.delete("/{faq_id}")
def delete_faq(
    organization_id: int,
    faq_id: int,
    db: Session = Depends(get_db),
    membership: models.OrganizationMembership = Depends(
        get_organization_membership
    ),
):
    if not service.delete_faq(db, organization_id, faq_id):
        raise HTTPException(
            status_code=404,
            detail="FAQ not found in this organization",
        )

    return {
        "message": "FAQ deleted successfully",
        "organization_id": organization_id,
        "faq_id": faq_id,
    }
