"""
CPU graphics engine (Pillow + NumPy): typography cards, kinetic-text animation frames,
poster titles, contact sheets, and simple audio feature analysis. No AI model required.
"""
import hashlib
import math
import wave
from typing import Dict, List, Optional, Sequence, Tuple

PALETTES: List[Tuple[Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]]] = [
    ((15, 23, 42), (234, 88, 12), (255, 247, 237)),     # slate -> orange (brand)
    ((17, 24, 39), (124, 58, 237), (245, 243, 255)),    # night -> violet
    ((6, 78, 59), (16, 185, 129), (236, 253, 245)),     # forest -> emerald
    ((30, 27, 75), (236, 72, 153), (253, 242, 248)),    # indigo -> pink
    ((12, 74, 110), (56, 189, 248), (240, 249, 255)),   # ocean -> sky
    ((69, 26, 3), (245, 158, 11), (255, 251, 235)),     # ember -> amber
]

STYLES = {"brand": 0, "violet": 1, "emerald": 2, "rose": 3, "ocean": 4, "amber": 5}


def palette_for(text: str, style: str = "auto"):
    if style in STYLES:
        return PALETTES[STYLES[style]]
    digest = int(hashlib.sha256((text or "").encode("utf-8")).hexdigest(), 16)
    return PALETTES[digest % len(PALETTES)]


def font(size: int):
    from PIL import ImageFont

    return ImageFont.load_default(size=size)  # bundled FreeType font (Pillow >= 10.1)


def gradient(size: Tuple[int, int], top, bottom, angle_mix: float = 0.35):
    """Diagonal two-colour gradient with a soft vignette."""
    import numpy as np
    from PIL import Image

    w, h = size
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    t = np.clip(y * (1 - angle_mix) + x * angle_mix, 0, 1)[..., None]
    top_c = np.array(top, dtype=np.float32)
    bottom_c = np.array(bottom, dtype=np.float32)
    img = top_c * (1 - t) + bottom_c * t
    cx, cy = (x - 0.5), (y - 0.5)
    vignette = 1 - 0.35 * np.clip((cx ** 2 + cy ** 2) * 2.2, 0, 1)
    img = img * vignette[..., None]
    return Image.fromarray(np.clip(img, 0, 255).astype("uint8"), "RGB")


def wrap(draw, text: str, fnt, max_width: int) -> List[str]:
    lines: List[str] = []
    for paragraph in (text or "").split("\n"):
        words = paragraph.split()
        line = ""
        for word in words:
            candidate = f"{line} {word}".strip()
            if draw.textlength(candidate, font=fnt) <= max_width or not line:
                line = candidate
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return [l for l in lines if l is not None]


