"""
Pipelines for the generative conversions. Each one has a CPU mode that always produces a
real result (FFmpeg / Pillow / Kokoro / Whisper) and, where useful, an AI mode that calls
the configured hosted AI provider (never simulated).
"""
import io
import json
import os
import re
from typing import List, Tuple

from app.adapters import graphics_adapter as gfx
from app.adapters import motion_adapter as motion
from app.adapters.ai_provider import AIProviderError, ai_provider
from app.adapters.ffmpeg_adapter import ffmpeg_adapter
from app.adapters.image_adapter import (OUTPUT_IMAGE_FORMATS, is_animated_image, open_image, sample_animation_frames,
                                        save_image, sharpness_score)
from app.adapters.tts_adapter import split_text, tts_adapter
from app.adapters.whisper_adapter import Segment, Transcript, to_srt
from app.core.config import settings
from app.engines.availability import engine_status
from app.engines.base import ConversionError, JobContext, stem_of
from app.engines.pipelines.common import free_models, sample_frames, speak_text, transcribe_media

MAX_SCENES = 10
MAX_AUDIO_VIDEO_SECONDS = 600
MAX_ANIMATION_SECONDS = 15


# ======================================================================
# shared helpers
# ======================================================================
def _text_input(ctx: JobContext, fallback_stem: str) -> Tuple[str, str]:
    if ctx.job.input_asset_ids:
        asset = ctx.input_asset(0)
        with open(ctx.input_path(0), "rb") as f:
            raw = f.read()
        try:
            return raw.decode("utf-8-sig").strip(), stem_of(asset.filename, fallback_stem)
        except UnicodeDecodeError:
            raise ConversionError("The text file must be UTF-8 encoded.")
    text = (ctx.params.get("text") or "").strip()
    if not text:
        raise ConversionError("Enter some text first.", code="NO_TEXT")
    return text, fallback_stem


def _ai_image(ctx: JobContext, prompt: str, size: Tuple[int, int], name: str):
    """Generate an image with the hosted provider; returns a PIL image."""
    try:
        data = ai_provider.generate_image(prompt, width=size[0] if size[0] <= 1440 else 1024,
                                          height=size[1] if size[1] <= 1440 else 1024)
    except AIProviderError as e:
        raise ConversionError(str(e), code="AI_PROVIDER_ERROR")
    path = ctx.tmp(name)
    with open(path, "wb") as f:
        f.write(data)
    try:
        return open_image(path).convert("RGB")
    except ValueError:
        raise ConversionError("The AI provider returned data that is not a valid image.", code="AI_PROVIDER_ERROR")


def _ai_describe(ctx: JobContext, image) -> str:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, "JPEG", quality=90)
    try:
        return ai_provider.describe_image(buf.getvalue())
    except AIProviderError as e:
        raise ConversionError(str(e), code="AI_PROVIDER_ERROR")


def _save_image_output(ctx: JobContext, img, stem: str, suffix: str, meta: dict) -> None:
    fmt = ctx.params.get("image_format", "png")
    ext, _ = OUTPUT_IMAGE_FORMATS[fmt]
    path = ctx.tmp(f"{suffix}{ext}")
    save_image(img, path, fmt)
    ctx.add_output(path, f"{stem}_{suffix}{ext}", f"image_{fmt}", {"width": img.width, "height": img.height, **meta})


def _size(ctx: JobContext, default: str = "landscape") -> Tuple[int, int]:
    return motion.SIZES.get(ctx.params.get("aspect", default), motion.SIZES[default])


def _wav16k(ctx: JobContext, path: str) -> str:
    wav = ctx.tmp("analysis_16k.wav")
    ffmpeg_adapter.to_wav_16k_mono(path, wav)
    return wav


def _scene_chunks(text: str) -> List[str]:
    """One scene per sentence (very long sentences are split; fragments < 12 chars join the previous scene)."""
    chunks: List[str] = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", (text or "").strip()):
        for piece in split_text(sentence, max_chars=180):
            if chunks and len(piece) < 12:
                chunks[-1] = f"{chunks[-1]} {piece}"
            else:
                chunks.append(piece)
    if not chunks:
        raise ConversionError("There is no text to turn into scenes.", code="NO_TEXT")
    max_scenes = min(MAX_SCENES, settings.MAX_VIDEO_SCENES)
    if len(chunks) > max_scenes:
        raise ConversionError(f"The script is too long for this server: {len(chunks)} scenes (max {max_scenes}). "
                              "Shorten it or split it into several videos.", code="INPUT_TOO_LONG")
    return chunks


