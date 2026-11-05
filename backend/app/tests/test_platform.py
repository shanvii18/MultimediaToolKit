"""Platform features added for the complete website: /me, asset deletion, Redis wake-up queue."""
import io

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_key
from app.services import job_queue

client = TestClient(app)
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def _key(prefix):
    db = SessionLocal()
    try:
        user, key = create_access_key(db, f"{prefix}-{id(db)}@example.com")
        return user.email, {"Authorization": f"Bearer {key}"}
    finally:
        db.close()


def test_me_returns_signed_in_user_and_mode():
    email, headers = _key("me")
    res = client.get("/api/v1/me", headers=headers)
    assert res.status_code == 200 and res.json()["email"] == email
    assert res.json()["auth_mode"] == "dev_open"  # tests run in development
    assert client.get("/api/v1/me", headers={"Authorization": "Bearer mtk_wrong"}).status_code == 401


def test_owner_can_delete_asset_and_others_cannot():
    _, alice = _key("alice-del")
    _, bob = _key("bob-del")
    asset = client.post("/api/v1/media", files={"file": ("a.png", io.BytesIO(PNG), "image/png")}, headers=alice).json()
    assert client.delete(f"/api/v1/assets/{asset['id']}", headers=bob).status_code == 404
    assert client.delete(f"/api/v1/assets/{asset['id']}", headers=alice).status_code == 204
    assert client.get(f"/api/v1/assets/{asset['id']}", headers=alice).status_code == 404
    assert client.get(asset["download_url"]).status_code == 404


class FakeRedis:
    def __init__(self):
        self.items = []

    def lpush(self, key, value):
        self.items.insert(0, (key, value))

    def ltrim(self, key, start, end):
        self.items = self.items[start:end + 1]

    def blpop(self, keys, timeout=0):
        return self.items.pop() if self.items else None


def test_redis_wakeup_signal_round_trip():
    fake = FakeRedis()
    assert job_queue.notify_new_job("job-1", client=fake) is True
    assert job_queue.wait_for_job_signal(1, client=fake) is True
    assert job_queue.wait_for_job_signal(1, client=fake) is False  # timed out, nothing queued


def test_redis_disabled_falls_back_to_polling():
    assert job_queue.notify_new_job("job-2") is False          # QUEUE_NOTIFY_REDIS is off in tests
    assert job_queue.wait_for_job_signal(1) is None             # caller polls the database instead
