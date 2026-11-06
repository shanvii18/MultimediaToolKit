"""
Server-side media type resolution.

The browser-supplied ``Content-Type`` of an upload is attacker-controlled and must
never be trusted or echoed back. MIME types are derived from the (already
allow-listed) file extension instead.
"""
import os

EXTENSION_MIME_TYPES = {
    # Video
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".mkv": "video/x-matroska",
    ".webm": "video/webm",
    ".flv": "video/x-flv",
    ".wmv": "video/x-ms-wmv",
    ".m4v": "video/x-m4v",
    # Audio
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".wma": "audio/x-ms-wma",
    # Images
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    # Documents & captions
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain; charset=utf-8",
    ".json": "application/json",
    ".srt": "application/x-subrip",
    ".vtt": "text/vtt; charset=utf-8",
}

DEFAULT_MIME_TYPE = "application/octet-stream"


def mime_type_for(filename: str) -> str:
    """Return the trusted MIME type for a stored filename / storage key."""
    ext = os.path.splitext(filename or "")[1].lower()
    return EXTENSION_MIME_TYPES.get(ext, DEFAULT_MIME_TYPE)
