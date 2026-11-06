"""Request dependencies: current user resolution and ownership scoping."""
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings, AUTH_MODE_DEV_OPEN
from app.core.database import get_db
from app.core.security import authenticate_access_key, get_or_create_dev_user, is_dev_user
from app.models.entities import User


def _extract_key(authorization: Optional[str], x_access_key: Optional[str]) -> Optional[str]:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip() or None
    if x_access_key:
        return x_access_key.strip() or None
    return None


def resolve_user(db: Session, authorization: Optional[str], x_access_key: Optional[str]) -> Optional[User]:
    """
    Returns the authenticated user, the local developer user (dev_open mode, no key sent),
    or None. Raises 401 when a key is sent but invalid/revoked.
    """
    raw_key = _extract_key(authorization, x_access_key)
    if raw_key:
        user = authenticate_access_key(db, raw_key)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or revoked access key.")
        return user
    if settings.effective_auth_mode == AUTH_MODE_DEV_OPEN:
        return get_or_create_dev_user(db)
    return None


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    x_access_key: Optional[str] = Header(None),
) -> User:
    user = resolve_user(db, authorization, x_access_key)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access key required. MultimediaToolKit is invite-only: open your personal invite link.",
        )
    return user


def get_optional_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
    x_access_key: Optional[str] = Header(None),
) -> Optional[User]:
    return resolve_user(db, authorization, x_access_key)


def owned_by(column, user: User):
    """
    SQL filter restricting rows to the user. The local developer user (development only)
    additionally sees legacy rows created before ownership existed (owner NULL).
    """
    if is_dev_user(user):
        return or_(column == user.id, column.is_(None))
    return column == user.id


def is_owner(owner_id: Optional[str], user: Optional[User]) -> bool:
    if user is None:
        return False
    if owner_id == user.id:
        return True
    return owner_id is None and is_dev_user(user)