# ======================================================================
# TEXT -> IMAGE
# ======================================================================
def text_to_image(ctx: JobContext) -> None:
    text, stem = _text_input(ctx, "text")
    size = _size(ctx, "square")
    if ctx.mode == "ai":
        ctx.progress(15, "Generating image with AI")
        img = _ai_image(ctx, text, size, "generated.png")
        meta = {"engine": f"AI provider: {ai_provider.provider}", "prompt": text[:500], "ai_generated": True}
        suffix = "ai_image"
    else:
        ctx.progress(30, "Designing typography poster")
        img = gfx.render_card(text, size=size, style=ctx.params.get("style", "auto"))
        meta = {"engine": "Pillow typography renderer", "ai_generated": False}
        suffix = "poster"
    ctx.progress(85, "Saving image")
    _save_image_output(ctx, img, stem, suffix, meta)


# ======================================================================
# TEXT -> VIDEO  (narrated scene video)
# ======================================================================
def text_to_video(ctx: JobContext) -> None:
    text, stem = _text_input(ctx, "story")
    scenes = _scene_chunks(text)
    size = _size(ctx, "landscape")
    narrate = bool(ctx.params.get("narrate", True))
    style = ctx.params.get("style", "auto")
    motions = ["zoom_in", "pan_right", "zoom_out", "pan_left"]

    clips, segments, t = [], [], 0.0
    span = 80.0 / len(scenes)
    # Pass 1: visuals + narration (model in memory). Pass 2: FFmpeg rendering (model released first),
    # so the TTS model and the video encoder are never resident at the same time on a 512 MB server.
    prepared = []
    for i, scene in enumerate(scenes):
        base = 8 + i * span * 0.5
        ctx.progress(base, f"Scene {i + 1}/{len(scenes)}: visuals")
        if ctx.mode == "ai_scenes":
            prompt = f"{scene} -- cinematic still, detailed, {style if style != 'auto' else 'film'} style"
            img = gfx.cover(_ai_image(ctx, prompt, size, f"scene_{i}.png"), size)
            img = gfx.add_title(img, scene) if ctx.params.get("captions_on_image", True) else img
        else:
            img = gfx.render_card(scene, size=size, style=style, subtitle=f"{i + 1} / {len(scenes)}")
        img_path = ctx.tmp(f"scene_{i:02d}.png")
        img.save(img_path)
        del img

        audio_path = ctx.tmp(f"scene_{i:02d}.wav")
        if narrate:
            ctx.progress(base + span * 0.25, f"Scene {i + 1}/{len(scenes)}: narration")
            seconds = tts_adapter.synthesize_to_wav(scene, audio_path, voice=ctx.params.get("voice", "af_heart"),
                                                    speed=float(ctx.params.get("speed", 1.0))) + 0.5
        else:
            seconds = max(3.0, len(scene.split()) * 0.42)
            motion.silence_wav(audio_path, seconds)
        prepared.append((scene, img_path, audio_path, seconds))

    free_models()
    for i, (scene, img_path, audio_path, seconds) in enumerate(prepared):
        ctx.progress(48 + i * span * 0.5, f"Scene {i + 1}/{len(scenes)}: rendering")
        clip = ctx.tmp(f"clip_{i:02d}.mp4")
        motion.ken_burns(img_path, clip, seconds, size=size, motion=motions[i % len(motions)], audio_path=audio_path)
        clips.append(clip)
        segments.append(Segment(start=t, end=t + seconds - 0.3, text=scene))
        t += seconds

    ctx.progress(90, "Joining scenes")
    joined = ctx.tmp("joined.mp4")
    motion.concat_clips(clips, joined, ctx.tmp("clips.txt"))
    srt = to_srt(Transcript(language="en", language_probability=1.0, duration=t, model="script", segments=segments))
    srt_path = ctx.tmp("captions.srt")
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt)
    final = ctx.tmp("video.mp4")
    motion.add_soft_subtitles(joined, srt_path, final)

    meta = {"engine": ("AI images + " if ctx.mode == "ai_scenes" else "Typography cards + ") +
                      (f"{tts_adapter.last_engine} narration + " if narrate else "") + "FFmpeg Ken Burns",
            "scenes": len(scenes), "duration_seconds": round(t, 2), "ai_generated": ctx.mode == "ai_scenes"}
    ctx.add_output(final, f"{stem}_video.mp4", "video_mp4", meta)
    ctx.add_text_output(srt, f"{stem}_captions.srt", "subtitles_srt", {"engine": "script timing"})


