import os
import subprocess
import shutil
import logging
from typing import Optional

logger = logging.getLogger(__name__)


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

    def extract_audio(self, input_video_path: str, output_audio_path: str, audio_format: str = "mp3") -> bool:
        """
        Extracts audio track from video using ffmpeg.
        Never mocks or fabricates extraction results.
        """
        ffmpeg_bin = self.get_ffmpeg_cmd()
        if not ffmpeg_bin:
            raise RuntimeError(
                "FFmpeg is not installed or not accessible on system PATH. "
                "Audio extraction requires a functional FFmpeg installation."
            )

        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input file not found: {input_video_path}")

        os.makedirs(os.path.dirname(os.path.abspath(output_audio_path)), exist_ok=True)

        cmd = [
            ffmpeg_bin,
            "-y",  # overwrite output
            "-i", input_video_path,
            "-vn",  # disable video stream
            "-acodec", "libmp3lame" if audio_format == "mp3" else "copy",
            "-q:a", "2",
            output_audio_path
        ]
        logger.info(f"Executing FFmpeg audio extraction: {' '.join(cmd)}")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if res.returncode != 0:
            err_msg = res.stderr.strip()
            # Extract most informative error tail
            clean_err = err_msg.splitlines()[-1] if err_msg else "Unknown FFmpeg error"
            logger.error(f"FFmpeg error: {err_msg}")
            raise RuntimeError(f"FFmpeg extraction failed ({clean_err}). Ensure the file contains a valid audio stream.")

        if not os.path.exists(output_audio_path) or os.path.getsize(output_audio_path) == 0:
            raise RuntimeError("FFmpeg completed but the output audio file was not created or is empty.")

        return True

    def convert_audio(self, input_audio_path: str, output_audio_path: str) -> bool:
        ffmpeg_bin = self.get_ffmpeg_cmd()
        if not ffmpeg_bin:
            raise RuntimeError("FFmpeg is not installed or not accessible on system PATH.")

        cmd = [ffmpeg_bin, "-y", "-i", input_audio_path, output_audio_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio conversion failed: {res.stderr[:200]}")
        return True


ffmpeg_adapter = FFmpegAdapter()
