import logging
import os
import shutil
import tempfile
from datetime import datetime
from typing import Optional

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.adapters.ffmpeg_adapter import FFmpegTimeoutError, UnsupportedAudioFormatError
from app.core.config import settings
from app.core.database import SessionLocal
from app.engines.base import ConversionError, JobContext
from app.engines.registry import get_spec
from app.models.entities import Job
from app.services.storage_service import storage_service

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"succeeded", "failed", "cancelled"}


def _error_code(exc: Exception) -> str:
    if isinstance(exc, ConversionError):
        return exc.code
    if isinstance(exc, FFmpegTimeoutError):
        return "TIMEOUT"
    if isinstance(exc, UnsupportedAudioFormatError):
        return "INVALID_INPUT"
    return "PROCESSING_ERROR"


def release_models() -> None:
    """Drop cached ML models so their memory can be reclaimed (small-RAM servers)."""
    import gc

    from app.adapters.tts_adapter import tts_adapter
    from app.adapters.whisper_adapter import whisper_adapter

    whisper_adapter._model = None
    whisper_adapter._model_size = None
    tts_adapter._kokoro = None
    gc.collect()


class JobRunnerService:
    @staticmethod
    def process_job(job_id: str, db: Optional[Session] = None, already_claimed: bool = False) -> Optional[Job]:
        """
        Executes a job through the conversion registry. Opens an independent SessionLocal if
        no session is provided.

        A queued job is claimed atomically (queued -> running) before execution, so the same
        job can never be executed twice concurrently. Workers that already claimed the job via
        the queue pass ``already_claimed=True``.
        """
        managed_db = False
        if db is None:
            db = SessionLocal()
            managed_db = True

        try:
            return JobRunnerService._execute(db, job_id, already_claimed)
        finally:
            if managed_db:
                db.close()

    @staticmethod
    def _claim(db: Session, job_id: str) -> bool:
        res = db.execute(
            update(Job)
            .where(Job.id == job_id, Job.status == "queued")
            .values(status="running", progress=10, started_at=datetime.utcnow())
        )
        db.commit()
        return res.rowcount == 1

    @staticmethod
    def _execute(db: Session, job_id: str, already_claimed: bool = False) -> Optional[Job]:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found.")
            return None

        # Idempotency guard: never re-run a finished job
        if job.status in TERMINAL_STATUSES:
            logger.info(f"Job {job_id} is already {job.status}; skipping duplicate execution.")
            return job

        if not already_claimed:
            if not JobRunnerService._claim(db, job_id):
                logger.info(f"Job {job_id} is not claimable (status={job.status}); skipping.")
                db.refresh(job)
                return job
        db.refresh(job)

        os.makedirs(settings.WORK_DIR, exist_ok=True)
        work_dir = tempfile.mkdtemp(prefix=f"job_{job.id[:8]}_", dir=settings.WORK_DIR)
        ctx = JobContext(db, job, work_dir, storage_service)
        try:
            spec = get_spec(job.tool)
            if spec is None or spec.run is None:
                raise ConversionError(f"Tool '{job.tool}' is not available.", code="UNKNOWN_TOOL")

            spec.run(ctx)

            if not ctx.outputs:
                raise RuntimeError("The conversion finished without producing any output.")
            job.status = "succeeded"
            job.progress = 100
            job.progress_message = "Completed"
            job.completed_at = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.error(f"Execution error for job {job_id}: {str(e)}", exc_info=not isinstance(e, ConversionError))
            db.rollback()
            ctx.cleanup_failed_outputs()
            job = db.query(Job).filter(Job.id == job_id).first()
            job.status = "failed"
            job.error_code = _error_code(e)
            job.error_message = str(e)
            job.progress_message = "Failed"
            job.completed_at = datetime.utcnow()
            try:
                db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to commit failed status for job {job_id}: {commit_err}")
                db.rollback()
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
            if not settings.KEEP_MODELS_LOADED:
                release_models()

        return job


job_runner_service = JobRunnerService()
