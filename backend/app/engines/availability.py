"""Runtime availability of each processing engine on *this* server (cached briefly)."""
import time
from typing import Dict, Optional

from app.adapters.ai_provider import ai_provider
from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.ocr_adapter import ocr_adapter
from app.adapters.tts_adapter import tts_adapter
from app.adapters.whisper_adapter import whisper_adapter

ENGINE_LABELS = {
    "ffmpeg": "FFmpeg",
    "whisper": "faster-whisper (speech recognition)",
    "kokoro": "Kokoro-82M (text-to-speech)",
    "tesseract": "Tesseract (OCR)",
    "pillow": "Pillow (images)",
    "ai_image": "Hosted AI image generation",
    "ai_caption": "Hosted AI image description",
}

_CACHE_SECONDS = 30.0
_cache: Dict[str, Optional[str]] = {}
_cache_time = 0.0


def _check_ffmpeg() -> Optional[str]:
    return None if ffmpeg_adapter.is_available() else "FFmpeg is not installed on this server."


def _check_pillow() -> Optional[str]:
    try:
        import PIL  # noqa: F401
        return None
    except ImportError:
        return "Pillow is not installed on this server."


_CHECKS = {
    "ffmpeg": _check_ffmpeg,
    "whisper": whisper_adapter.availability,
    "kokoro": tts_adapter.availability,
    "tesseract": ocr_adapter.availability,
    "pillow": _check_pillow,
    "ai_image": ai_provider.availability,
    "ai_caption": ai_provider.availability,
}


def engine_status(refresh: bool = False) -> Dict[str, Optional[str]]:
    """Map engine -> None (available) or a reason string."""
    global _cache, _cache_time
    if refresh or not _cache or time.monotonic() - _cache_time > _CACHE_SECONDS:
        _cache = {name: check() for name, check in _CHECKS.items()}
        _cache_time = time.monotonic()
    return dict(_cache)


def unavailable_reason(engines) -> Optional[str]:
    status = engine_status()
    for name in engines:
        reason = status.get(name, f"Unknown engine '{name}'.")
        if reason:
            return reason
    return None


def reset_cache() -> None:
    global _cache, _cache_time
    _cache, _cache_time = {}, 0.0