# ======================================================================
# TEXT -> ANIMATION
# ======================================================================
def text_to_animation(ctx: JobContext) -> None:
    text, stem = _text_input(ctx, "text")
    fmt = ctx.params.get("animation_format", "gif")
    size = motion.ANIMATION_SIZES.get(ctx.params.get("aspect", "square"), (480, 480))
    out = ctx.tmp(f"animation.{fmt}")
    if ctx.mode == "ai_loop":
        ctx.progress(15, "Generating image with AI")
        img = gfx.cover(_ai_image(ctx, text, (1024, 1024), "generated.png"), (size[0] * 2, size[1] * 2))
        src = ctx.tmp("source.png")
        img.save(src)
        ctx.progress(60, "Animating camera loop")
        clip = ctx.tmp("loop.mp4")
        motion.ken_burns(src, clip, 3.0, size=size, fps=15, motion="zoom_in")
        motion.encode_animation(clip, out, fmt=fmt, fps=15, width=size[0], boomerang=True)
        meta = {"engine": f"AI image ({ai_provider.provider}) + FFmpeg loop", "ai_generated": True}
    else:
        if len(text.split()) > 60:
            raise ConversionError("Kinetic text supports up to 60 words.", code="INPUT_TOO_LONG")
        ctx.progress(25, "Animating words")
        frames, fps = gfx.kinetic_text_frames(text, size=size, style=ctx.params.get("style", "auto"))
        ctx.progress(75, "Encoding animation")
        gfx.save_animation(frames, out, fps, fmt)
        meta = {"engine": "Pillow kinetic typography", "frames": len(frames), "fps": fps, "ai_generated": False}
    ctx.add_output(out, f"{stem}_animation.{fmt}", f"animation_{fmt}", meta)


# ======================================================================
# AUDIO -> IMAGE
# ======================================================================
def _audio_prompt(ctx: JobContext, path: str, features) -> Tuple[str, str]:
    """Build an image prompt from speech (if any) and the audio's character."""
    spoken = ""
    if engine_status().get("whisper") is None:
        try:
            transcript = transcribe_media(ctx, path, 20, 45)
            spoken = transcript.text[:300]
        except ConversionError:
            spoken = ""
    hint = (ctx.params.get("prompt_hint") or "").strip()
    mood = ", ".join(gfx.mood_words(features))
    subject = hint or (f"a scene inspired by: {spoken}" if spoken else "an abstract artwork of sound and rhythm")
    return f"{subject}. Mood: {mood}. Album cover art, high detail.", spoken


