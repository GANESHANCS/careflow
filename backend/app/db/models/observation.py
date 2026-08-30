from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.db.models.facility import Facility
    from backend.app.db.models.indicator import Indicator


class Observation(Base, TimestampMixin):
    """
    Normalized HMIS monthly timeseries observation model.
    """
    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    facility_id: Mapped[str] = mapped_column(String(64), ForeignKey("facilities.id", ondelete="CASCADE"), index=True, nullable=False)
    indicator_id: Mapped[str] = mapped_column(String(64), ForeignKey("indicators.id", ondelete="CASCADE"), index=True, nullable=False)
    observation_date: Mapped[str] = mapped_column(String(10), index=True, nullable=False) # ISO YYYY-MM-01
    reporting_month: Mapped[str] = mapped_column(String(7), nullable=False) # YYYY-MM
    
    # Preserves explicit missing vs zero distinction
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_type: Mapped[str] = mapped_column(String(32), default="VALID", nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), default="VALIDATED", nullable=False)

    # Provenance tracking
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    source_sheet: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    source_row: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ingested_at: Mapped[str] = mapped_column(String(64), nullable=False)
    transformation_version: Mapped[str] = mapped_column(String(32), default="2.0.0", nullable=False)

    # Relationships
    facility: Mapped["Facility"] = relationship("Facility", back_populates="observations")
    indicator: Mapped["Indicator"] = relationship("Indicator", back_populates="observations")

    __table_args__ = (
        UniqueConstraint("facility_id", "indicator_id", "observation_date", name="uq_facility_indicator_date"),
        Index("idx_obs_fac_ind_date", "facility_id", "indicator_id", "observation_date"),
    )
