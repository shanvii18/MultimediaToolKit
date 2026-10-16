import os
import shutil
import hashlib
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings


class StorageService:
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    def save_upload(self, upload_file: UploadFile) -> Tuple[str, int, str]:
        """
        Saves an uploaded file safely, enforcing size limits, extension whitelisting,
        non-empty payload check, and calculating SHA-256 checksum.
        Returns: (relative_storage_key, size_in_bytes, checksum)
        """
        import uuid
        raw_name = upload_file.filename or "uploaded_media"
        safe_filename = os.path.basename(raw_name)
        file_ext = os.path.splitext(safe_filename)[1].lower()

        if not file_ext or file_ext not in settings.ALLOWED_EXTENSIONS:
            allowed_list = ", ".join(sorted(settings.ALLOWED_EXTENSIONS))
            raise ValueError(
                f"File format '{file_ext}' is not supported. "
                f"Allowed formats: {allowed_list}"
            )

        storage_filename = f"{uuid.uuid4().hex}{file_ext}"
        destination_path = os.path.join(self.base_dir, storage_filename)

        hasher = hashlib.sha256()
        total_size = 0

        with open(destination_path, "wb") as buffer:
            while chunk := upload_file.file.read(1024 * 64):
                total_size += len(chunk)
                if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    buffer.close()
                    if os.path.exists(destination_path):
                        os.remove(destination_path)
                    raise ValueError(
                        f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
                    )
                hasher.update(chunk)
                buffer.write(chunk)

        if total_size == 0:
            if os.path.exists(destination_path):
                os.remove(destination_path)
            raise ValueError("Uploaded file is empty (0 bytes). Please upload a valid media file.")

        checksum = hasher.hexdigest()
        return storage_filename, total_size, checksum

    def get_full_path(self, storage_key: str) -> str:
        safe_key = os.path.basename(storage_key)
        safe_path = os.path.abspath(os.path.join(self.base_dir, safe_key))
        if not safe_path.startswith(self.base_dir):
            raise ValueError("Unsafe path traversal detected.")
        return safe_path

    def write_output_file(self, content_bytes: bytes, extension: str = ".txt") -> Tuple[str, int, str]:
        import uuid
        storage_filename = f"out_{uuid.uuid4().hex}{extension}"
        destination_path = os.path.join(self.base_dir, storage_filename)
        with open(destination_path, "wb") as f:
            f.write(content_bytes)

        checksum = hashlib.sha256(content_bytes).hexdigest()
        return storage_filename, len(content_bytes), checksum


storage_service = StorageService()
