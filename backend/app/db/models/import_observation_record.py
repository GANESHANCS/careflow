from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.import_job import ImportJob


class ImportObservationRecord(Base):
    """
    Durable per-observation change log tracking individual observation alterations
    performed during an HMIS import job, including the full before-image necessary
    for safe, atomic, and auditable rollback.
    """
    __tablename__ = "import_observation_records"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    import_job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    observation_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)

    # Action classification: INSERT, UPDATE, UNCHANGED
    action: Mapped[str] = mapped_column(String(20), nullable=False)

    # Before-image attributes preserved for UPDATE action rollback
    previous_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    previous_value_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    previous_validation_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    previous_source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    previous_source_sheet: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    previous_source_row: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    previous_ingested_at: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    previous_transformation_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    previous_import_job_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # After-image attributes set by this import
    new_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_value_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    import_job: Mapped["ImportJob"] = relationship("ImportJob", back_populates="change_records")
