
import os
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import models
from app.core.config import MAX_UPLOAD_SIZE_MB, UPLOAD_DIR
from app.database import SessionLocal
from app.knowledge.chunking import chunk_text
from app.knowledge.extract import extract_text

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def _storage_path(organization_id: int, source_id: int, ext: str) -> Path:
    return (
        Path(UPLOAD_DIR)
        / str(organization_id)
        / f"{source_id}{ext}"
    )


def _validate_upload(filename: str, file_size: int) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: PDF, TXT, DOCX",
        )
    if file_size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds the {MAX_UPLOAD_SIZE_MB}MB limit",
        )
    return ext


def create_source(
    db: Session,
    organization_id: int,
    file: UploadFile,
    title: str | None,
    chatbot_id: int | None,
) -> models.KnowledgeSource:
    # Read the upload into memory once; size is checked before writing.
    content = file.file.read()
    ext = _validate_upload(file.filename, len(content))

    if chatbot_id is not None:
        chatbot = (
            db.query(models.Chatbot)
            .filter(
                models.Chatbot.id == chatbot_id,
                models.Chatbot.organization_id == organization_id,
            )
            .first()
        )
        if chatbot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chatbot not found in this organization",
            )

    source = models.KnowledgeSource(
        organization_id=organization_id,
        chatbot_id=chatbot_id,
        title=title or file.filename or "Untitled",
        original_filename=file.filename or "unknown",
        file_path="",  # set after we know the source id
        file_size=len(content),
        content_type=file.content_type,
        processing_status=models.ProcessingStatus.PENDING,
    )
    db.add(source)
    db.flush()  # assigns source.id without committing

    file_path = _storage_path(organization_id, source.id, ext)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)
    source.file_path = str(file_path)

    db.commit()
    db.refresh(source)
    return source


def process_source(
    source_id: int, db: Session | None = None
) -> None:
    """Extract, clean, chunk and store document text.

    Designed to be called from a FastAPI BackgroundTask now and a
    Celery/RQ worker later — it manages its own DB session unless
    one is provided (used by tests).
    """
    own_session = db is None
    if own_session:
        db = SessionLocal()
    try:
        source = db.get(models.KnowledgeSource, source_id)
        if source is None:
            return

        source.processing_status = models.ProcessingStatus.PROCESSING
        source.error_message = None
        db.commit()

        text = extract_text(source.file_path)
        chunks = chunk_text(text)

        if not chunks:
            raise ValueError("No text could be extracted from the file")

        for index, chunk in enumerate(chunks):
            db.add(
                models.KnowledgeChunk(
                    organization_id=source.organization_id,
                    chatbot_id=source.chatbot_id,
                    knowledge_source_id=source.id,
                    content=chunk,
                    chunk_index=index,
                )
            )

        source.chunk_count = len(chunks)
        source.processing_status = models.ProcessingStatus.COMPLETED
        db.commit()
    except Exception:
        # Log the real error server-side; expose a generic message.
        import logging

        logging.getLogger(__name__).exception(
            "Knowledge source %s processing failed", source_id
        )
        source = db.get(models.KnowledgeSource, source_id)
        if source is not None:
            source.processing_status = models.ProcessingStatus.FAILED
            source.error_message = "Document processing failed"
            db.commit()
    finally:
        if own_session:
            db.close()


def list_sources(
    db: Session, organization_id: int
) -> list[models.KnowledgeSource]:
    return (
        db.query(models.KnowledgeSource)
        .filter(models.KnowledgeSource.organization_id == organization_id)
        .order_by(models.KnowledgeSource.id)
        .all()
    )


def get_source(
    db: Session, organization_id: int, source_id: int
) -> models.KnowledgeSource | None:
    return (
        db.query(models.KnowledgeSource)
        .filter(
            models.KnowledgeSource.id == source_id,
            models.KnowledgeSource.organization_id == organization_id,
        )
        .first()
    )


def delete_source(
    db: Session, organization_id: int, source_id: int
) -> bool:
    source = get_source(db, organization_id, source_id)
    if source is None:
        return False

    # Remove the stored file (ignore if already missing).
    try:
        os.remove(source.file_path)
    except OSError:
        pass

    db.delete(source)  # chunks removed via cascade
    db.commit()
    return True
