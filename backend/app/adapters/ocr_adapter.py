"""
OCR with Tesseract 5 (Apache-2.0) through pytesseract (Apache-2.0).

The `tesseract` binary must be installed on the host (Docker: `apt install tesseract-ocr`;
Windows: UB-Mannheim build). If it is missing, OCR features report themselves as
unavailable instead of failing mysteriously.
"""
import logging
import os
import shutil
from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Tesseract page segmentation modes offered to users.
OCR_LAYOUTS = {
    "auto": ("3", "Automatic page layout"),
    "block": ("6", "Single uniform block of text"),
    "sparse": ("11", "Sparse text (signs, memes, UI screenshots)"),
}

OCR_LANGUAGE_NAMES = {
    "eng": "English", "hin": "Hindi", "spa": "Spanish", "fra": "French", "deu": "German",
    "ita": "Italian", "por": "Portuguese", "rus": "Russian", "jpn": "Japanese", "kor": "Korean",
    "chi_sim": "Chinese (Simplified)", "ara": "Arabic", "ben": "Bengali", "tam": "Tamil",
}

_WINDOWS_CANDIDATES = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"D:\Tools\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
)


@dataclass
class OcrResult:
    text: str
    word_count: int
    mean_confidence: Optional[float]
    language: str
    layout: str


class TesseractAdapter:
    engine_name = "tesseract"

    def __init__(self):
        self._cmd: Optional[str] = None
        self._langs: Optional[List[str]] = None

    def find_cmd(self) -> Optional[str]:
        if self._cmd and os.path.isfile(self._cmd):
            return self._cmd
        candidates = [settings.TESSERACT_CMD] if settings.TESSERACT_CMD else []
        found = shutil.which("tesseract")
        if found:
            candidates.append(found)
        if os.name == "nt":
            candidates.extend(_WINDOWS_CANDIDATES)
        for cand in candidates:
            if cand and os.path.isfile(cand):
                self._cmd = cand
                return cand
        return None

    def availability(self) -> Optional[str]:
        try:
            import pytesseract  # noqa: F401
        except ImportError:
            return "OCR library (pytesseract) is not installed on this server."
        if not self.find_cmd():
            return "Tesseract OCR is not installed on this server."
        return None

    def _pytesseract(self):
        import pytesseract

        cmd = self.find_cmd()
        if not cmd:
            raise RuntimeError("Tesseract OCR is not installed on this server.")
        pytesseract.pytesseract.tesseract_cmd = cmd
        return pytesseract

    def languages(self) -> List[str]:
        if self._langs is None:
            try:
                self._langs = sorted(self._pytesseract().get_languages(config=""))
            except Exception:  # noqa: BLE001
                self._langs = []
        return self._langs

    @staticmethod
    def prepare(image):
        """Normalise an image for OCR: orientation, grayscale, upscale small inputs."""
        from PIL import Image, ImageOps

        img = ImageOps.exif_transpose(image)
        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            rgba = img.convert("RGBA")
            background.paste(rgba, mask=rgba.split()[-1])
            img = background
        img = img.convert("L")
        if img.width < 1000:
            factor = 2 if img.width >= 500 else 3
            img = img.resize((img.width * factor, img.height * factor), Image.LANCZOS)
        return img

    def ocr(self, image, language: str = "eng", layout: str = "auto") -> OcrResult:
        pyt = self._pytesseract()
        psm = OCR_LAYOUTS.get(layout, OCR_LAYOUTS["auto"])[0]
        config = f"--oem 1 --psm {psm}"
        img = self.prepare(image)
        text = pyt.image_to_string(img, lang=language, config=config, timeout=settings.OCR_TIMEOUT_SECONDS)
        data = pyt.image_to_data(img, lang=language, config=config, timeout=settings.OCR_TIMEOUT_SECONDS,
                                 output_type=pyt.Output.DICT)
        confs = []
        words = 0
        for word, conf in zip(data.get("text", []), data.get("conf", [])):
            try:
                c = float(conf)
            except (TypeError, ValueError):
                continue
            if word.strip() and c >= 0:
                words += 1
                confs.append(c)
        cleaned = "\n".join(line.rstrip() for line in text.splitlines()).strip()
        # collapse 3+ blank lines
        while "\n\n\n" in cleaned:
            cleaned = cleaned.replace("\n\n\n", "\n\n")
        return OcrResult(
            text=cleaned,
            word_count=words,
            mean_confidence=round(sum(confs) / len(confs), 1) if confs else None,
            language=language,
            layout=layout,
        )


ocr_adapter = TesseractAdapter()
