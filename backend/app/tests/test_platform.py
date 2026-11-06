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


def test_cors_origin_regex_setting_is_wired():
    from app.main import app as fastapi_app
    cors = [m for m in fastapi_app.user_middleware if m.cls.__name__ == "CORSMiddleware"][0]
    assert "allow_origin_regex" in cors.kwargs and cors.kwargs["allow_credentials"] is False


def test_release_models_clears_cached_engines():
    from app.adapters.tts_adapter import tts_adapter
    from app.adapters.whisper_adapter import whisper_adapter
    from app.services.job_runner_service import release_models
    whisper_adapter._model, tts_adapter._kokoro = object(), object()
    release_models()
    assert whisper_adapter._model is None and tts_adapter._kokoro is None


def test_ffmpeg_threads_cap(monkeypatch):
    from app.adapters.ffmpeg_adapter import threading_args
    from app.core.config import settings
    monkeypatch.setattr(settings, "FFMPEG_THREADS", 0)
    assert threading_args(["-i", "a.wav", "o.mp4"], "o.mp4") == ["-i", "a.wav", "o.mp4"]
    monkeypatch.setattr(settings, "FFMPEG_THREADS", 2)
    out = threading_args(["-i", "a.wav", "o.mp4"], "o.mp4")
    assert out[:4] == ["-filter_threads", "2", "-filter_complex_threads", "2"]
    assert out[-3:] == ["-threads", "2", "o.mp4"]


def test_ffmpeg_threads_cap_still_produces_output(monkeypatch, tmp_path):
    from app.adapters.ffmpeg_adapter import ffmpeg_adapter
    from app.core.config import settings
    if not ffmpeg_adapter.get_ffmpeg_cmd():
        import pytest
        pytest.skip("FFmpeg not installed")
    monkeypatch.setattr(settings, "FFMPEG_THREADS", 1)
    out = str(tmp_path / "t.mp4")
    ffmpeg_adapter.run_ffmpeg(["-f", "lavfi", "-i", "testsrc=size=320x240:rate=10", "-t", "1",
                               "-c:v", "libx264", "-pix_fmt", "yuv420p", out], out)
    assert (tmp_path / "t.mp4").stat().st_size > 0


def test_free_models_respects_keep_models_loaded(monkeypatch):
    from app.adapters.tts_adapter import tts_adapter
    from app.core.config import settings
    from app.engines.pipelines.common import free_models
    sentinel = object()
    monkeypatch.setattr(settings, "KEEP_MODELS_LOADED", True)
    tts_adapter._kokoro = sentinel
    free_models()
    assert tts_adapter._kokoro is sentinel
    monkeypatch.setattr(settings, "KEEP_MODELS_LOADED", False)
    free_models()
    assert tts_adapter._kokoro is None


def _queued_job(tool="text_to_image", params=None):
    from app.models.entities import Job
    db = SessionLocal()
    try:
        job = Job(tool=tool, status="running", progress=10,
                  params_json=params or {"mode": "poster", "text": "Isolated", "aspect": "square", "style": "auto",
                                         "image_format": "png"}, input_asset_ids=[])
        db.add(job); db.commit()
        return job.id
    finally:
        db.close()


def _job(job_id):
    from app.models.entities import Job
    db = SessionLocal()
    try:
        return db.query(Job).filter(Job.id == job_id).one()
    finally:
        db.close()


def test_isolated_job_runs_in_child_process():
    from app.worker.isolated import run_job_isolated
    job_id = _queued_job()
    result = run_job_isolated(job_id, memory_limit_mb=0)
    assert result["exitcode"] == 0, result
    assert _job(job_id).status == "succeeded"


def test_isolated_job_over_memory_limit_is_stopped_and_failed_cleanly():
    from app.worker.isolated import run_job_isolated
    job_id = _queued_job()
    result = run_job_isolated(job_id, memory_limit_mb=1)          # any real process exceeds 1 MB
    assert result["killed_for_memory"] is True
    job = _job(job_id)
    assert job.status == "failed" and job.error_code == "OUT_OF_MEMORY" and "memory" in job.error_message
