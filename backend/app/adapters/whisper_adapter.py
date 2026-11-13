"""
Speech-to-text with faster-whisper (CTranslate2, MIT) and OpenAI Whisper weights (MIT).

CPU-only, int8 quantised. One model is kept in memory at a time to respect small
machines (8 GB laptop / 512 MB-2 GB servers). Weights live in MODEL_CACHE_DIR/whisper.
"""
import importlib.util
import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

WHISPER_MODELS = {
    "tiny": "Tiny: fastest, lowest accuracy (~75 MB)",
    "base": "Base: balanced (~145 MB)",
    "small": "Small: more accurate, ~3x slower (~480 MB)",
}

# Whisper language codes offered in the UI ("auto" = detect).
WHISPER_LANGUAGES = {
    "auto": "Detect automatically",
    "en": "English", "hi": "Hindi", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "ja": "Japanese", "ko": "Korean",
    "zh": "Chinese", "ar": "Arabic", "bn": "Bengali", "ta": "Tamil", "te": "Telugu",
    "mr": "Marathi", "ur": "Urdu", "tr": "Turkish", "nl": "Dutch", "pl": "Polish",
}


@dataclass
class Segment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    language: str
    language_probability: float
    duration: float
    model: str
    segments: List[Segment] = field(default_factory=list)
    engine: str = ""                 # human-readable engine that actually produced the transcript

    @property
    def text(self) -> str:
        return "\n".join(s.text for s in self.segments).strip()


class WhisperAdapter:
    engine_name = "whisper"

    def __init__(self):
        self._lock = threading.Lock()
        self._model = None
        self._model_size: Optional[str] = None

    @property
    def download_root(self) -> str:
        return os.path.join(settings.MODEL_CACHE_DIR, "whisper")

    def _is_cached(self, size: str) -> bool:
        snap = os.path.join(self.download_root, f"models--Systran--faster-whisper-{size}", "snapshots")
        return os.path.isdir(snap) and any(os.listdir(snap))

    def availability(self) -> Optional[str]:
        """None when usable, otherwise a human-readable reason."""
        if importlib.util.find_spec("faster_whisper") is None:
            return "Speech recognition engine (faster-whisper) is not installed on this server."
        if not settings.AUTO_DOWNLOAD_MODELS and not self._is_cached(settings.WHISPER_DEFAULT_MODEL):
            return "Speech recognition model is not downloaded on this server."
        return None

    def _load(self, size: str):
        if size not in WHISPER_MODELS:
            raise ValueError(f"Unknown Whisper model '{size}'.")
        if self._model is not None and self._model_size == size:
            return self._model
        from faster_whisper import WhisperModel

        self._model = None  # free the previous model before loading another one
        logger.info("Loading Whisper model '%s' (cpu, %s)...", size, settings.WHISPER_COMPUTE_TYPE)
        os.makedirs(self.download_root, exist_ok=True)
        self._model = WhisperModel(
            size,
            device="cpu",
            compute_type=settings.WHISPER_COMPUTE_TYPE,
            cpu_threads=settings.WHISPER_CPU_THREADS,
            download_root=self.download_root,
            local_files_only=not settings.AUTO_DOWNLOAD_MODELS,
        )
        self._model_size = size
        return self._model

    def transcribe(
        self,
        wav_path: str,
        model_size: Optional[str] = None,
        language: Optional[str] = None,
        progress: Optional[Callable[[float], None]] = None,
    ) -> Transcript:
        size = model_size or settings.WHISPER_DEFAULT_MODEL
        lang = None if language in (None, "", "auto") else language
        cloud = self._transcribe_cloud(wav_path, lang)
        if cloud is not None:
            if progress:
                progress(1.0)
            return cloud
        with self._lock:  # one transcription at a time per process (CPU-bound)
            model = self._load(size)
            segments_iter, info = model.transcribe(
                wav_path, language=lang, beam_size=5, vad_filter=True, condition_on_previous_text=False,
            )
            duration = float(info.duration or 0.0)
            segments: List[Segment] = []
            for seg in segments_iter:  # generator: decoding happens while iterating
                text = (seg.text or "").strip()
                if text:
                    segments.append(Segment(start=float(seg.start), end=float(seg.end), text=text))
                if progress and duration > 0:
                    progress(min(1.0, float(seg.end) / duration))
        return Transcript(
            language=info.language,
            language_probability=float(info.language_probability or 0.0),
            duration=duration,
            model=size,
            segments=segments,
            engine=f"faster-whisper/{size} (on this server)",
        )

    @staticmethod
    def _transcribe_cloud(wav_path: str, language: Optional[str]) -> Optional[Transcript]:
        """Whisper large-v3-turbo on Cloudflare (seconds instead of minutes on a 0.1-CPU server).
        Returns None so the caller falls back to local faster-whisper on any problem."""
        from app.adapters.ai_provider import ai_provider

        if not ai_provider.speech_enabled():
            return None
        import tempfile

        from app.adapters.ffmpeg_adapter import ffmpeg_adapter

        try:
            with tempfile.TemporaryDirectory(prefix="mtk-asr-") as tmp:
                mp3 = os.path.join(tmp, "speech.mp3")       # ~8x smaller upload than 16 kHz WAV
                ffmpeg_adapter.run_ffmpeg(["-i", wav_path, "-ac", "1", "-ar", "16000", "-c:a", "libmp3lame",
                                           "-b:a", "48k", mp3], mp3)
                with open(mp3, "rb") as f:
                    result = ai_provider.transcribe(f.read(), language)
        except Exception as e:  # noqa: BLE001 - provider, quota, size or FFmpeg problem -> local model
            logger.warning("Cloud transcription failed (%s); using local Whisper.", str(e)[:200])
            return None
        info = result.get("transcription_info") or {}
        segments = [Segment(start=float(s.get("start") or 0), end=float(s.get("end") or 0), text=(s.get("text") or "").strip())
                    for s in result.get("segments") or [] if (s.get("text") or "").strip()]
        if not segments and (result.get("text") or "").strip():
            dur = float(info.get("duration") or 0)
            segments = [Segment(start=0.0, end=dur, text=result["text"].strip())]
        return Transcript(
            language=info.get("language") or (language or "en"),
            language_probability=float(info.get("language_probability") or 0.0),
            duration=float(info.get("duration") or (segments[-1].end if segments else 0.0)),
            model="large-v3-turbo",
            segments=segments,
            engine="Whisper large-v3-turbo (Cloudflare Workers AI)",
        )


def _ts(seconds: float, sep: str) -> str:
    ms = int(round(max(0.0, seconds) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}{sep}{ms:03d}"


def to_srt(transcript: Transcript) -> str:
    blocks = [
        f"{i}\n{_ts(s.start, ',')} --> {_ts(s.end, ',')}\n{s.text}\n"
        for i, s in enumerate(transcript.segments, start=1)
    ]
    return "\n".join(blocks)


def to_vtt(transcript: Transcript) -> str:
    body = "\n".join(f"{_ts(s.start, '.')} --> {_ts(s.end, '.')}\n{s.text}\n" for s in transcript.segments)
    return "WEBVTT\n\n" + body


def to_json(transcript: Transcript) -> dict:
    return {
        "language": transcript.language,
        "language_probability": round(transcript.language_probability, 4),
        "duration_seconds": round(transcript.duration, 3),
        "model": f"faster-whisper/{transcript.model}",
        "text": transcript.text,
        "segments": [{"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text} for s in transcript.segments],
    }


whisper_adapter = WhisperAdapter()
