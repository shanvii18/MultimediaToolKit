"""Audio/Video pipelines: Video→Audio, Audio→Text, Video→Text."""
import os
import uuid

from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.engines.base import ConversionError, JobContext, stem_of
from app.engines.pipelines.common import transcribe_media, save_transcript_outputs


def video_to_audio(ctx: JobContext) -> None:
    """Extract the soundtrack with FFmpeg, re-encoded for the chosen container (existing P1 feature)."""
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    fmt = ctx.params.get("audio_format", "mp3")
    spec = ffmpeg_adapter.audio_format_spec(fmt)

    ctx.progress(30, "Extracting audio track")
    out_path = ctx.tmp(f"audio_{uuid.uuid4().hex}{spec.extension}")
    ffmpeg_adapter.extract_audio(path, out_path, audio_format=fmt)

    ctx.progress(85, "Saving audio")
    ctx.add_output(out_path, f"{os.path.splitext(source.filename)[0]}_extracted{spec.extension}", f"audio_{fmt}", {
        "source_video_asset_id": source.id,
        "extraction_format": fmt,
        "codec": spec.codec,
        "engine": "FFmpeg",
    })


def audio_to_text(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    transcript = transcribe_media(ctx, path, 10, 90)
    ctx.progress(92, "Writing transcript files")
    save_transcript_outputs(ctx, transcript, stem_of(source.filename, "audio"),
                            {"source_asset_id": source.id})


def video_to_text(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    transcript = transcribe_media(
        ctx, path, 10, 90,
        require_audio_message="This video has no audio track, so there is no speech to transcribe.",
    )
    ctx.progress(92, "Writing transcript files")
    save_transcript_outputs(ctx, transcript, stem_of(source.filename, "video"),
                            {"source_asset_id": source.id, "pipeline": "FFmpeg audio extraction → Whisper"})


def require_audio_track(path: str) -> None:
    if not ffmpeg_adapter.probe(path).has_audio:
        raise ConversionError("This file has no audio track.", code="NO_AUDIO")
