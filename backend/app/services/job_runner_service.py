import os
import uuid
import json
import hashlib
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.entities import Job, Asset, JobOutput
from app.services.storage_service import storage_service
from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.storyboard_adapter import storyboard_adapter

logger = logging.getLogger(__name__)


class JobRunnerService:
    @staticmethod
    def process_job(job_id: str, db: Optional[Session] = None) -> Optional[Job]:
        """
        Executes an asynchronous job. Opens an independent SessionLocal if no session is provided,
        preventing DetachedInstanceError or closed session issues from FastAPI BackgroundTasks.
        """
        managed_db = False
        if db is None:
            db = SessionLocal()
            managed_db = True

        try:
            return JobRunnerService._execute(db, job_id)
        finally:
            if managed_db:
                db.close()

    @staticmethod
    def _execute(db: Session, job_id: str) -> Optional[Job]:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found.")
            return None

        # Idempotency guard: prevent duplicate execution if already finished
        if job.status == "succeeded":
            logger.info(f"Job {job_id} has already succeeded; skipping duplicate execution.")
            return job

        job.status = "running"
        job.progress = 10
        job.started_at = datetime.utcnow()
        db.commit()

        try:
            if job.tool == "idea_to_storyboard":
                concept = (job.params_json or {}).get("concept", "")
                style = (job.params_json or {}).get("style", "Cinematic")
                duration = int((job.params_json or {}).get("duration", 60))

                job.progress = 25
                db.commit()

                storyboard_result = storyboard_adapter.generate_storyboard(
                    concept=concept,
                    style=style,
                    target_duration_sec=duration
                )

                job.progress = 75
                db.commit()

                # Save storyboard as formatted JSON asset
                output_bytes = json.dumps(storyboard_result, indent=2).encode("utf-8")
                storage_key, size, checksum = storage_service.write_output_file(output_bytes, extension=".json")

                output_asset = Asset(
                    project_id=job.project_id,
                    owner_id=job.user_id,
                    filename=f"storyboard_{job.id[:8]}.json",
                    storage_key=storage_key,
                    media_type="application/json",
                    size=size,
                    checksum=checksum,
                    metadata_json={"storyboard_data": storyboard_result}
                )
                db.add(output_asset)
                db.flush()

                job_output = JobOutput(
                    job_id=job.id,
                    asset_id=output_asset.id,
                    output_type="storyboard_json"
                )
                db.add(job_output)

                job.status = "succeeded"
                job.progress = 100
                job.completed_at = datetime.utcnow()
                db.commit()

            elif job.tool == "video_to_audio":
                if not job.input_asset_ids or len(job.input_asset_ids) == 0:
                    raise ValueError("No input asset specified for video_to_audio.")

                input_asset = db.query(Asset).filter(Asset.id == job.input_asset_ids[0]).first()
                if not input_asset:
                    raise ValueError(f"Input asset '{job.input_asset_ids[0]}' was not found in storage.")

                input_path = storage_service.get_full_path(input_asset.storage_key)
                if not os.path.exists(input_path):
                    raise FileNotFoundError(f"Source video file is missing on disk: {input_path}")

                if not ffmpeg_adapter.is_available():
                    raise RuntimeError(
                        "FFmpeg is not installed or not available on the system PATH. "
                        "Media extraction requires FFmpeg to separate and encode audio streams."
                    )

                out_filename = f"audio_{uuid.uuid4().hex}.mp3"
                out_path = storage_service.get_full_path(out_filename)

                job.progress = 30
                db.commit()

                # Execute real audio extraction
                audio_format = (job.params_json or {}).get("audio_format", "mp3")
                ffmpeg_adapter.extract_audio(input_path, out_path, audio_format=audio_format)

                job.progress = 85
                db.commit()

                if not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
                    raise RuntimeError("Audio extraction failed to produce a valid output file.")

                size = os.path.getsize(out_path)
                with open(out_path, "rb") as f:
                    checksum = hashlib.sha256(f.read()).hexdigest()

                source_stem = os.path.splitext(input_asset.filename)[0]
                output_filename = f"{source_stem}_extracted.mp3"

                output_asset = Asset(
                    project_id=job.project_id,
                    owner_id=job.user_id,
                    filename=output_filename,
                    storage_key=out_filename,
                    media_type="audio/mpeg",
                    size=size,
                    checksum=checksum,
                    metadata_json={
                        "source_video_asset_id": input_asset.id,
                        "extraction_format": "mp3",
                        "engine": "FFmpeg"
                    }
                )
                db.add(output_asset)
                db.flush()

                job_output = JobOutput(
                    job_id=job.id,
                    asset_id=output_asset.id,
                    output_type="audio_mp3"
                )
                db.add(job_output)

                job.status = "succeeded"
                job.progress = 100
                job.completed_at = datetime.utcnow()
                db.commit()

            else:
                raise NotImplementedError(
                    f"Tool '{job.tool}' is registered in the blueprint roadmap and scheduled for worker runtime."
                )

        except Exception as e:
            logger.error(f"Execution error for job {job_id}: {str(e)}", exc_info=True)
            job.status = "failed"
            job.error_code = "PROCESSING_ERROR"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            try:
                db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to commit failed status for job {job_id}: {commit_err}")
                db.rollback()

        return job


job_runner_service = JobRunnerService()
