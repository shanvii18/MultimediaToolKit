import os
import subprocess
import shutil
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class FFmpegAdapter:
    def __init__(self):
        self.ffmpeg_cmd = shutil.which("ffmpeg") or "ffmpeg"

    def is_available(self) -> bool:
        try:
            res = subprocess.run([self.ffmpeg_cmd, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return res.returncode == 0
        except Exception:
            return False

    def extract_audio(self, input_video_path: str, output_audio_path: str, audio_format: str = "mp3") -> bool:
        """
        Extracts audio track from video using ffmpeg.
        """
        if not os.path.exists(input_video_path):
            raise FileNotFoundError(f"Input file not found: {input_video_path}")

        cmd = [
            self.ffmpeg_cmd,
            "-y",  # overwrite output
            "-i", input_video_path,
            "-vn",  # disable video recording
            "-acodec", "libmp3lame" if audio_format == "mp3" else "copy",
            "-q:a", "2",
            output_audio_path
        ]
        logger.info(f"Executing FFmpeg audio extraction: {' '.join(cmd)}")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            logger.error(f"FFmpeg error: {res.stderr}")
            raise RuntimeError(f"FFmpeg extraction failed: {res.stderr[:200]}")
        return True

    def convert_audio(self, input_audio_path: str, output_audio_path: str) -> bool:
        cmd = [self.ffmpeg_cmd, "-y", "-i", input_audio_path, output_audio_path]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"FFmpeg audio conversion failed: {res.stderr[:200]}")
        return True


ffmpeg_adapter = FFmpegAdapter()
