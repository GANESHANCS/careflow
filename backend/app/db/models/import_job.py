from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.import_error_log import ImportErrorLog
    from backend.app.db.models.import_observation_record import ImportObservationRecord
    from backend.app.db.models.import_batch import ImportBatch


class ImportJob(Base):
    """
    HMIS Data Import Job model tracking asynchronous file ingestion lifecycle,
    file provenance metadata, data quality scores, processing records, and rollback state.
    """
    __tablename__ = "import_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    job_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    batch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("import_batches.id"), nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    # Lifecycle states: QUEUED, PROCESSING, VALIDATED, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED, ROLLED_BACK
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", index=True, nullable=False)

    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Worker claiming, heartbeat and retry metadata
    claimed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    claimed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    error_summary: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    schema_profile: Mapped[Optional[str]] = mapped_column(String(64), default="mohfw_standard_v2", nullable=True)

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

    # Rollback audit metadata
    rolled_back_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rolled_back_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rollback_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    batch: Mapped[Optional["ImportBatch"]] = relationship("ImportBatch", back_populates="import_jobs")
    error_logs: Mapped[List["ImportErrorLog"]] = relationship(
        "ImportErrorLog", back_populates="import_job", cascade="all, delete-orphan"
    )
    change_records: Mapped[List["ImportObservationRecord"]] = relationship(
        "ImportObservationRecord", back_populates="import_job", cascade="all, delete-orphan"
    )
