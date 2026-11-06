"""Phase 1 batch 1: S3-compatible storage backend and Alembic migrations."""
import io
import os
import sqlite3
import subprocess
import sys

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.core.config import Settings, validate_settings
from app.services import storage_service as storage_module
from app.services.storage_service import S3StorageBackend, LocalStorageBackend, StorageService, validate_key

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


# ---------------- storage keys ----------------
@pytest.mark.parametrize("bad", ["../x.png", "a/b.png", "..", "", "x\\..\\y.png", ".hidden"])
def test_invalid_storage_keys_rejected(bad):
    with pytest.raises(ValueError):
        validate_key(bad)


def test_local_backend_round_trip(tmp_path):
    backend = LocalStorageBackend(str(tmp_path / "store"))
    src = tmp_path / "in.txt"
    src.write_bytes(b"hello")
    backend.put_file(str(src), "abc.txt", "text/plain")
    assert backend.exists("abc.txt")
    assert open(backend.materialize("abc.txt", str(tmp_path / "work")), "rb").read() == b"hello"
    backend.delete("abc.txt")
    assert not backend.exists("abc.txt")
    with pytest.raises(FileNotFoundError):
        backend.materialize("abc.txt", str(tmp_path / "work"))


# ---------------- S3-compatible backend (moto: in-process fake S3, no network, no account) ----------------
@pytest.fixture
def s3_service():
    with mock_aws():
        from botocore.config import Config

        client = boto3.client("s3", region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test",
                              config=Config(signature_version="s3v4", s3={"addressing_style": "path"}))
        client.create_bucket(Bucket="mtk-test")
        backend = S3StorageBackend(bucket="mtk-test", key_prefix="mtk/", client=client)
        yield StorageService(backend), client


def test_s3_backend_stores_and_materializes(s3_service, tmp_path):
    service, client = s3_service
    key, size, checksum = service.write_output_file(b"transcript text", ".txt")
    assert key.startswith("out_") and key.endswith(".txt")
    assert size == 15 and len(checksum) == 64

    head = client.head_object(Bucket="mtk-test", Key=f"mtk/{key}")
    assert head["ContentType"].startswith("text/plain")

    local = service.materialize(key, str(tmp_path))
    assert open(local, "rb").read() == b"transcript text"
    assert service.exists(key)
    service.delete(key)
    assert not service.exists(key)
    with pytest.raises(FileNotFoundError):
        service.materialize(key, str(tmp_path))


def test_s3_presigned_url_forces_download_and_type(s3_service):
    service, _ = s3_service
    key, _, _ = service.write_output_file(b"x", ".mp3")
    url = service.backend.presigned_url(key, 'my"song.mp3', "audio/mpeg", 300)
    assert "response-content-disposition=attachment" in url
    assert "response-content-type=audio%2Fmpeg" in url
    assert "X-Amz-Expires=300" in url
    assert "%22my%22song" not in url  # quotes stripped from filename


def test_api_upload_and_download_redirect_with_s3(s3_service, monkeypatch):
    from app.main import app
    service, client = s3_service
    monkeypatch.setattr(storage_module.storage_service, "backend", service.backend)
    api = TestClient(app)

    res = api.post("/api/v1/media", files={"file": ("photo.png", io.BytesIO(PNG), "text/html")})
    assert res.status_code == 200, res.text
    asset = res.json()
    keys = [o["Key"] for o in client.list_objects_v2(Bucket="mtk-test")["Contents"]]
    assert any(k.endswith(".png") for k in keys)

    dl = api.get(asset["download_url"], follow_redirects=False)
    assert dl.status_code == 307
    assert "mtk-test" in dl.headers["location"] and "Signature=" in dl.headers["location"]

    # Object removed from the bucket -> honest 410, not a broken redirect
    client.delete_object(Bucket="mtk-test", Key=[k for k in keys if k.endswith(".png")][0])
    assert api.get(asset["download_url"], follow_redirects=False).status_code == 410


def test_s3_configuration_validated():
    assert validate_settings(Settings(STORAGE_BACKEND="s3"))
    ok = Settings(STORAGE_BACKEND="s3", S3_BUCKET="b", S3_ACCESS_KEY_ID="a", S3_SECRET_ACCESS_KEY="s")
    assert validate_settings(ok) == []
    assert validate_settings(Settings(STORAGE_BACKEND="ftp"))


# ---------------- Alembic migrations ----------------
def _run_python(code: str, db_path: str, tmp_path) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update({
        "ENVIRONMENT": "development",
        "DATABASE_URL": f"sqlite:///{db_path}",
        "STORAGE_DIR": str(tmp_path / "s"),
        "WORK_DIR": str(tmp_path / "w"),
        "EMBEDDED_WORKER": "false",
    })
    return subprocess.run([sys.executable, "-c", code], cwd=BACKEND_ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)


