"""
Access keys (invite-only accounts) and signed download URLs.

Access keys are random 256-bit tokens. Because they carry full entropy, a plain
SHA-256 digest is sufficient for storage (no password-style slow hashing needed).
"""
import hashlib
import hmac
import secrets
import time
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import AccessKey, User

ACCESS_KEY_PREFIX = "mtk_"
DEV_USER_EMAIL = "local-dev@localhost"


# ---------------- Access keys ----------------
def generate_access_key() -> str:
    return ACCESS_KEY_PREFIX + secrets.token_urlsafe(32)


def hash_access_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.strip().encode("utf-8")).hexdigest()


def create_access_key(db: Session, email: str, label: Optional[str] = None) -> Tuple[User, str]:
    """Create (or reuse) the user for ``email`` and issue a new access key. Returns (user, raw_key)."""
    email = email.strip().lower()
    if not email or "@" not in email:
        raise ValueError("A valid email address is required.")
    if email == DEV_USER_EMAIL:
        raise ValueError("That email is reserved.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, role="user")
        db.add(user)
        db.flush()

    raw_key = generate_access_key()
    db.add(AccessKey(user_id=user.id, key_hash=hash_access_key(raw_key), label=label))
    db.commit()
    db.refresh(user)
    return user, raw_key


def revoke_access_keys(db: Session, email: str) -> int:
    user = db.query(User).filter(User.email == email.strip().lower()).first()
    if not user:
        return 0
    now = datetime.utcnow()
    keys = db.query(AccessKey).filter(AccessKey.user_id == user.id, AccessKey.revoked_at.is_(None)).all()
    for k in keys:
        k.revoked_at = now
    db.commit()
    return len(keys)


def authenticate_access_key(db: Session, raw_key: str) -> Optional[User]:
    if not raw_key:
        return None
    key = (
        db.query(AccessKey)
        .filter(AccessKey.key_hash == hash_access_key(raw_key), AccessKey.revoked_at.is_(None))
        .first()
    )
    if not key:
        return None
    key.last_used_at = datetime.utcnow()
    db.commit()
    return db.query(User).filter(User.id == key.user_id).first()


def get_or_create_dev_user(db: Session) -> User:
    user = db.query(User).filter(User.email == DEV_USER_EMAIL).first()
    if not user:
        user = User(email=DEV_USER_EMAIL, role="developer")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def is_dev_user(user: User) -> bool:
    return user is not None and user.email == DEV_USER_EMAIL


# ---------------- Signed download URLs ----------------
def _signature(asset_id: str, expires: int) -> str:
    msg = f"{asset_id}:{expires}".encode("utf-8")
    return hmac.new(settings.SIGNING_SECRET.encode("utf-8"), msg, hashlib.sha256).hexdigest()


def sign_download_path(asset_id: str, ttl_seconds: Optional[int] = None) -> str:
    expires = int(time.time()) + (ttl_seconds if ttl_seconds is not None else settings.DOWNLOAD_URL_TTL_SECONDS)
    return f"/api/v1/assets/{asset_id}/download?expires={expires}&signature={_signature(asset_id, expires)}"


def verify_download_signature(asset_id: str, expires: Optional[int], signature: Optional[str]) -> bool:
    if expires is None or not signature:
        return False
    if int(expires) < int(time.time()):
        return False
    return hmac.compare_digest(_signature(asset_id, int(expires)), signature)
