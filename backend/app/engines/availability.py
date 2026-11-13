"""Runtime availability of each processing engine on *this* server (cached briefly)."""
import time
from typing import Dict, Optional, Tuple

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
    "ai_img2img": "Hosted AI image restyle (img2img)",
}

AI_ENGINES = ("ai_image", "ai_caption", "ai_img2img")
LOCAL_AI_ENGINES = ("whisper", "kokoro")

_CACHE_SECONDS = 30.0
_cache: Dict[str, Optional[str]] = {}
_cache_time = 0.0
# Installed programs/models do not disappear while the server runs. Once found, they are never probed
# again: re-running `ffmpeg -version` on a 0.1-CPU server busy with a job timed out and wrongly reported
# "FFmpeg is not installed" (and slowed every request). Config-only AI checks are re-evaluated.
_STICKY = ("ffmpeg", "whisper", "kokoro", "tesseract", "pillow")
_found: Dict[str, object] = {}          # engine -> the check function that succeeded


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
    "ai_img2img": ai_provider.img2img_availability,
}


def engine_status(refresh: bool = False) -> Dict[str, Optional[str]]:
    """Map engine -> None (available) or a reason string."""
    global _cache, _cache_time
    if refresh or not _cache or time.monotonic() - _cache_time > _CACHE_SECONDS:
        fresh = {}
        for name, check in _CHECKS.items():
            if name in _STICKY and _found.get(name) is check and not refresh:
                fresh[name] = None
                continue
            fresh[name] = check()
            if name in _STICKY and fresh[name] is None:
                _found[name] = check
        _cache = fresh
        _cache_time = time.monotonic()
    return dict(_cache)


def unavailable_reason(engines) -> Optional[str]:
    status = engine_status()
    for name in engines:
        reason = status.get(name, f"Unknown engine '{name}'.")
        if reason:
            return reason
    return None


def engine_state(name: str) -> Tuple[str, Optional[str]]:
    """(state, reason): available | needs_config | temporarily_unavailable | unavailable."""
    reason = engine_status().get(name, f"Unknown engine '{name}'.")
    if name in AI_ENGINES:
        if reason:
            return "needs_config", reason
        issue = ai_provider.runtime_issue()
        if issue:
            return "temporarily_unavailable", issue
        return "available", None
    return ("unavailable", reason) if reason else ("available", None)


_SEVERITY = {"available": 0, "temporarily_unavailable": 1, "needs_config": 2, "unavailable": 3}


def engines_state(engines) -> Tuple[str, Optional[str]]:
    """Worst state across a mode's engines."""
    state, reason = "available", None
    for name in engines:
        s, r = engine_state(name)
        if _SEVERITY[s] > _SEVERITY[state]:
            state, reason = s, r
    return state, reason


def reset_cache() -> None:
    global _cache, _cache_time
    _cache, _cache_time = {}, 0.0
