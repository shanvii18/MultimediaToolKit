"""Public email + password accounts: sign-up, sign-in, sessions, and per-user isolation."""
import io
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.v1.auth import limiter
from app.core import config as config_module
from app.core.database import SessionLocal
from app.core.passwords import hash_password, verify_password
from app.core.security import create_access_key, hash_access_key
from app.main import app
from app.models.entities import AccessKey, User

client = TestClient(app)
settings = config_module.settings
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
PASSWORD = "correct horse battery"


@pytest.fixture(autouse=True)
def production_like_auth(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "access_key")
    limiter.reset()
    yield
    limiter.reset()


def email() -> str:
    return f"User-{uuid.uuid4().hex[:8]}@Example.com"


def signup(addr: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/signup", json={"email": addr, "password": password})


def login(addr: str, password: str = PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": addr, "password": password})


def bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_password_hashing_roundtrip_and_salted():
    h1, h2 = hash_password("s3cret-pass"), hash_password("s3cret-pass")
    assert h1.startswith("scrypt$") and h1 != h2
    assert verify_password("s3cret-pass", h1) and not verify_password("wrong-pass", h1)
    assert not verify_password("anything", None)


def test_signup_creates_account_and_session():
    addr = email()
    r = signup(addr)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["user"]["email"] == addr.lower() and body["token"].startswith("mtk_")
    me = client.get("/api/v1/me", headers=bearer(body["token"]))
    assert me.status_code == 200 and me.json()["email"] == addr.lower()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == addr.lower()).one()
        assert user.password_hash.startswith("scrypt$") and PASSWORD not in user.password_hash
        key = db.query(AccessKey).filter(AccessKey.user_id == user.id).one()
        assert key.key_hash == hash_access_key(body["token"]) and key.expires_at > datetime.utcnow()
    finally:
        db.close()


def test_duplicate_signup_is_rejected_case_insensitively():
    addr = email()
    assert signup(addr).status_code == 201
    assert signup(addr.upper()).status_code == 409


def test_existing_invited_account_cannot_be_claimed_by_signup():
    db = SessionLocal()
    try:
        owner, _ = create_access_key(db, f"owner-{uuid.uuid4().hex[:6]}@example.com")
        owner_email = owner.email
    finally:
        db.close()
    assert signup(owner_email).status_code == 409
    assert login(owner_email, PASSWORD).status_code == 401      # no password yet -> cannot sign in


@pytest.mark.parametrize("bad_email", ["", "not-an-email", "a@b", "local-dev@localhost"])
def test_signup_validates_email(bad_email):
    assert signup(bad_email).status_code == 422


@pytest.mark.parametrize("bad_password", ["short", "aaaaaaaaaaaa", "x" * 200])
def test_signup_validates_password(bad_password):
    assert signup(email(), bad_password).status_code == 422


def test_login_success_and_generic_failures():
    addr = email()
    signup(addr)
    ok = login(addr.upper())
    assert ok.status_code == 200 and ok.json()["token"].startswith("mtk_")
    wrong = login(addr, "wrong password!")
    unknown = login(email(), PASSWORD)
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"] == "Incorrect email or password."


def test_logout_revokes_the_session():
    token = signup(email()).json()["token"]
    assert client.get("/api/v1/me", headers=bearer(token)).status_code == 200
    assert client.post("/api/v1/auth/logout", headers=bearer(token)).status_code == 204
    assert client.get("/api/v1/me", headers=bearer(token)).status_code == 401


def test_expired_session_is_rejected():
    token = signup(email()).json()["token"]
    db = SessionLocal()
    try:
        key = db.query(AccessKey).filter(AccessKey.key_hash == hash_access_key(token)).one()
        key.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()
    assert client.get("/api/v1/me", headers=bearer(token)).status_code == 401


def test_api_still_requires_authentication():
    for path in ("/api/v1/me", "/api/v1/jobs", "/api/v1/assets", "/api/v1/projects"):
        assert client.get(path).status_code == 401, path
    assert client.post("/api/v1/media", files={"file": ("a.png", io.BytesIO(PNG), "image/png")}).status_code == 401


def test_users_only_see_their_own_data():
    a = signup(email()).json()["token"]
    b = signup(email()).json()["token"]
    up = client.post("/api/v1/media", files={"file": ("a.png", io.BytesIO(PNG), "image/png")}, headers=bearer(a))
    assert up.status_code == 200
    asset_id = up.json()["id"]
    assert asset_id in [x["id"] for x in client.get("/api/v1/assets", headers=bearer(a)).json()]
    assert asset_id not in [x["id"] for x in client.get("/api/v1/assets", headers=bearer(b)).json()]
    assert client.get(f"/api/v1/assets/{asset_id}", headers=bearer(b)).status_code == 404
    assert client.delete(f"/api/v1/assets/{asset_id}", headers=bearer(b)).status_code == 404
    job = client.post("/api/v1/jobs", headers=bearer(b),
                      json={"tool": "image_to_text", "input_asset_ids": [asset_id], "params_json": {}})
    assert job.status_code in (403, 404)


def test_login_is_rate_limited_per_email():
    addr = email()
    signup(addr)
    codes = [login(addr, "wrong password!").status_code for _ in range(settings.LOGIN_RATE_LIMIT_PER_15_MIN + 1)]
    assert codes[-1] == 429 and set(codes[:-1]) == {401}
    assert login(addr).status_code == 429          # even the right password waits out the window


def test_signup_is_rate_limited_per_ip():
    codes = [signup(email()).status_code for _ in range(settings.SIGNUP_RATE_LIMIT_PER_HOUR + 1)]
    assert codes[-1] == 429


def test_set_password_cli_lets_an_existing_account_sign_in(monkeypatch):
    from app import cli
    db = SessionLocal()
    try:
        owner, _ = create_access_key(db, f"owner-{uuid.uuid4().hex[:6]}@example.com")
        owner_email = owner.email
    finally:
        db.close()
    monkeypatch.setenv("MTK_NEW_PASSWORD", PASSWORD)
    assert cli._set_password(owner_email) == 0
    assert login(owner_email).status_code == 200


def test_job_submission_is_idempotent_per_user():
    token = signup(email()).json()["token"]
    other = signup(email()).json()["token"]
    body = {"tool": "text_to_image", "input_asset_ids": [], "params_json": {"mode": "poster", "text": "Hello"}}
    h = {**bearer(token), "Idempotency-Key": "retry-key-123"}
    first = client.post("/api/v1/jobs", json=body, headers=h)
    second = client.post("/api/v1/jobs", json=body, headers=h)
    assert first.status_code == second.status_code == 200
    assert first.json()["id"] == second.json()["id"]                     # no duplicate conversion
    third = client.post("/api/v1/jobs", json=body, headers={**bearer(token), "Idempotency-Key": "another-key"})
    assert third.json()["id"] != first.json()["id"]
    # Keys are scoped per user: someone else's identical key never returns this user's job.
    theirs = client.post("/api/v1/jobs", json=body, headers={**bearer(other), "Idempotency-Key": "retry-key-123"})
    assert theirs.status_code == 200 and theirs.json()["id"] != first.json()["id"]


def test_unhandled_errors_return_json_500_with_cors(monkeypatch):
    from app.api.v1 import router as router_module
    from app.core.config import settings as s
    monkeypatch.setattr(s, "AUTH_MODE", "dev_open")

    def boom(*a, **k):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(router_module, "list_conversions", boom)
    c = TestClient(app, raise_server_exceptions=False)
    origin = (s.cors_origins or ["http://localhost:3000"])[0]
    origin = "http://localhost:3000" if origin == "*" else origin
    r = c.get("/api/v1/conversions", headers={"Origin": origin})
    assert r.status_code == 500 and r.json()["error_code"] == "SERVER_ERROR"
    assert r.headers.get("access-control-allow-origin") in (origin, "*")