def audio_to_image(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "audio")
    size = _size(ctx, "landscape")

    if ctx.mode == "spectrogram":
        ctx.progress(30, "Rendering spectrogram")
        out = ctx.tmp("spectrogram.png")
        motion.spectrogram_image(path, out, size=size, color=ctx.params.get("palette", "magma"))
        img = open_image(out)
        _save_image_output(ctx, img, stem, "spectrogram", {"engine": "FFmpeg showspectrumpic", "ai_generated": False})
        return

    ctx.progress(10, "Analysing audio")
    features = gfx.analyze_wav(_wav16k(ctx, path))
    if ctx.mode == "ai_cover":
        prompt, spoken = _audio_prompt(ctx, path, features)
        ctx.progress(55, "Generating cover art with AI")
        img = gfx.cover(_ai_image(ctx, prompt, size, "cover.png"), size)
        _save_image_output(ctx, img, stem, "ai_cover", {"engine": f"AI provider: {ai_provider.provider}",
                                                         "prompt": prompt, "speech_excerpt": spoken,
                                                         "audio_features": features, "ai_generated": True})
        return

    # waveform art: real waveform composited on a mood-matched gradient
    ctx.progress(40, "Rendering waveform")
    wave_png = ctx.tmp("wave.png")
    motion.waveform_image(path, wave_png, size=(size[0], int(size[1] * 0.45)))
    style = gfx.style_for_features(features)
    top, bottom, ink = gfx.palette_for(stem, style)
    canvas = gfx.gradient(size, top, bottom)
    wave = open_image(wave_png).convert("RGBA")
    canvas.paste(wave, (0, (size[1] - wave.height) // 2), wave)
    canvas = gfx.add_title(canvas, ctx.params.get("title") or source.filename.rsplit(".", 1)[0])
    _save_image_output(ctx, canvas, stem, "waveform", {"engine": "FFmpeg showwavespic + Pillow",
                                                        "audio_features": features, "ai_generated": False})


# ======================================================================
# AUDIO -> VIDEO
# ======================================================================
def audio_to_video(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "audio")
    size = _size(ctx, "landscape")
    info = ffmpeg_adapter.probe(path)
    if not info.has_audio:
        raise ConversionError("This file has no audio track.", code="NO_AUDIO")
    if info.duration and info.duration > MAX_AUDIO_VIDEO_SECONDS:
        raise ConversionError(f"Audio is longer than {MAX_AUDIO_VIDEO_SECONDS // 60} minutes.", code="INPUT_TOO_LONG")

    ctx.progress(8, "Analysing audio")
    features = gfx.analyze_wav(_wav16k(ctx, path))
    title = ctx.params.get("title") or source.filename.rsplit(".", 1)[0]
    if ctx.mode == "ai_visualizer":
        prompt, _ = _audio_prompt(ctx, path, features)
        ctx.progress(45, "Generating background with AI")
        bg = gfx.cover(_ai_image(ctx, prompt, size, "bg.png"), size)
    else:
        top, bottom, _ = gfx.palette_for(title, gfx.style_for_features(features))
        bg = gfx.gradient(size, top, bottom)
    bg = gfx.add_title(bg, title, position="top")
    bg_path = ctx.tmp("background.png")
    bg.save(bg_path)

    ctx.progress(55, "Rendering visualiser")
    video = ctx.tmp("visualizer.mp4")
    motion.visualizer_video(path, bg_path, video, style=ctx.params.get("visual_style", "waves"), size=size)

    captions = None
    if ctx.params.get("captions", False):
        if engine_status().get("whisper"):
            raise ConversionError(f"Captions need speech recognition: {engine_status()['whisper']}",
                                  code="ENGINE_UNAVAILABLE")
        try:
            transcript = transcribe_media(ctx, path, 70, 92)
            if transcript.segments:
                captions = to_srt(transcript)
        except ConversionError as e:
            if e.code != "NO_SPEECH":
                raise
    final = video
    if captions:
        srt = ctx.tmp("captions.srt")
        with open(srt, "w", encoding="utf-8") as f:
            f.write(captions)
        final = ctx.tmp("visualizer_captioned.mp4")
        motion.add_soft_subtitles(video, srt, final)

    ctx.progress(95, "Saving video")
    ctx.add_output(final, f"{stem}_visualizer.mp4", "video_mp4", {
        "engine": "FFmpeg audio visualiser" + (" + AI background" if ctx.mode == "ai_visualizer" else ""),
        "visual_style": ctx.params.get("visual_style", "waves"), "captions": bool(captions),
        "ai_generated": ctx.mode == "ai_visualizer"})
    if captions:
        ctx.add_text_output(captions, f"{stem}_captions.srt", "subtitles_srt", {"engine": "speech recognition (Whisper)"})


# ======================================================================
# AUDIO -> ANIMATION
# ======================================================================
def audio_to_animation(ctx: JobContext) -> None:
    import numpy as np

    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "audio")
    fmt = ctx.params.get("animation_format", "gif")
    seconds = float(ctx.params.get("seconds", 6))
    start = float(ctx.params.get("start", 0))
    size = motion.ANIMATION_SIZES.get(ctx.params.get("aspect", "square"), (480, 480))
    out = ctx.tmp(f"animation.{fmt}")

    info = ffmpeg_adapter.probe(path)
    if not info.has_audio:
        raise ConversionError("This file has no audio track.", code="NO_AUDIO")
    if info.duration and start >= info.duration:
        raise ConversionError(f"Start time {start:.1f}s is beyond the end of the audio ({info.duration:.1f}s).")

    if ctx.mode == "waveform":
        ctx.progress(20, "Rendering waveform animation")
        bg = gfx.gradient(size, *gfx.palette_for(stem)[:2])
        bg_path = ctx.tmp("bg.png")
        bg.save(bg_path)
        clip = ctx.tmp("viz.mp4")
        motion.visualizer_video(path, bg_path, clip, style=ctx.params.get("visual_style", "waves"), size=size,
                                fps=15, max_seconds=start + seconds)
        ctx.progress(70, "Encoding animation")
        motion.encode_animation(clip, out, fmt=fmt, fps=12, width=size[0], start=start, duration=seconds)
        ctx.add_output(out, f"{stem}_waveform.{fmt}", f"animation_{fmt}",
                       {"engine": "FFmpeg visualiser → palette GIF/WebP", "ai_generated": False})
        return

    # pulse modes: an image breathing with the audio's loudness envelope
    ctx.progress(15, "Measuring loudness envelope")
    clip_wav = ctx.tmp("segment.wav")
    ffmpeg_adapter.run_ffmpeg(["-ss", f"{start:.3f}", "-i", path, "-t", f"{seconds:.3f}", "-vn", "-ac", "1",
                               "-ar", "16000", "-c:a", "pcm_s16le", clip_wav], clip_wav)
    import wave as wave_mod
    with wave_mod.open(clip_wav, "rb") as wf:
        samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype="<i2").astype(np.float32) / 32768.0
    fps = 12
    hop = max(1, 16000 // fps)
    env = np.array([np.sqrt(np.mean(samples[i:i + hop] ** 2) + 1e-12) for i in range(0, len(samples), hop)])
    if env.size == 0 or env.max() < 1e-4:
        raise ConversionError("The selected audio segment is silent.", code="NO_CONTENT")
    env = env / env.max()

    if ctx.mode == "ai_pulse":
        features = gfx.analyze_wav(clip_wav)
        prompt, _ = _audio_prompt(ctx, path, features)
        ctx.progress(40, "Generating artwork with AI")
        base = gfx.cover(_ai_image(ctx, prompt, (1024, 1024), "art.png"), size)
    else:
        base = gfx.render_card(ctx.params.get("title") or source.filename.rsplit(".", 1)[0], size=size)
    ctx.progress(65, "Animating to the beat")
    frames = []
    w, h = size
    for level in env[: int(seconds * fps)]:
        zoom = 1.0 + 0.12 * float(level)
        zw, zh = int(w * zoom), int(h * zoom)
        big = base.resize((zw, zh))
        left, top = (zw - w) // 2, (zh - h) // 2
        frames.append(big.crop((left, top, left + w, top + h)))
    gfx.save_animation(frames, out, fps, fmt)
    ctx.add_output(out, f"{stem}_pulse.{fmt}", f"animation_{fmt}", {
        "engine": "Loudness envelope (NumPy) + Pillow" + (" + AI artwork" if ctx.mode == "ai_pulse" else ""),
        "frames": len(frames), "ai_generated": ctx.mode == "ai_pulse"})


# ======================================================================
# IMAGE -> VIDEO / ANIMATION
# ======================================================================
def image_to_video(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "image")
    size = _size(ctx, "landscape")
    img = open_image(path)
    if getattr(img, "is_animated", False):
        img.seek(0)
    src = ctx.tmp("source.png")
    img.convert("RGB").save(src)

    audio = None
    seconds = float(ctx.params.get("seconds", 6))
    meta = {"engine": "FFmpeg Ken Burns", "motion": ctx.params.get("motion", "zoom_in"), "ai_generated": False}
    if ctx.mode == "narrated":
        ctx.progress(15, "Describing image with AI")
        description = _ai_describe(ctx, img)
        ctx.progress(40, "Narrating description")
        audio = ctx.tmp("narration.wav")
        seconds = tts_adapter.synthesize_to_wav(description, audio, voice=ctx.params.get("voice", "af_heart")) + 0.6
        meta.update({"engine": f"AI description ({ai_provider.last_caption_engine}) + {tts_adapter.last_engine} + FFmpeg Ken Burns",
                     "description": description, "ai_generated": True})
        ctx.add_text_output(description + "\n", f"{stem}_description.txt", "description_txt",
                            {"preview_text": description, "engine": ai_provider.last_caption_engine})

    free_models()
    ctx.progress(60, "Rendering camera motion")
    out = ctx.tmp("video.mp4")
    motion.ken_burns(src, out, seconds, size=size, motion=ctx.params.get("motion", "zoom_in"), audio_path=audio)
    ctx.add_output(out, f"{stem}_video.mp4", "video_mp4", {**meta, "duration_seconds": round(seconds, 2)})


def image_to_animation(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "image")
    fmt = ctx.params.get("animation_format", "gif")
    size = motion.ANIMATION_SIZES.get(ctx.params.get("aspect", "square"), (480, 480))
    img = open_image(path)
    if getattr(img, "is_animated", False):
        img.seek(0)
    src = ctx.tmp("source.png")
    img.convert("RGB").save(src)
    ctx.progress(30, "Animating camera loop")
    clip = ctx.tmp("loop.mp4")
    seconds = float(ctx.params.get("seconds", 3))
    motion.ken_burns(src, clip, seconds, size=size, fps=15, motion=ctx.params.get("motion", "zoom_in"))
    ctx.progress(70, "Encoding seamless loop")
    out = ctx.tmp(f"animation.{fmt}")
    motion.encode_animation(clip, out, fmt=fmt, fps=15, width=size[0], boomerang=True)
    ctx.add_output(out, f"{stem}_animation.{fmt}", f"animation_{fmt}",
                   {"engine": "FFmpeg Ken Burns boomerang loop", "ai_generated": False})


# ======================================================================
# VIDEO -> ANIMATION
# ======================================================================
def video_to_animation(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "video")
    info = ffmpeg_adapter.probe(path)
    if not info.has_video:
        raise ConversionError("This file has no video frames.")
    start = float(ctx.params.get("start", 0))
    duration = float(ctx.params.get("duration", 4))
    if info.duration and start >= info.duration:
        raise ConversionError(f"Start time {start:.1f}s is beyond the end of the video ({info.duration:.1f}s).")
    fmt = ctx.params.get("animation_format", "gif")
    ctx.progress(30, "Encoding animation")
    out = ctx.tmp(f"clip.{fmt}")
    motion.encode_animation(path, out, fmt=fmt, fps=int(ctx.params.get("fps", 12)),
                            width=int(ctx.params.get("width", 480)), start=start, duration=duration,
                            effect=ctx.params.get("effect", "none"), boomerang=bool(ctx.params.get("boomerang", False)))
    ctx.add_output(out, f"{stem}_animation.{fmt}", f"animation_{fmt}", {
        "engine": "FFmpeg palettegen/paletteuse" if fmt == "gif" else "FFmpeg libwebp",
        "start": start, "duration": duration, "effect": ctx.params.get("effect", "none"), "ai_generated": False})


# ======================================================================
# ANIMATION -> IMAGE / VIDEO
# ======================================================================
def animation_to_image(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "animation")
    if ctx.mode == "contact_sheet":
        count = int(ctx.params.get("frames", 12))
        ctx.progress(30, "Sampling frames")
        frames = sample_frames(ctx, path, count)
        sheet = gfx.contact_sheet(frames, columns=int(ctx.params.get("columns", 4)))
        _save_image_output(ctx, sheet, stem, "contact_sheet",
                           {"engine": "Pillow contact sheet", "frames": len(frames), "ai_generated": False})
        return

    ctx.progress(20, "Scoring frames for sharpness")
    frames = sample_frames(ctx, path, 16)
    scored = sorted(((sharpness_score(img), ts, img) for ts, img in frames), key=lambda x: x[0], reverse=True)
    score, ts, best = scored[0]
    if score <= 0 and len(scored) > 1:
        raise ConversionError("No usable frame was found (the animation appears blank).", code="NO_CONTENT")
    meta = {"engine": "Pillow sharpness scoring", "timestamp_seconds": ts, "ai_generated": False}
    if ctx.mode == "poster":
        title = (ctx.params.get("title") or "").strip() or source.filename.rsplit(".", 1)[0]
        best = gfx.add_title(best.convert("RGB"), title)
        meta["engine"] += " + Pillow poster title"
    _save_image_output(ctx, best.convert("RGB"), stem, "poster" if ctx.mode == "poster" else "best_frame", meta)


def _animation_frames_to_pngs(ctx: JobContext, path: str) -> Tuple[str, float, int]:
    from app.adapters.image_adapter import frame_durations

    img = open_image(path)
    durations = frame_durations(img)
    count = len(durations)
    for i in range(count):
        img.seek(i)
        img.load()
        img.convert("RGB").save(ctx.tmp(f"f_{i:05d}.png"))
    fps = count / max(0.04, sum(durations))
    return ctx.tmp("f_%05d.png"), fps, count


def animation_to_video(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "animation")
    fmt = ctx.params.get("video_format", "mp4")
    loops = int(ctx.params.get("loops", 3))
    width = int(ctx.params.get("width", 0)) or None
    smooth = bool(ctx.params.get("smooth", False))
    out = ctx.tmp(f"video.{fmt}")

    ctx.progress(20, "Reading animation frames")
    if is_animated_image(path):
        pattern, fps, count = _animation_frames_to_pngs(ctx, path)
        if count < 1:
            raise ConversionError("The animation has no frames.")
    else:
        # short clip container: render frames with FFmpeg first so looping is exact
        info = ffmpeg_adapter.probe(path)
        if not info.has_video:
            raise ConversionError("This file has no visual frames.")
        fps = 15.0
        ffmpeg_adapter.run_ffmpeg(["-i", path, "-vf", f"fps={fps}", "-frames:v", "900", ctx.tmp("f_%05d.png")])
        count = len([n for n in os.listdir(ctx.work_dir) if n.startswith("f_") and n.endswith(".png")])
        pattern = ctx.tmp("f_%05d.png")
    ctx.progress(55, "Rendering video" + (" with motion smoothing" if smooth else ""))
    motion.frames_to_video(pattern, fps, out, fmt=fmt, loops=loops, frame_count=count, width=width, smooth=smooth)
    ctx.add_output(out, f"{stem}_video.{fmt}", f"video_{fmt}", {
        "engine": "FFmpeg" + (" minterpolate" if smooth else ""), "loops": loops, "source_fps": round(fps, 2),
        "ai_generated": False})


# ======================================================================
# AI description modes for existing conversions
# ======================================================================
def describe_image_to_text(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    img = open_image(ctx.input_path(0))
    if getattr(img, "is_animated", False):
        img.seek(0)
    ctx.progress(30, "Describing image with AI")
    text = _ai_describe(ctx, img)
    stem = stem_of(source.filename, "image")
    ctx.add_text_output(text + "\n", f"{stem}_description.txt", "description_txt", {
        "engine": ai_provider.last_caption_engine, "preview_text": text, "ai_generated": True})


def describe_image_to_audio(ctx: JobContext) -> None:
    source = ctx.input_asset(0)
    img = open_image(ctx.input_path(0))
    if getattr(img, "is_animated", False):
        img.seek(0)
    ctx.progress(15, "Describing image with AI")
    text = _ai_describe(ctx, img)
    stem = stem_of(source.filename, "image")
    ctx.add_text_output(text + "\n", f"{stem}_description.txt", "description_txt",
                        {"engine": ai_provider.last_caption_engine, "preview_text": text})
    speak_text(ctx, text, f"{stem}_description", 40, 98, {"pipeline": "AI description → text-to-speech", "ai_generated": True})


def describe_animation(ctx: JobContext, speak: bool) -> None:
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "animation")
    ctx.progress(10, "Sampling key frames")
    frames = sample_frames(ctx, path, 3)
    parts = []
    for i, (ts, frame) in enumerate(frames):
        ctx.progress(20 + i * 20, f"Describing frame {i + 1}/{len(frames)} with AI")
        parts.append((ts, _ai_describe(ctx, frame)))
    text = "\n".join(f"[{ts:.2f}s] {d}" for ts, d in parts)
    ctx.add_text_output(text + "\n", f"{stem}_description.txt", "description_txt",
                        {"engine": ai_provider.last_caption_engine, "preview_text": text, "ai_generated": True})
    ctx.add_text_output(json.dumps({"frames": [{"timestamp": t, "description": d} for t, d in parts]}, indent=2),
                        f"{stem}_description.json", "description_json", {"engine": ai_provider.last_caption_engine})
    if speak:
        narration = " Then, ".join(d for _, d in parts)
        speak_text(ctx, narration, f"{stem}_narration", 82, 98, {"pipeline": "AI frame descriptions → text-to-speech",
                                                                 "ai_generated": True})


def video_poster(ctx: JobContext) -> None:
    """Video→Image poster modes: best frame + title (CPU) or AI-generated poster from the video."""
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "video")
    frames = sample_frames(ctx, path, 12)
    ctx.progress(30, "Choosing the strongest frame")
    score, ts, best = max(((sharpness_score(f), t, f) for t, f in frames), key=lambda x: x[0])
    title = (ctx.params.get("title") or "").strip() or source.filename.rsplit(".", 1)[0]
    size = _size(ctx, "portrait")
    if ctx.mode == "ai_poster":
        ctx.progress(45, "Describing the video with AI")
        description = _ai_describe(ctx, best)
        prompt = f"Movie poster: {description} Dramatic lighting, high detail, no text."
        ctx.progress(65, "Generating poster with AI")
        art = gfx.cover(_ai_image(ctx, prompt, size, "poster_art.png"), size)
        meta = {"engine": f"AI provider: {ai_provider.provider}", "prompt": prompt, "ai_generated": True}
    else:
        art = gfx.cover(best, size)
        meta = {"engine": "Best frame + Pillow poster title", "timestamp_seconds": ts, "ai_generated": False}
    poster = gfx.add_title(art, title)
    _save_image_output(ctx, poster, stem, "poster", meta)


