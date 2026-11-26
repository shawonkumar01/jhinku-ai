
from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app import models
from app.auth.router import router as auth_router
from app.schemas import (
    FAQCreate,
    FAQUpdate,
    FAQPatch,
    FAQResponse,
    OrganizationCreate,
    OrganizationResponse,
)


app = FastAPI(
    title="Jhinku AI",
    description="AI Customer Support SaaS Platform",
    version="0.1.0"
)


# ==========================================
# BASIC ROUTES
# ==========================================

app.include_router(auth_router)


@app.get("/")
async def root():
    return {
        "message": "Welcome to Jhinku AI",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/db-health")
def database_health():
    try:
        from sqlalchemy import text

        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "database": "jhinku_ai_db"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )


# ==========================================
# ORGANIZATION ROUTES
# ==========================================

# CREATE ORGANIZATION
@app.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED
)
def create_organization(
    organization: OrganizationCreate,
    db: Session = Depends(get_db)
):
    new_organization = models.Organization(
        name=organization.name
    )

    db.add(new_organization)
    db.commit()
    db.refresh(new_organization)

    return new_organization


# GET ALL ORGANIZATIONS
@app.get("/organizations")
def get_organizations(
    db: Session = Depends(get_db)
):
    organizations = (
        db.query(models.Organization)
        .order_by(models.Organization.id)
        .all()
    )

    return {
        "total": len(organizations),
        "data": organizations
    }


# GET SINGLE ORGANIZATION
@app.get(
    "/organizations/{organization_id}",
    response_model=OrganizationResponse
)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db)
):
    organization = db.get(
        models.Organization,
        organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    return organization


# ==========================================
# ORGANIZATION FAQ ROUTES
# ==========================================

# CREATE FAQ UNDER AN ORGANIZATION
@app.post(
    "/organizations/{organization_id}/faqs",
    response_model=FAQResponse,
    status_code=status.HTTP_201_CREATED
)
def create_organization_faq(
    organization_id: int,
    faq: FAQCreate,
    db: Session = Depends(get_db)
):
    organization = db.get(
        models.Organization,
        organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    new_faq = models.FAQ(
        organization_id=organization_id,
        question=faq.question,
        answer=faq.answer
    )

    db.add(new_faq)
    db.commit()
    db.refresh(new_faq)

    return new_faq


# GET ALL FAQS OF AN ORGANIZATION
@app.get(
    "/organizations/{organization_id}/faqs"
)
def get_organization_faqs(
    organization_id: int,
    db: Session = Depends(get_db)
):
    organization = db.get(
        models.Organization,
        organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    faqs = (
        db.query(models.FAQ)
        .filter(
            models.FAQ.organization_id == organization_id
        )
        .order_by(models.FAQ.id)
        .all()
    )

    return {
        "organization_id": organization_id,
        "organization_name": organization.name,
        "total": len(faqs),
        "data": faqs
    }


# GET SINGLE FAQ
@app.get(
    "/organizations/{organization_id}/faqs/{faq_id}",
    response_model=FAQResponse
)
def get_organization_faq(
    organization_id: int,
    faq_id: int,
    db: Session = Depends(get_db)
):
    faq = (
        db.query(models.FAQ)
        .filter(
            models.FAQ.id == faq_id,
            models.FAQ.organization_id == organization_id
        )
        .first()
    )

    if faq is None:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found in this organization"
        )

    return faq


# PUT - FULL FAQ UPDATE
@app.put(
    "/organizations/{organization_id}/faqs/{faq_id}",
    response_model=FAQResponse
)
def update_organization_faq(
    organization_id: int,
    faq_id: int,
    updated_faq: FAQUpdate,
    db: Session = Depends(get_db)
):
    faq = (
        db.query(models.FAQ)
        .filter(
            models.FAQ.id == faq_id,
            models.FAQ.organization_id == organization_id
        )
        .first()
    )

    if faq is None:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found in this organization"
        )

    faq.question = updated_faq.question
    faq.answer = updated_faq.answer

    db.commit()
    db.refresh(faq)

    return faq


# PATCH - PARTIAL FAQ UPDATE
@app.patch(
    "/organizations/{organization_id}/faqs/{faq_id}",
    response_model=FAQResponse
)
def patch_organization_faq(
    organization_id: int,
    faq_id: int,
    updated_data: FAQPatch,
    db: Session = Depends(get_db)
):
    faq = (
        db.query(models.FAQ)
        .filter(
            models.FAQ.id == faq_id,
            models.FAQ.organization_id == organization_id
        )
        .first()
    )

    if faq is None:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found in this organization"
        )

    update_fields = updated_data.model_dump(
        exclude_unset=True,
        exclude_none=True
    )

    if not update_fields:
        raise HTTPException(
            status_code=400,
            detail="At least one valid field must be provided"
        )

    for key, value in update_fields.items():
        setattr(faq, key, value)

    db.commit()
    db.refresh(faq)

    return faq


# DELETE FAQ
@app.delete(
    "/organizations/{organization_id}/faqs/{faq_id}"
)
def delete_organization_faq(
    organization_id: int,
    faq_id: int,
    db: Session = Depends(get_db)
):
    faq = (
        db.query(models.FAQ)
        .filter(
            models.FAQ.id == faq_id,
            models.FAQ.organization_id == organization_id
        )
        .first()
    )

    if faq is None:
        raise HTTPException(
            status_code=404,
            detail="FAQ not found in this organization"
        )

    db.delete(faq)
    db.commit()

    return {
        "message": "FAQ deleted successfully",
        "organization_id": organization_id,
        "faq_id": faq_id
    }
