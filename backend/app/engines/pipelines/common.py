"""Reusable pipeline steps shared by several conversions."""
import json
import os
from typing import Dict, List, Optional

from app.adapters.ffmpeg_adapter import ffmpeg_adapter, AUDIO_FORMATS
from app.adapters.image_adapter import is_animated_image, sample_animation_frames, open_image
from app.adapters.ocr_adapter import ocr_adapter
from app.adapters.tts_adapter import tts_adapter
from app.adapters.whisper_adapter import whisper_adapter, Transcript, to_srt, to_vtt, to_json
from app.core.config import settings
from app.engines.base import ConversionError, JobContext


def free_models() -> None:
    """Release Whisper/Kokoro before FFmpeg work when KEEP_MODELS_LOADED=false (512 MB servers)."""
    from app.services.job_runner_service import free_models_if_configured
    free_models_if_configured()


# ---------------- speech recognition ----------------
def transcribe_media(ctx: JobContext, media_path: str, start: float, end: float,
                     require_audio_message: str = "This file has no audio track to transcribe.") -> Transcript:
    """Decode any audio/video file to 16 kHz WAV and transcribe it with Whisper."""
    info = ffmpeg_adapter.probe(media_path)
    if not info.has_audio:
        raise ConversionError(require_audio_message, code="NO_AUDIO")
    if info.duration and info.duration > settings.MAX_TRANSCRIBE_SECONDS:
        raise ConversionError(
            f"The media is {info.duration / 60:.0f} minutes long; the limit is "
            f"{settings.MAX_TRANSCRIBE_SECONDS // 60} minutes.", code="INPUT_TOO_LONG")

    ctx.progress(start, "Preparing audio")
    wav = ctx.tmp("speech_16k.wav")
    ffmpeg_adapter.to_wav_16k_mono(media_path, wav)

    model = ctx.params.get("model") or settings.WHISPER_DEFAULT_MODEL
    ctx.progress(start + 2, f"Loading speech model ({model})")
    transcript = whisper_adapter.transcribe(
        wav, model_size=model, language=ctx.params.get("language", "auto"),
        progress=ctx.sub_progress(start + 5, end, "Transcribing speech"),
    )
    free_models()
    return transcript


def save_transcript_outputs(ctx: JobContext, transcript: Transcript, stem: str, extra: Optional[Dict] = None) -> None:
    if not transcript.segments:
        raise ConversionError("No speech was detected in the audio.", code="NO_SPEECH")
    meta = {
        "engine": transcript.engine or f"faster-whisper/{transcript.model}",
        "language": transcript.language,
        "duration_seconds": round(transcript.duration, 2),
        "preview_text": transcript.text[:2000],
        **(extra or {}),
    }
    ctx.add_text_output(transcript.text + "\n", f"{stem}_transcript.txt", "transcript_txt", meta)
    ctx.add_text_output(to_srt(transcript), f"{stem}_subtitles.srt", "subtitles_srt", {"engine": meta["engine"]})
    ctx.add_text_output(to_vtt(transcript), f"{stem}_subtitles.vtt", "subtitles_vtt", {"engine": meta["engine"]})
    ctx.add_text_output(json.dumps({**to_json(transcript), **(extra or {})}, indent=2, ensure_ascii=False),
                        f"{stem}_transcript.json", "transcript_json", {"engine": meta["engine"]})


