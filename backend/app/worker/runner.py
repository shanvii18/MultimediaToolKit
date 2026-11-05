import logging
import os
import socket
import threading
import time
import uuid
from typing import Optional

from app.core.config import settings
from app.core.database import SessionLocal
from app.services.job_queue import claim_next_job, heartbeat, recover_stale_jobs, wait_for_job_signal
from app.services.job_runner_service import job_runner_service

logger = logging.getLogger(__name__)


def default_worker_id(prefix: str = "worker") -> str:
    return f"{prefix}-{socket.gethostname()}-{os.getpid()}-{uuid.uuid4().hex[:6]}"


class JobWorker:
    """Polls the jobs table, executes one job at a time, and sends lease heartbeats."""

    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or default_worker_id()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_recovery = 0.0

    # ---- single iteration (used by tests and the loop) ----
    def recover(self) -> int:
        db = SessionLocal()
        try:
            return recover_stale_jobs(db)
        finally:
            db.close()

    def run_once(self) -> Optional[str]:
        """Claim and execute at most one job. Returns the job id processed, or None."""
        db = SessionLocal()
        try:
            job_id = claim_next_job(db, self.worker_id)
        finally:
            db.close()
        if job_id is None:
            return None

        beat_stop = threading.Event()
        beat = threading.Thread(target=self._heartbeat_loop, args=(job_id, beat_stop), daemon=True)
        beat.start()
        try:
            job_runner_service.process_job(job_id, already_claimed=True)
        except Exception:  # process_job records failures itself; never let the loop die
            logger.exception("Unexpected error while processing job %s", job_id)
        finally:
            beat_stop.set()
            beat.join(timeout=5)
        return job_id

    def drain(self, max_jobs: int = 100) -> int:
        processed = 0
        while processed < max_jobs and self.run_once():
            processed += 1
        return processed

    def _heartbeat_loop(self, job_id: str, stop: threading.Event) -> None:
        while not stop.wait(settings.WORKER_HEARTBEAT_SECONDS):
            db = SessionLocal()
            try:
                heartbeat(db, job_id, self.worker_id)
            except Exception:
                logger.exception("Heartbeat failed for job %s", job_id)
            finally:
                db.close()

    # ---- continuous loop ----
    def run_forever(self) -> None:
        logger.info("Job worker %s started (poll every %ss).", self.worker_id, settings.WORKER_POLL_INTERVAL_SECONDS)
        while not self._stop.is_set():
            try:
                if time.monotonic() - self._last_recovery > max(30, settings.WORKER_HEARTBEAT_SECONDS):
                    self.recover()
                    self._last_recovery = time.monotonic()
                if self.run_once() is None:
                    # Wake instantly on a Redis signal if enabled, otherwise poll the database.
                    if wait_for_job_signal(settings.WORKER_POLL_INTERVAL_SECONDS) is None:
                        self._stop.wait(settings.WORKER_POLL_INTERVAL_SECONDS)
            except Exception:
                logger.exception("Worker loop error; retrying shortly.")
                self._stop.wait(settings.WORKER_POLL_INTERVAL_SECONDS)
        logger.info("Job worker %s stopped.", self.worker_id)

    def start_in_background(self) -> None:
        self._thread = threading.Thread(target=self.run_forever, name="mtk-job-worker", daemon=True)
        self._thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=timeout)
