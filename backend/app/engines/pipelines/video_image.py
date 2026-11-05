"""Video→Image: extract a chosen frame (or the sharpest one) and apply simple edits."""
from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.image_adapter import FrameEdits, OUTPUT_IMAGE_FORMATS, apply_edits, open_image, save_image, sharpness_score
from app.engines.base import ConversionError, JobContext, stem_of

BEST_FRAME_SAMPLES = 12


def _edits(params) -> FrameEdits:
    max_width = int(params.get("max_width") or 0)
    return FrameEdits(
        rotate=int(params.get("rotate", "0")),
        crop_left=float(params.get("crop_left", 0)),
        crop_top=float(params.get("crop_top", 0)),
        crop_right=float(params.get("crop_right", 0)),
        crop_bottom=float(params.get("crop_bottom", 0)),
        brightness=float(params.get("brightness", 1.0)),
        contrast=float(params.get("contrast", 1.0)),
        grayscale=bool(params.get("grayscale", False)),
        max_width=max_width or None,
    )


def video_to_image(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    ctx.progress(10, "Inspecting video")
    info = ffmpeg_adapter.probe(path)
    if not info.has_video:
        raise ConversionError("This file has no video frames.", code="INVALID_INPUT")
    duration = info.duration or 0.0

    candidates = []
    if ctx.mode == "best_frame":
        if duration <= 0:
            raise ConversionError("The video duration could not be determined.")
        report = ctx.sub_progress(15, 70, "Scoring frames for sharpness")
        for i in range(BEST_FRAME_SAMPLES):
            ts = round((i + 0.5) * duration / BEST_FRAME_SAMPLES, 3)
            preview = ctx.tmp(f"sample_{i:02d}.png")
            ffmpeg_adapter.extract_frame(path, ts, preview, width=480)
            candidates.append((sharpness_score(open_image(preview)), ts))
            report((i + 1) / BEST_FRAME_SAMPLES)
        score, timestamp = max(candidates)
        if score <= 0:
            raise ConversionError("No usable frame was found (the video appears blank).", code="NO_CONTENT")
    else:
        timestamp = float(ctx.params.get("timestamp", 0.0))
        if duration and timestamp > duration:
            raise ConversionError(
                f"Timestamp {timestamp:.2f}s is beyond the end of the video ({duration:.2f}s).")

    ctx.progress(75, f"Extracting frame at {timestamp:.2f}s")
    raw = ctx.tmp("frame_full.png")
    ffmpeg_adapter.extract_frame(path, timestamp, raw)

    ctx.progress(85, "Applying edits")
    try:
        img = apply_edits(open_image(raw), _edits(ctx.params))
    except ValueError as e:
        raise ConversionError(str(e))
    fmt = ctx.params.get("image_format", "png")
    ext, _ = OUTPUT_IMAGE_FORMATS[fmt]
    out = ctx.tmp(f"frame{ext}")
    save_image(img, out, fmt)

    ctx.add_output(out, f"{stem_of(source.filename, 'video')}_frame_{timestamp:.2f}s{ext}", f"image_{fmt}", {
        "engine": "FFmpeg + Pillow",
        "mode": ctx.mode,
        "timestamp_seconds": timestamp,
        "width": img.width,
        "height": img.height,
        "sharpness_candidates": [{"timestamp": t, "score": round(s, 1)} for s, t in sorted(candidates, key=lambda c: c[1])],
        "source_asset_id": source.id,
    })
