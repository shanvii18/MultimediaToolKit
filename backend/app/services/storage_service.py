import os
import shutil
import hashlib
from typing import Tuple
from fastapi import UploadFile
from app.core.config import settings


class StorageService:
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_upload(self, upload_file: UploadFile) -> Tuple[str, int, str]:
        """
        Saves an uploaded file safely, calculating its byte size and SHA-256 checksum.
        Returns: (relative_storage_key, size_in_bytes, checksum)
        """
        import uuid
        file_ext = os.path.splitext(upload_file.filename)[1].lower()
        storage_filename = f"{uuid.uuid4().hex}{file_ext}"
        destination_path = os.path.join(self.base_dir, storage_filename)

        hasher = hashlib.sha256()
        total_size = 0

        with open(destination_path, "wb") as buffer:
            while chunk := upload_file.file.read(1024 * 64):
                total_size += len(chunk)
                if total_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    # Cleanup oversized file
                    buffer.close()
                    if os.path.exists(destination_path):
                        os.remove(destination_path)
                    raise ValueError(f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes.")
                hasher.update(chunk)
                buffer.write(chunk)

        checksum = hasher.hexdigest()
        return storage_filename, total_size, checksum

    def get_full_path(self, storage_key: str) -> str:
        safe_path = os.path.abspath(os.path.join(self.base_dir, storage_key))
        if not safe_path.startswith(os.path.abspath(self.base_dir)):
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
