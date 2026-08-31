from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base

if TYPE_CHECKING:
    from backend.app.db.models.import_job import ImportJob


class ImportErrorLog(Base):
    """
    Detailed audit error/warning log associated with an HMIS import job execution.
    """
    __tablename__ = "import_error_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    import_job_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_row: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_sheet: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_code: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="ERROR", nullable=False) # WARNING, ERROR, CRITICAL
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    import_job: Mapped["ImportJob"] = relationship("ImportJob", back_populates="error_logs")
