"""
FFmpeg-based motion engine: Ken Burns camera moves, audio visualisers, high-quality
GIF/WebP encoding (palettegen), animation -> video, clip concatenation and soft subtitles.
"""
import os
from typing import List, Optional, Sequence, Tuple

from app.adapters.ffmpeg_adapter import ffmpeg_adapter

SIZES = {
    "landscape": (1280, 720),
    "portrait": (720, 1280),
    "square": (1080, 1080),
}
ANIMATION_SIZES = {"square": (480, 480), "landscape": (640, 360), "portrait": (360, 640)}
VIDEO_ENCODE = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


def _zoompan(motion: str, frames: int, size: Tuple[int, int], fps: int) -> str:
    w, h = size
    n = max(1, frames - 1)
    if motion == "zoom_out":
        z, x, y = f"1.18-0.18*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    elif motion == "pan_left":
        z, x, y = "1.18", f"(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"
    elif motion == "pan_right":
        z, x, y = "1.18", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"
    else:  # zoom_in
        z, x, y = f"1+0.18*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
    # Upscale first so the slow zoom is smooth, then crop to the target aspect.
    return (f"scale={w * 2}:{h * 2}:force_original_aspect_ratio=increase,crop={w * 2}:{h * 2},"
            f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={w}x{h}:fps={fps},setsar=1,format=yuv420p")


def ken_burns(image_path: str, out_path: str, seconds: float, size=(1280, 720), fps: int = 25,
              motion: str = "zoom_in", audio_path: Optional[str] = None) -> None:
    frames = max(2, int(round(seconds * fps)))
    args = ["-i", image_path]
    if audio_path:
        args += ["-i", audio_path]
    args += ["-vf", _zoompan(motion, frames, size, fps), "-frames:v", str(frames), *VIDEO_ENCODE]
    if audio_path:
        args += ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-af", "apad", "-t", f"{seconds:.3f}"]
    else:
        args += ["-an"]
    args.append(out_path)
    ffmpeg_adapter.run_ffmpeg(args, out_path, error_hint="Could not render the camera motion.")


def silence_wav(out_path: str, seconds: float) -> None:
    ffmpeg_adapter.run_ffmpeg(
        ["-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{seconds:.3f}", "-c:a", "pcm_s16le", out_path],
        out_path)


def concat_clips(clip_paths: Sequence[str], out_path: str, list_path: str) -> None:
    """Concatenate clips that share codecs/parameters (stream copy, no quality loss)."""
    with open(list_path, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write("file '" + os.path.abspath(p).replace("\\", "/").replace("'", "'\\''") + "'\n")
    ffmpeg_adapter.run_ffmpeg(["-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy",
                               "-movflags", "+faststart", out_path], out_path)


def add_soft_subtitles(video_path: str, srt_path: str, out_path: str) -> None:
    """Attach an SRT as a selectable subtitle track (mov_text) without re-encoding video/audio."""
    ffmpeg_adapter.run_ffmpeg(["-i", video_path, "-i", srt_path, "-map", "0", "-map", "1:s", "-c", "copy",
                               "-c:s", "mov_text", "-metadata:s:s:0", "language=eng", out_path], out_path)


VISUALIZERS = {
    "waves": "showwaves=s={w}x{h}:mode=cline:rate={fps}:colors=0xF97316|0xFBBF24",
    "spectrum": "showspectrum=s={w}x{h}:mode=combined:color=fire:slide=scroll:scale=cbrt",
    "bars": "showfreqs=s={w}x{h}:mode=bar:ascale=sqrt:fscale=log:colors=0xF97316|0xFBBF24:rate={fps}",
}


def visualizer_video(audio_path: str, background_path: str, out_path: str, style: str = "waves",
                     size=(1280, 720), fps: int = 25, max_seconds: Optional[float] = None) -> None:
    """Audio-reactive visualiser blended (screen mode) over a still background, with the original audio."""
    w, h = size
    # Render the visualiser at half resolution and upscale: ~4x less memory/CPU (small servers).
    vw, vh = max(2, (w // 2) // 2 * 2), max(2, (h // 2) // 2 * 2)
    viz = VISUALIZERS.get(style, VISUALIZERS["waves"]).format(w=vw, h=vh, fps=fps)
    graph = (f"[0:a]apad,{viz},fps={fps},scale={w}:{h}:flags=bilinear,format=rgb24[v];"
             f"[1:v]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},fps={fps},format=rgb24[bg];"
             f"[bg][v]blend=all_mode=screen,format=yuv420p[out]")
    # The output length is set explicitly with -t. Ending the graph early (blend/overlay
    # shortest=1 or -shortest) makes FFmpeg 7+ abort with a spurious ENOMEM at teardown.
    length = min(max_seconds or 1e9, media_duration(audio_path) or 600.0)
    args = ["-i", audio_path, "-loop", "1", "-t", f"{length + 1:.3f}", "-i", background_path,
            "-filter_complex", graph,
            "-map", "[out]", "-map", "0:a", *VIDEO_ENCODE, "-c:a", "aac", "-b:a", "192k",
            "-t", f"{length:.3f}", out_path]
    ffmpeg_adapter.run_ffmpeg(args, out_path, error_hint="Make sure the file contains an audio track.")


def spectrogram_image(audio_path: str, out_path: str, size=(1280, 720), color: str = "magma") -> None:
    ffmpeg_adapter.run_ffmpeg(["-i", audio_path, "-lavfi",
                               f"showspectrumpic=s={size[0]}x{size[1]}:legend=1:color={color}:scale=log",
                               "-frames:v", "1", out_path], out_path,
                              error_hint="Make sure the file contains an audio track.")


def waveform_image(audio_path: str, out_path: str, size=(1280, 360), color: str = "0xF97316") -> None:
    ffmpeg_adapter.run_ffmpeg(["-i", audio_path, "-filter_complex",
                               f"showwavespic=s={size[0]}x{size[1]}:split_channels=0:colors={color}",
                               "-frames:v", "1", out_path], out_path,
                              error_hint="Make sure the file contains an audio track.")


EFFECTS = {
    "none": "",
    "grayscale": "hue=s=0",
    "vintage": "curves=preset=vintage",
    "cartoon": "edgedetect=mode=colormix:high=0.25:low=0.08",
}


def encode_animation(input_path: str, out_path: str, fmt: str = "gif", fps: int = 12, width: int = 480,
                     start: float = 0.0, duration: Optional[float] = None, effect: str = "none",
                     boomerang: bool = False, input_args: Sequence[str] = ()) -> None:
    """Video/frames -> optimised GIF (palettegen/paletteuse) or animated WebP."""
    chain = [f"fps={fps}", f"scale={width}:-2:flags=lanczos"]
    if EFFECTS.get(effect):
        chain.append(EFFECTS[effect])
    base = ",".join(chain)
    if boomerang:
        base += ",split[f][r0];[r0]reverse[r];[f][r]concat=n=2:v=1:a=0"
    # -ss / -t are INPUT options here, so effects like boomerang can extend the output.
    trim = ["-ss", f"{start:.3f}"] if start else []
    dur = ["-t", f"{duration:.3f}"] if duration else []
    if fmt == "webp":
        graph = f"[0:v]{base}[out]"
        args = [*trim, *dur, *input_args, "-i", input_path, "-filter_complex", graph, "-map", "[out]",
                "-c:v", "libwebp", "-lossless", "0", "-q:v", "75", "-loop", "0", "-an", out_path]
    else:
        graph = f"[0:v]{base},split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4[out]"
        args = [*trim, *dur, *input_args, "-i", input_path, "-filter_complex", graph, "-map", "[out]",
                "-loop", "0", "-an", out_path]
    ffmpeg_adapter.run_ffmpeg(args, out_path, error_hint="Could not encode the animation.")


def frames_to_video(pattern: str, fps: float, out_path: str, fmt: str = "mp4", loops: int = 1,
                    frame_count: int = 1, width: Optional[int] = None, smooth: bool = False) -> None:
    """Numbered PNG frames -> MP4/WebM, optionally looped and motion-interpolated to 30 fps."""
    chain = []
    if loops > 1:
        chain.append(f"loop=loop={loops - 1}:size={frame_count}:start=0")
    chain.append(f"scale={width}:-2:flags=lanczos" if width else "scale=trunc(iw/2)*2:trunc(ih/2)*2")
    total = loops * frame_count / fps
    if smooth:
        # minterpolate stops at the last frame's timestamp; pad so the final frame keeps its full duration.
        chain.append(f"tpad=stop_mode=clone:stop_duration={2.0 / fps:.4f}")
        chain.append("minterpolate=fps=30:mi_mode=blend")
    chain.append("format=yuv420p")
    codec = ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", "34", "-row-mt", "1"] if fmt == "webm" else VIDEO_ENCODE
    ffmpeg_adapter.run_ffmpeg(["-framerate", f"{fps:.4f}", "-i", pattern, "-vf", ",".join(chain), *codec,
                               "-t", f"{total:.3f}", "-an", out_path], out_path, error_hint="Could not render the video.")


def media_duration(path: str) -> float:
    info = ffmpeg_adapter.probe(path)
    return float(info.duration or 0.0)
