import os
import re
import hashlib
import secrets
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
ALLOWED_MIME_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/octet-stream"
}


class ImportStorageService:
    def __init__(self, base_upload_dir: str = "data/uploads"):
        self.base_upload_dir = Path(base_upload_dir)
        self.base_upload_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def generate_job_code() -> str:
        """Generates secure unique job code e.g. JOB_20260831_153000_a1b2c3."""
        now_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rand_suffix = secrets.token_hex(3)
        return f"JOB_{now_str}_{rand_suffix}"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitizes filename to prevent directory traversal attacks (../, \\, null bytes).
        Returns a clean safe base filename.
        """
        if not filename:
            return "uploaded_file.csv"
        # Take basename to strip directory paths
        base = os.path.basename(filename)
        # Strip null bytes and control chars
        base = base.replace("\0", "").strip()
        # Replace path separators or dangerous characters
        clean_name = re.sub(r'[^a-zA-Z0-9_\.\-]', '_', base)
        # Prevent hidden files or empty names
        clean_name = clean_name.lstrip('.')
        if not clean_name:
            return "uploaded_file.csv"
        return clean_name

    @staticmethod
    def calculate_file_hash(content: bytes) -> str:
        """Calculates SHA-256 hex digest of file content for idempotency checking."""
        return hashlib.sha256(content).hexdigest()

    def save_upload_file(self, job_code: str, original_filename: str, content: bytes) -> Tuple[str, str]:
        """
        Saves uploaded file content inside data/uploads/{job_code}/{sanitized_filename}.
        Returns (relative_storage_path, absolute_storage_path).
        """
        job_dir = self.base_upload_dir / job_code
        job_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = self.sanitize_filename(original_filename)
        file_path = job_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        abs_path = str(file_path.resolve())
        rel_path = str(file_path)

        return rel_path, abs_path
