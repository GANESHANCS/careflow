from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.db.models.import_job import ImportJob
from backend.app.services.imports.storage import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    ImportStorageService,
)


class ImportValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class ImportValidatorService:
    @staticmethod
    def validate_file_constraints(original_filename: str, content: bytes, mime_type: Optional[str] = None):
        """
        Validates uploaded file against extension, size, and filename safety policies.
        Raises ImportValidationError if invalid.
        """
        if not content or len(content) == 0:
            raise ImportValidationError("EMPTY_FILE", "Uploaded file is empty (0 bytes).")

        if len(content) > MAX_FILE_SIZE_BYTES:
            raise ImportValidationError(
                "FILE_TOO_LARGE",
                f"File size ({len(content)} bytes) exceeds the maximum allowed limit of 50 MB."
            )

        sanitized = ImportStorageService.sanitize_filename(original_filename)
        ext = Path(sanitized).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise ImportValidationError(
                "INVALID_FILE_TYPE",
                f"Unsupported file format '{ext}'. Only .csv, .xlsx, and .xls files are supported."
            )

    @staticmethod
    def check_idempotency(db: Session, file_hash: str) -> Optional[ImportJob]:
        """
        Checks if an import job with the identical file hash has already been ingested or is currently processing.
        Returns the existing ImportJob if found, else None.
        """
        existing_job = (
            db.query(ImportJob)
            .filter(
                ImportJob.file_hash == file_hash,
                ImportJob.status.in_(["COMPLETED", "PROCESSING", "VALIDATED", "COMPLETED_WITH_WARNINGS"])
            )
            .order_by(ImportJob.id.desc())
            .first()
        )
        return existing_job
