"""
Local text-to-speech with Kokoro-82M (weights Apache-2.0) via kokoro-onnx (MIT).

Runs on CPU with ONNX Runtime using the int8-quantised model (~88 MB). Model files are
downloaded once from the kokoro-onnx GitHub release into MODEL_CACHE_DIR/kokoro.
Phonemisation uses espeak-ng (GPL-3.0, bundled by espeakng-loader) -- see THIRD_PARTY_NOTICES.md.
"""
import importlib.util
import logging
import os
import re
import threading
import urllib.request
import wave
from typing import Callable, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Curated English voices (all included in voices-v1.0.bin).
KOKORO_VOICES = {
    "af_heart": "Heart: US English, female",
    "af_bella": "Bella: US English, female",
    "af_sarah": "Sarah: US English, female",
    "am_michael": "Michael: US English, male",
    "am_adam": "Adam: US English, male",
    "bf_emma": "Emma: British English, female",
    "bf_isabella": "Isabella: British English, female",
    "bm_george": "George: British English, male",
    "bm_daniel": "Daniel: British English, male",
}
SAMPLE_RATE = 24000
_MAX_CHUNK_CHARS = 350


def split_text(text: str, max_chars: int = _MAX_CHUNK_CHARS) -> List[str]:
    """Split into sentence-based chunks <= max_chars (keeps progress granular, bounds memory)."""
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?;:])\s+", text)
    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        while len(sentence) > max_chars:  # very long sentence: split at the last space
            cut = sentence.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            if current:
                chunks.append(current)
                current = ""
            chunks.append(sentence[:cut].strip())
            sentence = sentence[cut:].strip()
        if current and len(current) + 1 + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return [c for c in chunks if c]


class KokoroTTSAdapter:
    engine_name = "kokoro"

    def __init__(self):
        self._lock = threading.Lock()
        self._kokoro = None

    @property
    def model_dir(self) -> str:
        return os.path.join(settings.MODEL_CACHE_DIR, "kokoro")

    @property
    def model_path(self) -> str:
        return os.path.join(self.model_dir, settings.KOKORO_MODEL_FILE)

    @property
    def voices_path(self) -> str:
        return os.path.join(self.model_dir, settings.KOKORO_VOICES_FILE)

    def _files_present(self) -> bool:
        return os.path.isfile(self.model_path) and os.path.isfile(self.voices_path)

    def availability(self) -> Optional[str]:
        if importlib.util.find_spec("kokoro_onnx") is None:
            return "Text-to-speech engine (kokoro-onnx) is not installed on this server."
        if not self._files_present() and not settings.AUTO_DOWNLOAD_MODELS:
            return "Text-to-speech model files are not downloaded on this server."
        return None

    def ensure_model_files(self) -> None:
        os.makedirs(self.model_dir, exist_ok=True)
        for filename, dest in ((settings.KOKORO_MODEL_FILE, self.model_path),
                               (settings.KOKORO_VOICES_FILE, self.voices_path)):
            if os.path.isfile(dest):
                continue
            if not settings.AUTO_DOWNLOAD_MODELS:
                raise RuntimeError(f"Missing TTS model file {filename} and AUTO_DOWNLOAD_MODELS is disabled.")
            url = f"{settings.KOKORO_RELEASE_URL.rstrip('/')}/{filename}"
            logger.info("Downloading %s ...", url)
            tmp = dest + ".part"
            urllib.request.urlretrieve(url, tmp)  # noqa: S310 - fixed https release URL from settings
            os.replace(tmp, dest)

    def _load(self):
        if self._kokoro is None:
            self.ensure_model_files()
            from kokoro_onnx import Kokoro

            logger.info("Loading Kokoro TTS model %s", self.model_path)
            self._kokoro = Kokoro(self.model_path, self.voices_path)
        return self._kokoro

    @staticmethod
    def lang_for_voice(voice: str) -> str:
        return "en-gb" if voice.startswith("b") else "en-us"

    def synthesize_to_wav(
        self,
        text: str,
        output_wav: str,
        voice: str = "af_heart",
        speed: float = 1.0,
        progress: Optional[Callable[[float], None]] = None,
    ) -> float:
        """Synthesize ``text`` to a 24 kHz mono 16-bit WAV. Returns the duration in seconds."""
        import numpy as np

        if voice not in KOKORO_VOICES:
            raise ValueError(f"Unknown voice '{voice}'.")
        chunks = split_text(text)
        if not chunks:
            raise ValueError("There is no text to speak.")

        pause = np.zeros(int(SAMPLE_RATE * 0.12), dtype=np.float32)
        parts = []
        with self._lock:
            kokoro = self._load()
            for i, chunk in enumerate(chunks):
                samples, sample_rate = kokoro.create(chunk, voice=voice, speed=float(speed),
                                                     lang=self.lang_for_voice(voice))
                if sample_rate != SAMPLE_RATE:
                    raise RuntimeError(f"Unexpected TTS sample rate {sample_rate}.")
                parts.extend([samples.astype(np.float32), pause])
                if progress:
                    progress((i + 1) / len(chunks))

        audio = np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)
        pcm = (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2")
        with wave.open(output_wav, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(pcm.tobytes())
        return len(pcm) / SAMPLE_RATE


tts_adapter = KokoroTTSAdapter()