def fit_text(draw, text: str, box_w: int, box_h: int, max_size: int = 96, min_size: int = 22):
    """Largest font size whose wrapped text fits in the box."""
    size = max_size
    while size >= min_size:
        fnt = font(size)
        lines = wrap(draw, text, fnt, box_w)
        line_h = int(size * 1.25)
        if line_h * len(lines) <= box_h:
            return fnt, lines, line_h
        size -= 4
    fnt = font(min_size)
    lines = wrap(draw, text, fnt, box_w)
    max_lines = max(1, box_h // int(min_size * 1.25))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .,;") + "…"
    return fnt, lines, int(min_size * 1.25)


def render_card(text: str, size=(1280, 720), style: str = "auto", subtitle: str = "", background=None):
    """A title/typography card. ``background`` (PIL image) is used instead of a gradient if given."""
    from PIL import Image, ImageDraw, ImageFilter

    bg_top, bg_bottom, ink = palette_for(text, style)
    w, h = size
    if background is not None:
        img = cover(background, size).filter(ImageFilter.GaussianBlur(radius=2))
        shade = Image.new("RGB", size, (0, 0, 0))
        img = Image.blend(img, shade, 0.45)
    else:
        img = gradient(size, bg_top, bg_bottom)
    draw = ImageDraw.Draw(img)
    margin = int(w * 0.09)
    fnt, lines, line_h = fit_text(draw, text.strip(), w - 2 * margin, int(h * 0.62), max_size=int(h * 0.12))
    total = line_h * len(lines)
    y = (h - total) // 2 - (int(h * 0.04) if subtitle else 0)
    for line in lines:
        lw = draw.textlength(line, font=fnt)
        x = (w - lw) / 2
        draw.text((x + 2, y + 3), line, font=fnt, fill=(0, 0, 0))
        draw.text((x, y), line, font=fnt, fill=ink)
        y += line_h
    if subtitle:
        sf = font(max(18, int(h * 0.035)))
        sw = draw.textlength(subtitle, font=sf)
        draw.text(((w - sw) / 2, y + int(h * 0.03)), subtitle, font=sf, fill=(226, 232, 240))
    accent = bg_bottom if background is None else (234, 88, 12)
    draw.rectangle([margin, h - int(h * 0.08), margin + int(w * 0.12), h - int(h * 0.08) + 6], fill=accent)
    return img


def cover(img, size):
    """Resize + centre-crop to exactly ``size`` (like CSS object-fit: cover)."""
    from PIL import ImageOps

    return ImageOps.fit(img.convert("RGB"), size, method=3)


def add_title(img, title: str, position: str = "bottom"):
    """Poster-style title band over an image."""
    from PIL import Image, ImageDraw

    img = img.convert("RGB").copy()
    w, h = img.size
    band_h = int(h * 0.24)
    overlay = Image.new("RGBA", (w, band_h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for i in range(band_h):  # fade-in gradient band
        alpha = int(200 * (i / band_h if position == "bottom" else 1 - i / band_h))
        od.line([(0, i), (w, i)], fill=(0, 0, 0, alpha))
    y0 = h - band_h if position == "bottom" else 0
    img.paste(overlay, (0, y0), overlay)
    draw = ImageDraw.Draw(img)
    fnt, lines, line_h = fit_text(draw, title, int(w * 0.86), int(band_h * 0.7), max_size=int(h * 0.09), min_size=18)
    y = y0 + (band_h - line_h * len(lines)) // 2 + (int(band_h * 0.12) if position == "bottom" else 0)
    for line in lines:
        lw = draw.textlength(line, font=fnt)
        draw.text(((w - lw) / 2 + 2, y + 2), line, font=fnt, fill=(0, 0, 0))
        draw.text(((w - lw) / 2, y), line, font=fnt, fill=(255, 255, 255))
        y += line_h
    return img


def kinetic_text_frames(text: str, size=(720, 720), fps: int = 12, style: str = "auto",
                        seconds_per_word: float = 0.35, hold_seconds: float = 1.2):
    """Words appear one by one with a pop-in scale, then hold. Returns (frames, fps)."""
    from PIL import Image, ImageDraw

    words = (text or "").split()[:60]
    if not words:
        raise ValueError("There is no text to animate.")
    bg_top, bg_bottom, ink = palette_for(text, style)
    base = gradient(size, bg_top, bg_bottom)
    w, h = size
    margin = int(w * 0.08)
    probe = ImageDraw.Draw(base)
    fnt, lines, line_h = fit_text(probe, " ".join(words), w - 2 * margin, int(h * 0.7), max_size=int(h * 0.11))

    # position of each word
    positions = []
    y = (h - line_h * len(lines)) // 2
    for line in lines:
        lw = probe.textlength(line, font=fnt)
        x = (w - lw) / 2
        for word in line.split():
            positions.append((word, x, y))
            x += probe.textlength(word + " ", font=fnt)
        y += line_h

    per_word = max(1, int(round(seconds_per_word * fps)))
    total = per_word * len(positions) + int(hold_seconds * fps)
    frames = []
    for f in range(total):
        frame = base.copy()
        draw = ImageDraw.Draw(frame)
        for i, (word, x, yy) in enumerate(positions):
            start = i * per_word
            if f < start:
                break
            p = min(1.0, (f - start + 1) / per_word)
            ease = 1 - (1 - p) ** 3
            offset = int((1 - ease) * line_h * 0.35)
            color = tuple(int(c * ease + bc * (1 - ease)) for c, bc in zip(ink, bg_top))
            draw.text((x, yy + offset), word, font=fnt, fill=color)
        frames.append(frame)
    return frames, fps


def save_animation(frames: Sequence, path: str, fps: int, fmt: str = "gif") -> None:
    duration = int(1000 / max(1, fps))
    first, rest = frames[0], list(frames[1:])
    if fmt == "webp":
        first.save(path, "WEBP", save_all=True, append_images=rest, duration=duration, loop=0, quality=85)
    else:
        first.save(path, "GIF", save_all=True, append_images=rest, duration=duration, loop=0, optimize=True)


def contact_sheet(frames: Sequence[Tuple[float, object]], columns: int = 4, thumb_width: int = 320):
    from PIL import Image, ImageDraw

    thumbs = []
    for ts, frame in frames:
        ratio = thumb_width / frame.width
        t = frame.convert("RGB").resize((thumb_width, max(1, int(frame.height * ratio))))
        ImageDraw.Draw(t).text((8, 6), f"{ts:.2f}s", font=font(16), fill=(255, 255, 255))
        thumbs.append(t)
    rows = math.ceil(len(thumbs) / columns)
    th = max(t.height for t in thumbs)
    gap = 8
    sheet = Image.new("RGB", (columns * thumb_width + (columns + 1) * gap, rows * th + (rows + 1) * gap), (15, 23, 42))
    for i, t in enumerate(thumbs):
        r, c = divmod(i, columns)
        sheet.paste(t, (gap + c * (thumb_width + gap), gap + r * (th + gap)))
    return sheet


# ---------------- audio features (no ML) ----------------
def analyze_wav(path: str) -> Dict[str, float]:
    """Loudness / brightness / dynamics of a 16-bit mono WAV, used to steer visuals and prompts."""
    import numpy as np

    with wave.open(path, "rb") as wf:
        rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if samples.size == 0:
        return {"duration": 0.0, "rms": 0.0, "brightness": 0.0, "dynamics": 0.0}
    win = max(1, rate // 10)
    usable = samples[: samples.size // win * win].reshape(-1, win) if samples.size >= win else samples[None, :]
    rms_frames = np.sqrt((usable ** 2).mean(axis=1) + 1e-12)
    zcr = float(np.mean(np.abs(np.diff(np.sign(samples))) > 0))
    return {
        "duration": float(samples.size / rate),
        "rms": float(np.sqrt((samples ** 2).mean())),
        "brightness": zcr,
        "dynamics": float(rms_frames.std() / (rms_frames.mean() + 1e-9)),
    }


def mood_words(features: Dict[str, float]) -> List[str]:
    words = []
    words.append("energetic, vivid" if features["rms"] > 0.12 else "calm, soft" if features["rms"] < 0.04 else "warm, balanced")
    words.append("bright, airy" if features["brightness"] > 0.12 else "deep, moody")
    words.append("dynamic, dramatic" if features["dynamics"] > 0.6 else "steady, flowing")
    return words


def style_for_features(features: Dict[str, float]) -> str:
    if features["rms"] > 0.12:
        return "brand" if features["brightness"] > 0.12 else "rose"
    if features["brightness"] > 0.12:
        return "ocean"
    return "violet" if features["dynamics"] > 0.6 else "emerald"
