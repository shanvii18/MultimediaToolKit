"""Image utilities built on Pillow (MIT-CMU): safe loading, frame editing, sharpness, animation frames."""
import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.core.config import settings

ANIMATED_IMAGE_EXTENSIONS = {".gif", ".webp"}
OUTPUT_IMAGE_FORMATS = {
    "png": (".png", "PNG"),
    "jpg": (".jpg", "JPEG"),
    "webp": (".webp", "WEBP"),
}


@dataclass
class FrameEdits:
    rotate: int = 0                 # 0 / 90 / 180 / 270 (clockwise)
    crop_left: float = 0.0          # percentages of width/height removed from each side
    crop_top: float = 0.0
    crop_right: float = 0.0
    crop_bottom: float = 0.0
    brightness: float = 1.0         # 1.0 = unchanged
    contrast: float = 1.0
    grayscale: bool = False
    max_width: Optional[int] = None


def open_image(path: str):
    """Open an image with a decompression-bomb guard. Returns a fully loaded PIL image."""
    from PIL import Image, UnidentifiedImageError

    Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
    try:
        img = Image.open(path)
        img.load()
    except Image.DecompressionBombError:
        raise ValueError("The image is too large to process.")
    except (UnidentifiedImageError, OSError):
        raise ValueError("The file could not be read as an image (it may be corrupt or an unsupported format).")
    return img


def apply_edits(img, edits: FrameEdits):
    from PIL import ImageEnhance, ImageOps

    img = ImageOps.exif_transpose(img).convert("RGB")
    if edits.rotate % 360:
        img = img.rotate(-(edits.rotate % 360), expand=True)
    if any((edits.crop_left, edits.crop_top, edits.crop_right, edits.crop_bottom)):
        w, h = img.size
        left = int(w * edits.crop_left / 100)
        top = int(h * edits.crop_top / 100)
        right = w - int(w * edits.crop_right / 100)
        bottom = h - int(h * edits.crop_bottom / 100)
        if right - left < 8 or bottom - top < 8:
            raise ValueError("The crop removes the whole image. Reduce the crop percentages.")
        img = img.crop((left, top, right, bottom))
    if abs(edits.brightness - 1.0) > 1e-3:
        img = ImageEnhance.Brightness(img).enhance(edits.brightness)
    if abs(edits.contrast - 1.0) > 1e-3:
        img = ImageEnhance.Contrast(img).enhance(edits.contrast)
    if edits.grayscale:
        img = ImageOps.grayscale(img).convert("RGB")
    if edits.max_width and img.width > edits.max_width:
        ratio = edits.max_width / img.width
        img = img.resize((edits.max_width, max(1, int(img.height * ratio))))
    return img


def save_image(img, path: str, fmt: str) -> None:
    _, pil_format = OUTPUT_IMAGE_FORMATS[fmt]
    options = {"quality": 92} if pil_format in ("JPEG", "WEBP") else {"optimize": True}
    img.convert("RGB").save(path, pil_format, **options)


def sharpness_score(img) -> float:
    """Edge-energy sharpness (higher = sharper). Near-black/near-white frames score 0."""
    from PIL import ImageFilter, ImageStat

    gray = img.convert("L")
    if gray.width > 480:
        gray = gray.resize((480, max(1, int(gray.height * 480 / gray.width))))
    mean = ImageStat.Stat(gray).mean[0]
    if mean < 12 or mean > 245:
        return 0.0
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return float(ImageStat.Stat(edges).var[0])


def is_animated_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in ANIMATED_IMAGE_EXTENSIONS


def sample_animation_frames(path: str, count: int) -> Tuple[List[Tuple[float, object]], float, int]:
    """
    Sample up to ``count`` evenly spaced frames from an animated GIF/WebP.
    Returns ([(timestamp_seconds, RGB image)], total_duration_seconds, total_frames).
    """
    img = open_image(path)
    durations = frame_durations(img)
    total_frames = len(durations) or 1
    total_duration = sum(durations) or 0.0

    count = max(1, min(count, total_frames))
    wanted = sorted({int((i + 0.5) * total_frames / count) for i in range(count)})
    starts = [sum(durations[:i]) for i in range(total_frames)]
    frames = []
    for index in wanted:
        img.seek(index)
        img.load()
        frames.append((round(starts[index], 3), img.convert("RGB").copy()))
    return frames, total_duration, total_frames


def frame_durations(img) -> List[float]:
    """Per-frame durations in seconds. Seeks + loads each frame (Pillow only fills WebP timing after load)."""
    durations = []
    for index in range(getattr(img, "n_frames", 1)):
        img.seek(index)
        img.load()
        durations.append(max(0.02, (img.info.get("duration") or 100) / 1000.0))
    img.seek(0)
    return durations
