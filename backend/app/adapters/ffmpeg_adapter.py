import os
import json
import subprocess
import shutil
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class FFmpegTimeoutError(RuntimeError):
    """Raised when an FFmpeg process exceeds its time limit (process is killed)."""


class UnsupportedAudioFormatError(ValueError):
    pass


@dataclass(frozen=True)
class AudioFormatSpec:
    extension: str
    codec: str
    mime_type: str
    codec_args: List[str] = field(default_factory=list)


# Each output format is re-encoded with a codec that is valid for its container.
AUDIO_FORMATS: Dict[str, AudioFormatSpec] = {
    "mp3": AudioFormatSpec(".mp3", "libmp3lame", "audio/mpeg", ["-q:a", "2"]),
    "wav": AudioFormatSpec(".wav", "pcm_s16le", "audio/wav"),
    "m4a": AudioFormatSpec(".m4a", "aac", "audio/mp4", ["-b:a", "192k"]),
    "ogg": AudioFormatSpec(".ogg", "libvorbis", "audio/ogg", ["-q:a", "5"]),
    "flac": AudioFormatSpec(".flac", "flac", "audio/flac"),
}


@dataclass(frozen=True)
class MediaInfo:
    duration: Optional[float]
    has_audio: bool
    has_video: bool
    width: Optional[int] = None
    height: Optional[int] = None
    format_name: str = ""


def threading_args(args: List[str], output_path: Optional[str] = None) -> List[str]:
    """Apply FFMPEG_THREADS: cap filter-graph threads (global) and encoder threads (output option)."""
    n = settings.FFMPEG_THREADS
    if n <= 0:
        return list(args)
    out = ["-filter_threads", str(n), "-filter_complex_threads", str(n), *args]
    if output_path and args and args[-1] == output_path:
        out = out[:-1] + ["-threads", str(n), output_path]
    return out


def _remove_quietly(path: Optional[str]) -> None:
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            logger.warning("Could not remove partial output %s", path)


