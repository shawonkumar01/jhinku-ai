
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth.schemas import TokenResponse, UserLogin, UserRegister
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expiry,
    verify_password,
)
from app import models


def _issue_tokens(db: Session, user: models.User) -> TokenResponse:
    """Create an access token and a new stored refresh token."""
    raw_refresh = generate_refresh_token()

    db.add(
        models.RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=refresh_token_expiry(),
        )
    )
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=raw_refresh,
    )


def register_user(
    db: Session, data: UserRegister
) -> models.User:
    existing = (
        db.query(models.User)
        .filter(models.User.email == data.email.lower())
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = models.User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(
    db: Session, data: UserLogin
) -> TokenResponse:
    user = (
        db.query(models.User)
        .filter(models.User.email == data.email.lower())
        .first()
    )

    # Same error for unknown email and wrong password to avoid
    # revealing which emails are registered.
    if user is None or not verify_password(
        data.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    return _issue_tokens(db, user)


def refresh_tokens(db: Session, raw_refresh: str) -> TokenResponse:
    """Rotate a refresh token: revoke the old one, issue a new pair."""
    token_hash = hash_refresh_token(raw_refresh)
    stored = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == token_hash)
        .first()
    )

    now = datetime.now(timezone.utc)
    expires_at = stored.expires_at if stored else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if (
        stored is None
        or stored.revoked_at is not None
        or expires_at <= now
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = stored.user
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # Revoke the presented token before issuing the new one.
    stored.revoked_at = now
    db.commit()

    return _issue_tokens(db, user)


def logout_user(db: Session, raw_refresh: str) -> None:
    """Revoke a refresh token so it can no longer be used."""
    token_hash = hash_refresh_token(raw_refresh)
    stored = (
        db.query(models.RefreshToken)
        .filter(models.RefreshToken.token_hash == token_hash)
        .first()
    )

    if stored is not None and stored.revoked_at is None:
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()
