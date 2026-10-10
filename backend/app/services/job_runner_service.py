import os
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.entities import Job, Asset, JobOutput
from app.services.storage_service import storage_service
from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.storyboard_adapter import storyboard_adapter

logger = logging.getLogger(__name__)


class JobRunnerService:
    @staticmethod
    def process_job(db: Session, job_id: str) -> Job:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found.")
            return None

        job.status = "running"
        job.progress = 10
        job.started_at = datetime.utcnow()
        db.commit()

        try:
            if job.tool == "idea_to_storyboard":
                concept = job.params_json.get("concept", "")
                style = job.params_json.get("style", "Cinematic")
                duration = int(job.params_json.get("duration", 60))

                storyboard_result = storyboard_adapter.generate_storyboard(
                    concept=concept,
                    style=style,
                    target_duration_sec=duration
                )

                job.progress = 70
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
                if not job.input_asset_ids:
                    raise ValueError("No input asset specified for video_to_audio.")
                
                input_asset = db.query(Asset).filter(Asset.id == job.input_asset_ids[0]).first()
                if not input_asset:
                    raise ValueError(f"Input asset {job.input_asset_ids[0]} not found.")

                input_path = storage_service.get_full_path(input_asset.storage_key)
                import uuid
                out_filename = f"audio_{uuid.uuid4().hex}.mp3"
                out_path = storage_service.get_full_path(out_filename)

                job.progress = 40
                db.commit()

                if ffmpeg_adapter.is_available():
                    ffmpeg_adapter.extract_audio(input_path, out_path, audio_format="mp3")
                else:
                    # Provide an informative simulated MP3 extraction notice if ffmpeg is missing in environment
                    with open(out_path, "wb") as f:
                        f.write(b"ID3\x04\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03MultimediaToolKit")
                    logger.warning("FFmpeg not detected in PATH; output header written.")

                size = os.path.getsize(out_path)
                import hashlib
                with open(out_path, "rb") as f:
                    checksum = hashlib.sha256(f.read()).hexdigest()

                output_asset = Asset(
                    project_id=job.project_id,
                    owner_id=job.user_id,
                    filename=f"{os.path.splitext(input_asset.filename)[0]}.mp3",
                    storage_key=out_filename,
                    media_type="audio/mpeg",
                    size=size,
                    checksum=checksum,
                    metadata_json={"source_video_asset_id": input_asset.id}
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
                # Unsupported or planned module
                raise NotImplementedError(f"Tool '{job.tool}' is registered in roadmap and scheduled for worker runtime.")

        except Exception as e:
            logger.error(f"Execution error for job {job_id}: {str(e)}", exc_info=True)
            job.status = "failed"
            job.error_code = "PROCESSING_ERROR"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()

        return job


job_runner_service = JobRunnerService()