# ======================================================================
# VIDEO / ANIMATION -> IMAGE : AI restyle (img2img)
# ======================================================================
def ai_restyle_frame(ctx: JobContext) -> None:
    """Pick the sharpest frame (CPU), then repaint it with the hosted img2img model in the requested style."""
    source = ctx.input_asset(0)
    path = ctx.input_path(0)
    stem = stem_of(source.filename, "frame")
    ctx.progress(15, "Choosing the sharpest frame")
    frames = sample_frames(ctx, path, 12)
    score, ts, best = max(((sharpness_score(f), t, f) for t, f in frames), key=lambda x: x[0])
    style = (ctx.params.get("style_prompt") or "").strip()
    if not style:
        raise ConversionError("Describe the style you want (for example 'watercolor painting').", code="INVALID_INPUT")
    strength = float(ctx.params.get("strength", 0.6))
    buf = io.BytesIO()
    best.convert("RGB").save(buf, "PNG")
    ctx.progress(40, "Restyling with AI")
    try:
        data = ai_provider.transform_image(buf.getvalue(), f"{style}, high quality, detailed", strength=strength)
    except AIProviderError as e:
        raise ConversionError(str(e), code="AI_PROVIDER_ERROR")
    raw = ctx.tmp("restyled.png")
    with open(raw, "wb") as f:
        f.write(data)
    try:
        img = open_image(raw).convert("RGB")
    except ValueError:
        raise ConversionError("The AI provider returned data that is not a valid image.", code="AI_PROVIDER_ERROR")
    ctx.progress(90, "Saving image")
    _save_image_output(ctx, img, stem, "ai_restyled", {
        "engine": f"AI provider: {ai_provider.provider} ({settings.CLOUDFLARE_IMG2IMG_MODEL})",
        "style_prompt": style, "strength": strength, "source_timestamp_seconds": ts, "ai_generated": True})
