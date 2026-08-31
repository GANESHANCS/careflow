from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.import_error_log import ImportErrorLog


class ImportJob(Base):
    """
    HMIS Data Import Job model tracking asynchronous file ingestion lifecycle,
    file provenance metadata, data quality scores, and processing records.
    """
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    job_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    # Lifecycle states: QUEUED, PROCESSING, VALIDATED, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", index=True, nullable=False)

    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    error_logs: Mapped[List["ImportErrorLog"]] = relationship(
        "ImportErrorLog", back_populates="import_job", cascade="all, delete-orphan"
    )
