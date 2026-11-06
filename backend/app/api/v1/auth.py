"""Public email + password accounts: sign up, sign in, sign out.

Signing in issues an expiring, random bearer token (stored only as a SHA-256 hash). Every other
API route still requires that token and keeps its ownership checks.
"""
import re
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.passwords import hash_password, password_problem, verify_password
from app.core.security import DEV_USER_EMAIL, create_session_token, revoke_token
from app.models.entities import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")


class Credentials(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=256)


# ---------------- tiny in-memory rate limiter (single instance; resets on restart) ----------------
class RateLimiter:
    def __init__(self) -> None:
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window_seconds: int) -> bool:
        """Record an attempt; False when the key exceeded ``limit`` attempts within the window."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window_seconds:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    for header in ("cf-connecting-ip", "true-client-ip"):
        if request.headers.get(header):
            return request.headers[header].strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _throttle(key: str, limit: int, window: int) -> None:
    if not limiter.hit(key, limit, window):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail="Too many attempts. Please wait a few minutes and try again.")


def _normalise_email(raw: str) -> str:
    email = raw.strip().lower()
    if not EMAIL_RE.match(email) or email == DEV_USER_EMAIL:
        raise HTTPException(status_code=422, detail="Please enter a valid email address.")
    return email


def _session_response(db: Session, user: User) -> dict:
    token, expires = create_session_token(db, user)
    return {"token": token, "expires_at": expires.isoformat() + "Z",
            "user": {"id": user.id, "email": user.email, "role": user.role}}


@router.post("/signup", status_code=201)
def signup(body: Credentials, request: Request, db: Session = Depends(get_db)):
    _throttle(f"signup:{client_ip(request)}", settings.SIGNUP_RATE_LIMIT_PER_HOUR, 3600)
    email = _normalise_email(body.email)
    problem = password_problem(body.password)
    if problem:
        raise HTTPException(status_code=422, detail=problem)
    if db.query(User).filter(User.email == email).first():
        # Accounts created before passwords existed are never claimable by sign-up (no takeover).
        raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in.")
    user = User(email=email, role="user", password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in.")
    db.refresh(user)
    return _session_response(db, user)


@router.post("/login")
def login(body: Credentials, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    email = body.email.strip().lower()
    _throttle(f"login-ip:{ip}", settings.LOGIN_RATE_LIMIT_PER_15_MIN * 3, 900)
    _throttle(f"login-email:{email}", settings.LOGIN_RATE_LIMIT_PER_15_MIN, 900)
    user = db.query(User).filter(User.email == email).first() if email else None
    if not verify_password(body.password, user.password_hash if user else None):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password.")
    return _session_response(db, user)


@router.post("/logout", status_code=204)
def logout(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if authorization and authorization.lower().startswith("bearer "):
        revoke_token(db, authorization[7:].strip())
    return None
