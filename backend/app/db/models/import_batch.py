from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.import_job import ImportJob


class ImportBatch(Base):
    """
    Tracks automated HMIS batch ingestion cycles (e.g. from incoming directory scans
    or bulk manual ingestion), aggregating multiple import jobs with consolidated lifecycle
    monitoring, progress metrics, and failure recovery.
    """
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    batch_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(64), default="DIRECTORY_WATCHER", nullable=False)

    # Statuses: QUEUED, PROCESSING, COMPLETED, PARTIALLY_FAILED, FAILED, CANCELLED
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", index=True, nullable=False)

    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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

    initiated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Relationship to associated import jobs
    import_jobs: Mapped[List["ImportJob"]] = relationship(
        "ImportJob", back_populates="batch", cascade="all, delete-orphan", order_by="ImportJob.id.asc()"
    )
