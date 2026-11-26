
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.schemas import UserResponse
from app.core.security import decode_access_token
from app.database import get_db
from app import models

_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        _bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> models.User:
    """Resolve the authenticated user from the Authorization header."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise unauthorized

    user = db.get(models.User, user_id)
    if user is None or not user.is_active:
        raise unauthorized

    return user


def get_current_user_response(
    user: models.User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(user)
