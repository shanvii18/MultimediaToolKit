"""
Test isolation: every test session uses a throw-away SQLite database and storage
directory, so running the suite never touches the developer's real data.

Environment variables must be set before any `app.*` module is imported, because
settings and the database engine are created at import time.
"""
import os
import shutil
import tempfile

_TEST_ROOT = tempfile.mkdtemp(prefix="mtk-tests-")
os.environ["ENVIRONMENT"] = "development"
# TEST_DATABASE_URL lets the same suite run against a real (disposable!) PostgreSQL database.
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{os.path.join(_TEST_ROOT, 'test.db')}"
os.environ["STORAGE_DIR"] = os.path.join(_TEST_ROOT, "storage")
os.environ["WORK_DIR"] = os.path.join(_TEST_ROOT, "work")
os.environ["STORAGE_BACKEND"] = "local"
os.environ["EMBEDDED_WORKER"] = "false"
os.environ["SIGNING_SECRET"] = "test-signing-secret-0123456789abcdef0123456789"
os.environ.pop("AUTH_MODE", None)

import pytest  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    try:
        from app.core.database import engine

        engine.dispose()
    except Exception:
        pass
    shutil.rmtree(_TEST_ROOT, ignore_errors=True)


@pytest.fixture
def worker():
    from app.worker.runner import JobWorker

    return JobWorker("test-worker")
