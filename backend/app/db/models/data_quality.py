from typing import Optional
from sqlalchemy import String, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.models.base import Base, TimestampMixin


class DataQualityLog(Base, TimestampMixin):
    """
    Data Quality Audit Log Model for recording 13-point pipeline audit findings.
    """
    __tablename__ = "data_quality_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    audit_timestamp: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    issue_category: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    affected_record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