# ---------------- speech synthesis ----------------
def speak_text(ctx: JobContext, text: str, stem: str, start: float, end: float,
               extra_meta: Optional[Dict] = None) -> None:
    """Synthesize ``text`` (Cloudflare speech, or local Kokoro as fallback) in the requested audio format."""
    text = (text or "").strip()
    if not text:
        raise ConversionError("There is no text to speak.", code="NO_TEXT")
    if len(text) > settings.MAX_TEXT_CHARS:
        raise ConversionError(f"Text is too long ({len(text)} characters; limit {settings.MAX_TEXT_CHARS}).",
                              code="INPUT_TOO_LONG")

    voice = ctx.params.get("voice", "af_heart")
    speed = float(ctx.params.get("speed", 1.0))
    fmt = ctx.params.get("audio_format", "mp3")
    if fmt not in AUDIO_FORMATS:
        raise ConversionError(f"Unsupported audio format '{fmt}'.")

    ctx.progress(start, "Generating speech")
    wav = ctx.tmp("speech.wav")
    duration = tts_adapter.synthesize_to_wav(
        text, wav, voice=voice, speed=speed,
        progress=ctx.sub_progress(start + 3, end - 5, "Synthesizing speech"),
    )
    free_models()
    spec = AUDIO_FORMATS[fmt]
    if fmt == "wav":
        final = wav
    else:
        ctx.progress(end - 4, f"Encoding {fmt.upper()}")
        final = ctx.tmp(f"speech{spec.extension}")
        ffmpeg_adapter.encode_audio(wav, final, fmt)
    ctx.add_output(final, f"{stem}{spec.extension}", f"audio_{fmt}", {
        "engine": tts_adapter.last_engine,
        "voice": voice,
        "speed": speed,
        "duration_seconds": round(duration, 2),
        "characters": len(text),
        **(extra_meta or {}),
    })


# ---------------- OCR ----------------
def ocr_image_file(ctx: JobContext, path: str):
    img = open_image(path)
    if getattr(img, "is_animated", False):
        img.seek(0)
    language = ctx.params.get("ocr_language", "eng")
    _require_ocr_language(language)
    return ocr_adapter.ocr(img, language=language, layout=ctx.params.get("layout", "auto"))


def _require_ocr_language(language: str) -> None:
    installed = ocr_adapter.languages()
    if installed and language not in installed:
        raise ConversionError(
            f"OCR language '{language}' is not installed on this server (installed: {', '.join(installed)}).",
            code="ENGINE_UNAVAILABLE")


def sample_frames(ctx: JobContext, path: str, count: int) -> List:
    """Return [(timestamp, PIL image)] for GIF/WebP (Pillow) or any video container (FFmpeg)."""
    if is_animated_image(path):
        frames, _, _ = sample_animation_frames(path, count)
        return frames
    info = ffmpeg_adapter.probe(path)
    if not info.has_video:
        raise ConversionError("The file has no visual frames.", code="INVALID_INPUT")
    duration = info.duration or 0.0
    stamps = [round((i + 0.5) * duration / count, 3) for i in range(count)] if duration > 0 else [0.0]
    frames = []
    for i, ts in enumerate(stamps):
        out = ctx.tmp(f"frame_{i:03d}.png")
        ffmpeg_adapter.extract_frame(path, ts, out)
        frames.append((ts, open_image(out).convert("RGB")))
    return frames


def ocr_frames(ctx: JobContext, frames: List, start: float, end: float) -> List[Dict]:
    """OCR each sampled frame; return de-duplicated text blocks with their first timestamp."""
    language = ctx.params.get("ocr_language", "eng")
    _require_ocr_language(language)
    seen = set()
    blocks = []
    report = ctx.sub_progress(start, end, "Reading on-screen text")
    for i, (ts, frame) in enumerate(frames):
        result = ocr_adapter.ocr(frame, language=language, layout="sparse")
        normalized = " ".join(result.text.split()).lower()
        alnum = sum(ch.isalnum() for ch in normalized)
        confident = result.mean_confidence is None or result.mean_confidence >= 45
        # Skip OCR noise from frames without real text (stray glyphs, low confidence).
        if result.text and alnum >= 3 and confident and normalized not in seen:
            seen.add(normalized)
            blocks.append({"timestamp": ts, "text": result.text, "confidence": result.mean_confidence})
        report((i + 1) / max(1, len(frames)))
    return blocks


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path
