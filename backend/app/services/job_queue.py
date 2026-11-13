"""
Durable, database-backed job queue.

The ``jobs`` table *is* the queue: a job is persisted as ``queued`` by the API and
claimed atomically by a worker. A ``job_leases`` row records which worker holds it
and when it last sent a heartbeat. Jobs whose worker disappeared (restart, deploy,
free-tier sleep, crash) are re-queued up to ``JOB_MAX_ATTEMPTS`` and then failed with
``WORKER_LOST`` -- they can no longer stay "running" forever.

Works on PostgreSQL (``FOR UPDATE SKIP LOCKED``) and SQLite (conditional UPDATE).
"""
import logging
import threading
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import Job, JobLease

logger = logging.getLogger(__name__)


REDIS_WAKE_KEY = "mtk:jobs:wake"
_redis_client = None


def _redis():
    """Optional Redis client for instant worker wake-ups (None when disabled or unreachable)."""
    global _redis_client
    if not settings.QUEUE_NOTIFY_REDIS:
        return None
    if _redis_client is None:
        try:
            import redis

            client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=2, socket_timeout=5)
            client.ping()
            _redis_client = client
        except Exception as e:  # noqa: BLE001 - Redis is an optimisation, never a dependency
            logger.warning("Redis wake-up queue unavailable (%s); workers fall back to polling.", type(e).__name__)
            return None
    return _redis_client


# In-process wake-up for the embedded worker (API and worker share a process on small deployments):
# a new job starts immediately instead of waiting for the next database poll.
LOCAL_WAKE = threading.Event()


def notify_new_job(job_id: str, client=None) -> bool:
    """Push a wake-up signal so an idle worker claims the job immediately. The DB stays the source of truth."""
    LOCAL_WAKE.set()
    client = client or _redis()
    if client is None:
        return False
    try:
        client.lpush(REDIS_WAKE_KEY, job_id)
        client.ltrim(REDIS_WAKE_KEY, 0, 999)
        return True
    except Exception:  # noqa: BLE001
        return False


def wait_for_job_signal(timeout_seconds: float, client=None) -> Optional[bool]:
    """
    Block until a wake-up signal arrives or the timeout passes.
    Returns True (signalled), False (timed out) or None (Redis not in use -> caller should poll).
    """
    client = client or _redis()
    if client is None:
        return None
    try:
        return client.blpop([REDIS_WAKE_KEY], timeout=max(1, int(timeout_seconds))) is not None
    except Exception:  # noqa: BLE001
        return None


def claim_next_job(db: Session, worker_id: str) -> Optional[str]:
    """Atomically move the oldest queued job to running and lease it to ``worker_id``."""
    for _ in range(5):  # retry a few times if another worker wins the race
        candidate = (
            db.query(Job.id)
            .filter(Job.status == "queued")
            .order_by(Job.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=True)
            .first()
        )
        if candidate is None:
            db.commit()
            return None

        job_id = candidate[0]
        now = datetime.utcnow()
        res = db.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == "queued")
            .values(status="running", progress=10, started_at=now)
        )
        if res.rowcount != 1:
            db.rollback()
            continue

        lease = db.get(JobLease, job_id)
        if lease is None:
            lease = JobLease(job_id=job_id, worker_id=worker_id, attempts=0)
            db.add(lease)
        lease.worker_id = worker_id
        lease.attempts = (lease.attempts or 0) + 1
        lease.claimed_at = now
        lease.heartbeat_at = now
        db.commit()
        return job_id
    return None


def heartbeat(db: Session, job_id: str, worker_id: str) -> None:
    db.execute(
        update(JobLease)
        .where(JobLease.job_id == job_id, JobLease.worker_id == worker_id)
        .values(heartbeat_at=datetime.utcnow())
    )
    db.commit()


def recover_stale_jobs(db: Session, now: Optional[datetime] = None) -> int:
    """
    Re-queue (or fail) running jobs whose worker stopped sending heartbeats.
    Also covers legacy jobs left 'running' by the old in-process BackgroundTasks runner.
    Returns the number of jobs recovered.
    """
    now = now or datetime.utcnow()
    cutoff = now - timedelta(seconds=settings.JOB_STALE_AFTER_SECONDS)
    recovered = 0

    running = db.query(Job).filter(Job.status == "running").all()
    for job in running:
        lease = db.get(JobLease, job.id)
        last_seen = lease.heartbeat_at if lease else job.started_at
        if last_seen is not None and last_seen >= cutoff:
            continue

        attempts = lease.attempts if lease else 1
        if attempts < settings.JOB_MAX_ATTEMPTS:
            job.status = "queued"
            job.progress = 0
            job.started_at = None
            logger.warning("Re-queuing abandoned job %s (attempt %s of %s).", job.id, attempts, settings.JOB_MAX_ATTEMPTS)
        else:
            job.status = "failed"
            job.error_code = "WORKER_LOST"
            job.error_message = (
                "Processing was interrupted (server restart or worker crash) and the retry limit was reached. "
                "Please submit the job again."
            )
            job.completed_at = now
            logger.error("Job %s abandoned after %s attempts; marked failed.", job.id, attempts)
        recovered += 1

    db.commit()
    return recovered
