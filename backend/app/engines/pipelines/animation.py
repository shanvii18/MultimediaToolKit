"""
Animation→Text and Animation→Audio.

Animations (GIF / animated WebP / short MP4-WebM-MOV clips) are handled honestly:
- speech in an audio track is transcribed with Whisper;
- text visible in the frames is read with Tesseract OCR;
- *visual description* of what happens in a silent animation needs a vision-language
  model and is Coming Soon -- if neither speech nor text exists, the job fails clearly.
"""
import json
import uuid

from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.image_adapter import is_animated_image
from app.engines.availability import engine_status
from app.engines.base import ConversionError, JobContext, stem_of
from app.engines.pipelines.common import ocr_frames, sample_frames, speak_text, transcribe_media

FRAME_SAMPLES = 8


def _has_audio(path: str) -> bool:
    if is_animated_image(path):
        return False  # GIF / WebP cannot carry audio
    return ffmpeg_adapter.probe(path).has_audio


def animation_to_text(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "animation")
    status = engine_status()
    report = {"source_asset_id": source.id, "speech": None, "on_screen_text": [], "notes": []}

    ctx.progress(5, "Inspecting animation")
    if _has_audio(path):
        if status.get("whisper"):
            report["notes"].append(f"Speech skipped: {status['whisper']}")
        else:
            transcript = transcribe_media(ctx, path, 8, 55)
            if transcript.segments:
                report["speech"] = {"language": transcript.language, "text": transcript.text,
                                    "segments": [{"start": s.start, "end": s.end, "text": s.text}
                                                 for s in transcript.segments]}
    else:
        report["notes"].append("No audio track (no speech to transcribe).")

    if status.get("tesseract"):
        report["notes"].append(f"On-screen text skipped: {status['tesseract']}")
    else:
        ctx.progress(58, "Sampling frames")
        frames = sample_frames(ctx, path, FRAME_SAMPLES)
        report["on_screen_text"] = ocr_frames(ctx, frames, 60, 92)
        report["frames_sampled"] = len(frames)

    if not report["speech"] and not report["on_screen_text"]:
        raise ConversionError(
            "No speech or readable on-screen text was found in this animation. "
            "Describing purely visual animations is coming soon.", code="NO_CONTENT")

    lines = []
    if report["on_screen_text"]:
        lines.append("ON-SCREEN TEXT")
        for block in report["on_screen_text"]:
            lines.append(f"[{block['timestamp']:.2f}s] {block['text']}")
        lines.append("")
    if report["speech"]:
        lines.append("SPEECH TRANSCRIPT")
        lines.append(report["speech"]["text"])
    text = "\n".join(lines).strip() + "\n"

    ctx.progress(95, "Saving text")
    ctx.add_text_output(text, f"{stem}_text.txt", "animation_txt", {
        "engine": "Whisper + Tesseract", "preview_text": text[:2000], "source_asset_id": source.id,
    })
    ctx.add_text_output(json.dumps(report, indent=2, ensure_ascii=False), f"{stem}_analysis.json",
                        "animation_json", {"engine": "Whisper + Tesseract"})


def animation_to_audio(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "animation")

    if ctx.mode == "soundtrack":
        ctx.progress(10, "Checking for an audio track")
        if not _has_audio(path):
            raise ConversionError(
                "This animation has no audio track (GIF and WebP never do). "
                "Try the 'Read on-screen text aloud' mode instead.", code="NO_AUDIO")
        fmt = ctx.params.get("audio_format", "mp3")
        spec = ffmpeg_adapter.audio_format_spec(fmt)
        out = ctx.tmp(f"soundtrack_{uuid.uuid4().hex}{spec.extension}")
        ctx.progress(30, "Extracting soundtrack")
        ffmpeg_adapter.extract_audio(path, out, audio_format=fmt)
        ctx.add_output(out, f"{stem}_soundtrack{spec.extension}", f"audio_{fmt}", {
            "engine": "FFmpeg", "mode": "soundtrack", "codec": spec.codec, "source_asset_id": source.id,
        })
        return

    # read_text: OCR sampled frames, then speak the text in on-screen order
    ctx.progress(5, "Sampling frames")
    frames = sample_frames(ctx, path, FRAME_SAMPLES)
    blocks = ocr_frames(ctx, frames, 10, 40)
    if not blocks:
        raise ConversionError("No readable on-screen text was found to read aloud.", code="NO_TEXT_FOUND")
    text = "\n".join(b["text"] for b in blocks)
    ctx.add_text_output(text + "\n", f"{stem}_read_text.txt", "ocr_txt", {
        "engine": "Tesseract OCR", "preview_text": text[:2000],
    })
    speak_text(ctx, text, f"{stem}_read_aloud", 45, 98, {
        "pipeline": "Frame sampling → Tesseract OCR → Kokoro TTS", "mode": "read_text", "source_asset_id": source.id,
    })