class FFmpegAdapter:
    def __init__(self):
        self._cached_ffmpeg_cmd: Optional[str] = None

    def get_ffmpeg_cmd(self) -> Optional[str]:
        """
        Dynamically finds the ffmpeg executable on PATH, Windows Registry paths, or standard locations.
        """
        if self._cached_ffmpeg_cmd and os.path.isfile(self._cached_ffmpeg_cmd):
            return self._cached_ffmpeg_cmd

        # 1. Standard shutil.which lookup
        found = shutil.which("ffmpeg")
        if found:
            self._cached_ffmpeg_cmd = found
            return found

        # 2. Windows registry PATH lookup (handles winget installations before full OS restart)
        if os.name == "nt":
            try:
                import winreg
                for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                    try:
                        subkey = r"Environment" if root == winreg.HKEY_CURRENT_USER else r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
                        with winreg.OpenKey(root, subkey) as key:
                            path_val = winreg.QueryValueEx(key, "Path")[0]
                            for p in path_val.split(";"):
                                cand = os.path.join(p.strip(), "ffmpeg.exe")
                                if os.path.isfile(cand):
                                    self._cached_ffmpeg_cmd = cand
                                    return cand
                    except Exception:
                        continue
            except Exception:
                pass

            # 3. Known WinGet package path check
            user_home = os.path.expanduser("~")
            winget_pkgs = os.path.join(user_home, r"AppData\Local\Microsoft\WinGet\Packages")
            if os.path.isdir(winget_pkgs):
                for root_dir, _, files in os.walk(winget_pkgs):
                    if "ffmpeg.exe" in files:
                        cand = os.path.join(root_dir, "ffmpeg.exe")
                        self._cached_ffmpeg_cmd = cand
                        return cand

        return None

    def is_available(self) -> bool:
        cmd = self.get_ffmpeg_cmd()
        if not cmd:
            return False
        try:
            res = subprocess.run([cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    @staticmethod
    def audio_format_spec(audio_format: str) -> AudioFormatSpec:
        fmt = (audio_format or "").strip().lower()
        if fmt not in AUDIO_FORMATS:
            raise UnsupportedAudioFormatError(
                f"Unsupported audio format '{audio_format}'. Supported: {', '.join(sorted(AUDIO_FORMATS))}."
            )
        return AUDIO_FORMATS[fmt]

    def _run(self, cmd: List[str], output_path: Optional[str], timeout_seconds: Optional[int]) -> subprocess.CompletedProcess:
        """Run FFmpeg with a hard timeout; on timeout the process is killed and partial output removed."""
        timeout = timeout_seconds if timeout_seconds is not None else settings.FFMPEG_TIMEOUT_SECONDS
        try:
            return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            _remove_quietly(output_path)
            raise FFmpegTimeoutError(f"FFmpeg exceeded the {timeout}s processing time limit and was stopped.")

    def extract_audio(
        self,
        input_video_path: str,
        output_audio_path: str,
        audio_format: str = "mp3",
        timeout_seconds: Optional[int] = None,
    ) -> bool:
        """
        Extracts the audio track from a video using ffmpeg, re-encoding with the codec that
        matches ``audio_format`` (never stream-copying into a mismatched container).
        Never mocks or fabricates extraction results.
        """
        spec = self.audio_format_spec(audio_format)

        ffmpeg_bin = self.get_ffmpeg_cmd()
        if not ffmpeg_bin:
            raise RuntimeError(
                "FFmpeg is not installed or not accessible on system PATH. "
                "Audio extraction requires a functional FFmpeg installation."
            )

        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input file not found: {input_video_path}")

        if os.path.splitext(output_audio_path)[1].lower() != spec.extension:
            raise ValueError(
                f"Output path extension must be '{spec.extension}' for format '{audio_format}'."
            )

        os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)

        cmd = [
            ffmpeg_bin,
            "-y",  # overwrite output
            "-i", input_video_path,
            "-vn",  # disable video stream
            "-map", "0:a:0",  # first audio stream (clear error if none)
            "-c:a", spec.codec,
            *spec.codec_args,
            output_audio_path,
        ]
        logger.info(f"Executing FFmpeg audio extraction: {' '.join(cmd)}")
        res = self._run(cmd, output_audio_path, timeout_seconds)

        if res.returncode != 0:
            _remove_quietly(output_audio_path)
            err_msg = res.stderr.strip()
            # Extract most informative error tail
            clean_err = err_msg.splitlines()[-1] if err_msg else "Unknown FFmpeg error"
            logger.error(f"FFmpeg error: {err_msg}")
            raise RuntimeError(f"FFmpeg extraction failed ({clean_err}). Ensure the file contains a valid audio stream.")

        if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
            _remove_quietly(output_audio_path)
            raise RuntimeError("FFmpeg completed but the output audio file was not created or is empty.")

        return True

    # ------------------------------------------------------------------ #
    # Generic helpers used by the conversion engines
    # ------------------------------------------------------------------ #
    def _require(self) -> str:
        ffmpeg_bin = self.get_ffmpeg_cmd()
        if not ffmpeg_bin:
            raise RuntimeError("FFmpeg is not installed or not accessible on system PATH.")
        return ffmpeg_bin

    def get_ffprobe_cmd(self) -> Optional[str]:
        ffmpeg_bin = self.get_ffmpeg_cmd()
        if ffmpeg_bin:
            folder = os.path.dirname(ffmpeg_bin)
            for name in ("ffprobe.exe", "ffprobe"):
                cand = os.path.join(folder, name)
                if os.path.isfile(cand):
                    return cand
        return shutil.which("ffprobe")

    def run_ffmpeg(self, args: List[str], output_path: Optional[str] = None,
                   timeout_seconds: Optional[int] = None, error_hint: str = "") -> None:
        """Run ffmpeg with -y/-hide_banner and the standard timeout; raise RuntimeError with the stderr tail."""
        cmd = [self._require(), "-y", "-hide_banner", "-loglevel", "error", *threading_args(args, output_path)]
        res = self._run(cmd, output_path, timeout_seconds)
        if res.returncode != 0:
            _remove_quietly(output_path)
            tail = (res.stderr or "").strip().splitlines()
            raise RuntimeError(f"FFmpeg failed ({tail[-1] if tail else 'unknown error'}). {error_hint}".strip())
        if output_path and (not os.path.exists(output_path) or os.path.getsize(output_path) == 0):
            _remove_quietly(output_path)
            raise RuntimeError(f"FFmpeg produced no output. {error_hint}".strip())

    def probe(self, path: str) -> MediaInfo:
        """Inspect a media file with ffprobe (duration, streams, dimensions)."""
        ffprobe = self.get_ffprobe_cmd()
        if not ffprobe:
            raise RuntimeError("ffprobe is not available (it ships with FFmpeg).")
        cmd = [ffprobe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            raise FFmpegTimeoutError("ffprobe exceeded its time limit.")
        if res.returncode != 0:
            raise RuntimeError("The file could not be read as media (it may be corrupt or an unsupported format).")
        data = json.loads(res.stdout or "{}")
        streams = data.get("streams", [])
        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        duration = None
        for candidate in (data.get("format", {}).get("duration"), (video or {}).get("duration")):
            try:
                if candidate not in (None, "N/A"):
                    duration = float(candidate)
                    break
            except (TypeError, ValueError):
                continue
        return MediaInfo(
            duration=duration,
            has_audio=any(s.get("codec_type") == "audio" for s in streams),
            has_video=video is not None,
            width=int(video["width"]) if video and video.get("width") else None,
            height=int(video["height"]) if video and video.get("height") else None,
            format_name=data.get("format", {}).get("format_name", ""),
        )

    def to_wav_16k_mono(self, input_path: str, output_wav: str) -> None:
        """Decode the first audio stream to 16 kHz mono PCM (speech-recognition input)."""
        self.run_ffmpeg(
            ["-i", input_path, "-vn", "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", output_wav],
            output_wav,
            error_hint="Make sure the file contains an audio track.",
        )

    def encode_audio(self, input_path: str, output_path: str, audio_format: str) -> None:
        spec = self.audio_format_spec(audio_format)
        if os.path.splitext(output_path)[1].lower() != spec.extension:
            raise ValueError(f"Output path extension must be '{spec.extension}' for format '{audio_format}'.")
        self.run_ffmpeg(["-i", input_path, "-vn", "-c:a", spec.codec, *spec.codec_args, output_path], output_path)

    def extract_frame(self, input_path: str, timestamp: float, output_path: str, width: Optional[int] = None) -> None:
        """Extract the single frame at ``timestamp`` seconds (accurate seek) as an image."""
        vf = ["-vf", f"scale={int(width)}:-2"] if width else []
        self.run_ffmpeg(
            ["-ss", f"{max(0.0, timestamp):.3f}", "-i", input_path, "-frames:v", "1", *vf, output_path],
            output_path,
            error_hint="The timestamp may be beyond the end of the video.",
        )

    def convert_audio(self, input_audio_path: str, output_audio_path: str, timeout_seconds: Optional[int] = None) -> bool:
        ffmpeg_bin = self.get_ffmpeg_cmd()
        if not ffmpeg_bin:
            raise RuntimeError("FFmpeg is not installed or not accessible on system PATH.")

        cmd = [ffmpeg_bin, "-y", "-i", input_audio_path, output_audio_path]
        res = self._run(cmd, output_audio_path, timeout_seconds)
        if res.returncode != 0:
            _remove_quietly(output_audio_path)
            raise RuntimeError(f"FFmpeg audio conversion failed: {res.stderr[:200]}")
        return True


ffmpeg_adapter = FFmpegAdapter()
