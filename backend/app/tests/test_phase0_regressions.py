"""
Phase 0 regression tests: security, ownership isolation, durable jobs, database
safety and FFmpeg format/timeout handling. Each test maps to a PROJECT_AUDIT.md finding.
"""
import io
import os
import subprocess
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core import config as config_module
from app.core import database as database_module
from app.core.config import Settings, validate_settings, storage_warnings
from app.core.database import SessionLocal, resolve_database_url, DatabaseConfigurationError
from app.core.security import create_access_key, revoke_access_keys, sign_download_path
from app.models.entities import Asset, Job, JobLease
from app.adapters.ffmpeg_adapter import ffmpeg_adapter, FFmpegTimeoutError
from app.services.job_queue import claim_next_job, recover_stale_jobs
from app.services.job_runner_service import job_runner_service
from app.services.storage_service import storage_service

client = TestClient(app)
settings = config_module.settings

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


# ---------------- helpers ----------------
def new_user(prefix: str = "user"):
    db = SessionLocal()
    try:
        user, key = create_access_key(db, f"{prefix}-{uuid.uuid4().hex[:8]}@example.com")
        return user.id, key
    finally:
        db.close()


def auth(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


def upload(headers=None, name="pic.png", data=PNG_BYTES, content_type="image/png"):
    return client.post(
        "/api/v1/media",
        files={"file": (name, io.BytesIO(data), content_type)},
        headers=headers or {},
    )


@pytest.fixture
def access_key_mode(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_MODE", "access_key")


@pytest.fixture
def drained(worker):
    """Start from an empty queue so queue-level assertions are deterministic."""
    worker.drain()
    return worker


@pytest.fixture
def mini_video(tmp_path):
    ffmpeg_bin = ffmpeg_adapter.get_ffmpeg_cmd()
    if not ffmpeg_bin or not ffmpeg_adapter.is_available():
        pytest.skip("FFmpeg executable not available on this host environment.")
    path = tmp_path / "clip.mp4"
    res = subprocess.run(
        [
            ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", "testsrc=duration=1:size=160x120:rate=10",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
            str(path),
        ],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    assert res.returncode == 0, res.stderr
    return path


# =====================================================================
# 1. Download Content-Type vulnerability (audit 4.1)
# =====================================================================
def test_upload_ignores_spoofed_client_content_type():
    res = upload(name="evil.png", content_type="text/html")
    assert res.status_code == 200
    asset = res.json()
    assert asset["media_type"] == "image/png"

    dl = client.get(asset["download_url"])
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("image/png")
    assert dl.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in dl.headers["content-security-policy"]
    assert dl.headers["content-disposition"].startswith("attachment")


def test_download_ignores_untrusted_media_type_stored_by_old_versions():
    asset_id = upload().json()["id"]
    db = SessionLocal()
    try:
        db.query(Asset).filter(Asset.id == asset_id).update({"media_type": "text/html"})
        db.commit()
    finally:
        db.close()

    dl = client.get(f"/api/v1/assets/{asset_id}/download")
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("image/png")
    assert "text/html" not in dl.headers["content-type"]


def test_svg_is_served_as_sandboxed_attachment():
    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
    asset = upload(name="logo.svg", data=svg, content_type="text/html").json()
    dl = client.get(asset["download_url"])
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith("image/svg+xml")
    assert dl.headers["content-disposition"].startswith("attachment")
    assert "sandbox" in dl.headers["content-security-policy"]


def test_html_upload_still_rejected():
    assert upload(name="page.html", data=b"<html></html>", content_type="text/html").status_code == 400


def test_missing_physical_file_returns_410_gone():
    asset = upload().json()
    os.remove(storage_service.get_full_path(_storage_key(asset["id"])))
    dl = client.get(f"/api/v1/assets/{asset['id']}/download")
    assert dl.status_code == 410
    assert "no longer available" in dl.json()["detail"]


def _storage_key(asset_id: str) -> str:
    db = SessionLocal()
    try:
        return db.query(Asset).filter(Asset.id == asset_id).first().storage_key
    finally:
        db.close()


# =====================================================================
# 2. Ownership & access isolation (audit 4.2)
# =====================================================================
def test_users_cannot_see_or_download_each_others_assets():
    _, key_a = new_user("alice")
    _, key_b = new_user("bob")
    asset_a = upload(auth(key_a)).json()

    ids_b = [a["id"] for a in client.get("/api/v1/assets", headers=auth(key_b)).json()]
    assert asset_a["id"] not in ids_b
    assert client.get(f"/api/v1/assets/{asset_a['id']}", headers=auth(key_b)).status_code == 404
    assert client.get(f"/api/v1/assets/{asset_a['id']}/download", headers=auth(key_b)).status_code == 404

    assert client.get(f"/api/v1/assets/{asset_a['id']}", headers=auth(key_a)).status_code == 200
    ids_a = [a["id"] for a in client.get("/api/v1/assets", headers=auth(key_a)).json()]
    assert asset_a["id"] in ids_a


def test_users_cannot_process_each_others_assets():
    _, key_a = new_user("alice")
    _, key_b = new_user("bob")
    asset_a = upload(auth(key_a), name="a.mp4", content_type="video/mp4").json()
    res = client.post(
        "/api/v1/jobs",
        json={"tool": "video_to_audio", "input_asset_ids": [asset_a["id"]], "params_json": {"audio_format": "mp3"}},
        headers=auth(key_b),
    )
    assert res.status_code == 404


def test_users_cannot_see_each_others_projects_and_jobs(worker):
    _, key_a = new_user("alice")
    _, key_b = new_user("bob")
    project = client.post("/api/v1/projects", json={"title": "Private A"}, headers=auth(key_a)).json()
    job = client.post(
        "/api/v1/jobs",
        json={"tool": "idea_to_storyboard", "params_json": {"concept": "A quiet lighthouse keeper story at night"}},
        headers=auth(key_a),
    ).json()
    worker.drain()

    assert client.get(f"/api/v1/projects/{project['id']}", headers=auth(key_b)).status_code == 404
    assert client.get(f"/api/v1/projects/{project['id']}/assets", headers=auth(key_b)).status_code == 404
    assert project["id"] not in [p["id"] for p in client.get("/api/v1/projects", headers=auth(key_b)).json()]
    assert client.get(f"/api/v1/jobs/{job['id']}", headers=auth(key_b)).status_code == 404
    assert job["id"] not in [j["id"] for j in client.get("/api/v1/jobs", headers=auth(key_b)).json()]
    assert upload(auth(key_b), name="x.png").status_code == 200
    res = client.post(
        "/api/v1/media",
        files={"file": ("x.png", io.BytesIO(PNG_BYTES), "image/png")},
        data={"project_id": project["id"]},
        headers=auth(key_b),
    )
    assert res.status_code == 404

    # Owner sees everything, and job outputs are owned by the job owner
    own = client.get(f"/api/v1/jobs/{job['id']}", headers=auth(key_a)).json()
    assert own["status"] == "succeeded"
    assert own["outputs"][0]["asset"]["owner_id"] == own["user_id"]


def test_access_key_mode_requires_valid_key(access_key_mode):
    assert client.get("/api/v1/assets").status_code == 401
    assert client.get("/api/v1/assets", headers=auth("mtk_not-a-real-key")).status_code == 401
    assert client.post("/api/v1/projects", json={"title": "x"}).status_code == 401
    assert client.get("/api/v1/assets/anything/download").status_code == 401
    _, key = new_user("carol")
    assert client.get("/api/v1/assets", headers=auth(key)).status_code == 200
    assert client.get("/api/v1/assets", headers={"X-Access-Key": key}).status_code == 200
    # Health stays public for uptime monitors
    assert client.get("/health").status_code == 200


def test_revoked_key_is_rejected(access_key_mode):
    user_id, key = new_user("dave")
    assert client.get("/api/v1/jobs", headers=auth(key)).status_code == 200
    db = SessionLocal()
    try:
        from app.models.entities import User
        email = db.query(User).filter(User.id == user_id).first().email
        assert revoke_access_keys(db, email) == 1
    finally:
        db.close()
    assert client.get("/api/v1/jobs", headers=auth(key)).status_code == 401


def test_raw_access_keys_are_not_stored():
    _, key = new_user("erin")
    db = SessionLocal()
    try:
        from app.models.entities import AccessKey
        stored = [k.key_hash for k in db.query(AccessKey).all()]
    finally:
        db.close()
    assert key not in stored
    assert all(len(h) == 64 for h in stored)


def test_production_configuration_is_validated():
    secret = "s" * 48
    assert validate_settings(Settings(ENVIRONMENT="production", SIGNING_SECRET=secret)) == []
    assert Settings(ENVIRONMENT="production", SIGNING_SECRET=secret).effective_auth_mode == "access_key"
    assert validate_settings(Settings(ENVIRONMENT="production", AUTH_MODE="dev_open", SIGNING_SECRET=secret))
    assert validate_settings(Settings(ENVIRONMENT="production", SIGNING_SECRET=""))
    assert validate_settings(Settings(ENVIRONMENT="production", SIGNING_SECRET="short"))
    assert Settings(ENVIRONMENT="development").effective_auth_mode == "dev_open"


def test_cors_never_allows_credentials():
    res = client.get("/health", headers={"Origin": "https://evil.example"})
    assert res.headers.get("access-control-allow-credentials") is None


# =====================================================================
# 3. Signed download URLs
# =====================================================================
def test_signed_download_url_works_without_key_and_rejects_tampering(access_key_mode):
    _, key = new_user("frank")
    asset = upload(auth(key)).json()
    url = asset["download_url"]
    assert "signature=" in url and "expires=" in url

    assert client.get(url).status_code == 200
    assert client.get(url[:-4] + "0000").status_code == 403

    expired = sign_download_path(asset["id"], ttl_seconds=-10)
    assert client.get(expired).status_code == 403

    other = upload(auth(key)).json()
    forged = url.replace(asset["id"], other["id"])
    assert client.get(forged).status_code == 403


# =====================================================================
# 4. Silent SQLite fallback (audit 4.4) and health (audit 4.8)
# =====================================================================
UNREACHABLE_PG = "postgresql://user:pass@127.0.0.1:1/nowhere"


def test_production_refuses_unreachable_postgres():
    with pytest.raises(DatabaseConfigurationError):
        resolve_database_url(UNREACHABLE_PG, is_development=False)


def test_production_refuses_sqlite():
    with pytest.raises(DatabaseConfigurationError):
        resolve_database_url("sqlite:///./x.db", is_development=False)


def test_development_falls_back_to_sqlite_only_when_allowed():
    assert resolve_database_url(UNREACHABLE_PG, is_development=True).startswith("sqlite")
    with pytest.raises(DatabaseConfigurationError):
        resolve_database_url(UNREACHABLE_PG, is_development=True, allow_sqlite_fallback=False)


def test_postgres_scheme_normalised():
    assert resolve_database_url("sqlite:///./x.db", is_development=True) == "sqlite:///./x.db"
    from app.core.database import normalize_database_url
    assert normalize_database_url("postgres://a:b@h/db").startswith("postgresql+psycopg2://")


def test_health_reports_database_outage(monkeypatch):
    class BrokenEngine:
        def connect(self):
            raise RuntimeError("db down")

    monkeypatch.setattr(database_module, "engine", BrokenEngine())
    res = client.get("/health")
    assert res.status_code == 503
    assert res.json() == {"status": "error", "database": "unreachable"}


def test_ephemeral_storage_warning_in_production():
    s = Settings(ENVIRONMENT="production", SIGNING_SECRET="s" * 48, STORAGE_DIR="/tmp/storage")
    assert storage_warnings(s)


# =====================================================================
# 5. Durable job queue (audit 4.3)
# =====================================================================
def _create_storyboard_job(headers=None) -> str:
    res = client.post(
        "/api/v1/jobs",
        json={"tool": "idea_to_storyboard", "params_json": {"concept": "Glacier research team tracking ancient ice cores"}},
        headers=headers or {},
    )
    assert res.status_code == 200
    return res.json()["id"]


def test_job_is_persisted_as_queued_and_run_by_worker(drained):
    job_id = _create_storyboard_job()
    assert client.get(f"/api/v1/jobs/{job_id}").json()["status"] == "queued"

    assert drained.run_once() == job_id
    job = client.get(f"/api/v1/jobs/{job_id}").json()
    assert job["status"] == "succeeded"
    assert job["outputs"][0]["asset"]["download_url"]


def test_job_claim_is_atomic(drained):
    job_id = _create_storyboard_job()
    db = SessionLocal()
    try:
        assert claim_next_job(db, "worker-1") == job_id
        assert claim_next_job(db, "worker-2") is None
        lease = db.get(JobLease, job_id)
        assert lease.worker_id == "worker-1" and lease.attempts == 1
    finally:
        db.close()

    # A second executor cannot run a job that another worker holds
    job = job_runner_service.process_job(job_id)
    assert job.status == "running"
    assert client.get(f"/api/v1/jobs/{job_id}").json()["outputs"] == []

    job_runner_service.process_job(job_id, already_claimed=True)  # the owner finishes it
    assert client.get(f"/api/v1/jobs/{job_id}").json()["status"] == "succeeded"


def _age_lease(job_id: str, seconds: int):
    db = SessionLocal()
    try:
        lease = db.get(JobLease, job_id)
        lease.heartbeat_at = datetime.utcnow() - timedelta(seconds=seconds)
        db.commit()
    finally:
        db.close()


def test_abandoned_job_is_requeued_then_failed(drained):
    job_id = _create_storyboard_job()
    stale = settings.JOB_STALE_AFTER_SECONDS + 30

    db = SessionLocal()
    try:
        assert claim_next_job(db, "crashed-worker") == job_id
    finally:
        db.close()

    _age_lease(job_id, stale)
    db = SessionLocal()
    try:
        assert recover_stale_jobs(db) >= 1
        assert db.get(Job, job_id).status == "queued"
        for _ in range(settings.JOB_MAX_ATTEMPTS - 1):
            assert claim_next_job(db, "crashed-again") == job_id
            db.close()
            _age_lease(job_id, stale)
            db = SessionLocal()
            recover_stale_jobs(db)
        job = db.get(Job, job_id)
        assert job.status == "failed"
        assert job.error_code == "WORKER_LOST"
    finally:
        db.close()


def test_recent_heartbeat_is_not_recovered(drained):
    job_id = _create_storyboard_job()
    db = SessionLocal()
    try:
        claim_next_job(db, "healthy-worker")
        recover_stale_jobs(db)
        assert db.get(Job, job_id).status == "running"
    finally:
        db.close()
    job_runner_service.process_job(job_id, already_claimed=True)


def test_legacy_stuck_running_job_without_lease_is_recovered():
    db = SessionLocal()
    try:
        job = Job(tool="idea_to_storyboard", status="running", progress=10,
                  params_json={"concept": "Legacy job left running by old runner"},
                  started_at=datetime.utcnow() - timedelta(hours=2))
        db.add(job)
        db.commit()
        recover_stale_jobs(db)
        db.refresh(job)
        assert job.status == "queued"
    finally:
        db.close()


def test_finished_job_is_never_rerun(drained):
    job_id = _create_storyboard_job()
    drained.run_once()
    job_runner_service.process_job(job_id)
    job_runner_service.process_job(job_id, already_claimed=True)
    assert len(client.get(f"/api/v1/jobs/{job_id}").json()["outputs"]) == 1


# =====================================================================
# 6. Video -> Audio formats (audit 4.6) and FFmpeg timeout (audit 4.7)
# =====================================================================
MAGIC = {
    "mp3": lambda b: b[:3] == b"ID3" or b[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"),
    "wav": lambda b: b[:4] == b"RIFF" and b[8:12] == b"WAVE",
    "flac": lambda b: b[:4] == b"fLaC",
    "ogg": lambda b: b[:4] == b"OggS",
    "m4a": lambda b: b[4:8] == b"ftyp",
}
MIME = {"mp3": "audio/mpeg", "wav": "audio/wav", "flac": "audio/flac", "ogg": "audio/ogg", "m4a": "audio/mp4"}


@pytest.mark.parametrize("fmt", ["mp3", "wav", "m4a", "ogg", "flac"])
def test_video_to_audio_each_format_has_correct_container(fmt, mini_video, drained):
    with open(mini_video, "rb") as f:
        video = client.post("/api/v1/media", files={"file": ("clip.mp4", f, "video/mp4")}).json()
    job = client.post(
        "/api/v1/jobs",
        json={"tool": "video_to_audio", "input_asset_ids": [video["id"]], "params_json": {"audio_format": fmt}},
    ).json()
    drained.run_once()

    data = client.get(f"/api/v1/jobs/{job['id']}").json()
    assert data["status"] == "succeeded", data["error_message"]
    out = data["outputs"][0]
    assert out["output_type"] == f"audio_{fmt}"
    assert out["asset"]["filename"] == f"clip_extracted.{fmt}"
    assert out["asset"]["media_type"] == MIME[fmt]
    assert out["asset"]["metadata_json"]["extraction_format"] == fmt

    dl = client.get(out["asset"]["download_url"])
    assert dl.status_code == 200
    assert dl.headers["content-type"].startswith(MIME[fmt])
    assert MAGIC[fmt](dl.content), f"{fmt} output does not have a valid {fmt} header"


def test_unsupported_audio_format_rejected_before_queueing():
    video = upload(name="v.mp4", data=b"0" * 32, content_type="video/mp4").json()
    res = client.post(
        "/api/v1/jobs",
        json={"tool": "video_to_audio", "input_asset_ids": [video["id"]], "params_json": {"audio_format": "exe"}},
    )
    assert res.status_code == 400
    assert "unsupported audio format" in res.json()["detail"].lower()


def test_ffmpeg_timeout_kills_job_and_removes_partial_output(mini_video, drained, monkeypatch):
    real_run = subprocess.run

    def hanging_ffmpeg(cmd, *args, **kwargs):
        if "-vn" in cmd:
            assert kwargs.get("timeout") == settings.FFMPEG_TIMEOUT_SECONDS
            with open(cmd[-1], "wb") as partial:
                partial.write(b"partial-output")
            raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout"))
        return real_run(cmd, *args, **kwargs)

    with open(mini_video, "rb") as f:
        video = client.post("/api/v1/media", files={"file": ("clip.mp4", f, "video/mp4")}).json()
    before = set(os.listdir(settings.STORAGE_DIR))

    monkeypatch.setattr("app.adapters.ffmpeg_adapter.subprocess.run", hanging_ffmpeg)
    job = client.post(
        "/api/v1/jobs",
        json={"tool": "video_to_audio", "input_asset_ids": [video["id"]], "params_json": {"audio_format": "mp3"}},
    ).json()
    drained.run_once()

    data = client.get(f"/api/v1/jobs/{job['id']}").json()
    assert data["status"] == "failed"
    assert data["error_code"] == "TIMEOUT"
    assert "time limit" in data["error_message"]
    assert set(os.listdir(settings.STORAGE_DIR)) == before, "partial output file was left behind"


def test_real_ffmpeg_process_is_stopped_by_timeout(mini_video, tmp_path):
    with pytest.raises(FFmpegTimeoutError):
        ffmpeg_adapter.extract_audio(str(mini_video), str(tmp_path / "out.mp3"), "mp3", timeout_seconds=0.001)
    assert not (tmp_path / "out.mp3").exists()


def test_output_extension_must_match_format(mini_video, tmp_path):
    with pytest.raises(ValueError):
        ffmpeg_adapter.extract_audio(str(mini_video), str(tmp_path / "out.mp3"), "wav")
