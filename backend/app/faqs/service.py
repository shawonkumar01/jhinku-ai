
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.faqs.schemas import FAQCreate, FAQPatch, FAQUpdate


def _get_faq(
    db: Session, organization_id: int, faq_id: int
) -> models.FAQ | None:
    return (
        db.query(models.FAQ)
        .filter(
            models.FAQ.id == faq_id,
            models.FAQ.organization_id == organization_id,
        )
        .first()
    )


def create_faq(
    db: Session, organization_id: int, data: FAQCreate
) -> models.FAQ:
    faq = models.FAQ(
        organization_id=organization_id,
        question=data.question,
        answer=data.answer,
    )
    db.add(faq)
    db.commit()
    db.refresh(faq)
    return faq


def list_faqs(db: Session, organization_id: int) -> list[models.FAQ]:
    return (
        db.query(models.FAQ)
        .filter(models.FAQ.organization_id == organization_id)
        .order_by(models.FAQ.id)
        .all()
    )


def get_faq(
    db: Session, organization_id: int, faq_id: int
) -> models.FAQ | None:
    return _get_faq(db, organization_id, faq_id)


def update_faq(
    db: Session,
    organization_id: int,
    faq_id: int,
    data: FAQUpdate,
) -> models.FAQ | None:
    faq = _get_faq(db, organization_id, faq_id)
    if faq is None:
        return None

    faq.question = data.question
    faq.answer = data.answer
    db.commit()
    db.refresh(faq)
    return faq


def patch_faq(
    db: Session,
    organization_id: int,
    faq_id: int,
    data: FAQPatch,
) -> models.FAQ | None:
    faq = _get_faq(db, organization_id, faq_id)
    if faq is None:
        return None

    update_fields = data.model_dump(exclude_unset=True, exclude_none=True)
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one valid field must be provided",
        )

    for key, value in update_fields.items():
        setattr(faq, key, value)

    db.commit()
    db.refresh(faq)
    return faq


def delete_faq(
    db: Session, organization_id: int, faq_id: int
) -> bool:
    faq = _get_faq(db, organization_id, faq_id)
    if faq is None:
        return False

    db.delete(faq)
    db.commit()
    return True