def _tables(db_path):
    con = sqlite3.connect(db_path)
    try:
        return {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    finally:
        con.close()


def _columns(db_path, table):
    con = sqlite3.connect(db_path)
    try:
        return {r[1] for r in con.execute(f"pragma table_info({table})")}
    finally:
        con.close()


def test_fresh_database_is_migrated_to_head(tmp_path):
    db = str(tmp_path / "fresh.db")
    res = _run_python("from app.core.migrations import upgrade_database; upgrade_database()", db, tmp_path)
    assert res.returncode == 0, res.stderr
    assert {"users", "jobs", "assets", "access_keys", "job_leases", "alembic_version"} <= _tables(db)
    assert "progress_message" in _columns(db, "jobs")
    con = sqlite3.connect(db)
    assert con.execute("select version_num from alembic_version").fetchone()[0] == "0003_session_expiry"
    con.close()


def test_legacy_create_all_database_is_stamped_and_upgraded(tmp_path):
    """A database created by the pre-Alembic code (create_all, no access_keys/job_leases) keeps its data."""
    db = str(tmp_path / "legacy.db")
    con = sqlite3.connect(db)
    con.executescript("""
        create table users (id varchar(36) primary key, email varchar(255) not null, password_hash varchar(255),
                            role varchar(50) not null, created_at datetime not null);
        create table projects (id varchar(36) primary key, owner_id varchar(36), title varchar(255) not null,
                               description text, created_at datetime not null, updated_at datetime not null);
        create table assets (id varchar(36) primary key, project_id varchar(36), owner_id varchar(36),
                             filename varchar(255) not null, storage_key varchar(512) not null,
                             media_type varchar(100) not null, size integer not null, checksum varchar(64),
                             metadata_json json, created_at datetime not null);
        create table jobs (id varchar(36) primary key, project_id varchar(36), user_id varchar(36),
                           tool varchar(100) not null, status varchar(50) not null, progress integer not null,
                           input_asset_ids json, params_json json, error_code varchar(100), error_message text,
                           created_at datetime not null, started_at datetime, completed_at datetime);
        create table job_outputs (id varchar(36) primary key, job_id varchar(36) not null,
                                  asset_id varchar(36) not null, output_type varchar(100) not null,
                                  created_at datetime not null);
        create table usage_events (id varchar(36) primary key, user_id varchar(36), job_id varchar(36),
                                   event_type varchar(100) not null, units integer not null, created_at datetime not null);
        insert into jobs values ('legacy-job', null, null, 'video_to_audio', 'succeeded', 100, '[]', '{}',
                                 null, null, '2026-10-01 10:00:00', null, null);
    """)
    con.commit()
    con.close()

    res = _run_python("from app.core.migrations import upgrade_database; upgrade_database()", db, tmp_path)
    assert res.returncode == 0, res.stderr
    assert {"access_keys", "job_leases", "alembic_version"} <= _tables(db)
    assert "progress_message" in _columns(db, "jobs")
    con = sqlite3.connect(db)
    assert con.execute("select status from jobs where id='legacy-job'").fetchone()[0] == "succeeded"
    con.close()


def test_models_and_migrations_are_in_sync(tmp_path):
    """Equivalent of `alembic check`: autogenerate must find no differences after upgrade."""
    db = str(tmp_path / "check.db")
    code = (
        "from app.core.migrations import upgrade_database; upgrade_database()\n"
        "from alembic.migration import MigrationContext\n"
        "from alembic.autogenerate import compare_metadata\n"
        "from app.core.database import engine, Base\n"
        "from app.models import entities\n"
        "with engine.connect() as c:\n"
        "    diff = compare_metadata(MigrationContext.configure(c), Base.metadata)\n"
        "print('DIFF', diff)\n"
    )
    res = _run_python(code, db, tmp_path)
    assert res.returncode == 0, res.stderr
    assert "DIFF []" in res.stdout, res.stdout


def test_migrations_downgrade_and_upgrade(tmp_path):
    db = str(tmp_path / "updown.db")
    code = (
        "from alembic import command\n"
        "from app.core.migrations import upgrade_database, alembic_config\n"
        "upgrade_database()\n"
        "command.downgrade(alembic_config(), '0001_baseline')\n"
        "command.upgrade(alembic_config(), 'head')\n"
    )
    res = _run_python(code, db, tmp_path)
    assert res.returncode == 0, res.stderr
    assert "progress_message" in _columns(db, "jobs")
