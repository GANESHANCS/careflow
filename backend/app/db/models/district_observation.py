from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, ForeignKey, UniqueConstraint, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.db.models.indicator import Indicator
    from backend.app.db.models.import_job import ImportJob


def classify_subgroup_total(subgroup_type: str) -> bool:
    """
    Classifies whether a subgroup/type represents an aggregate total for a parameter
    versus a disaggregated component slice (demographic slice, stock lifecycle event, or test numerator/denominator).

    Distinguishes:
    - True totals: 'TOTAL', '4. Total', '3. Total', 'Total'
    - Non-totals / slices: '1. Children', '2. Adults', '1. 6-14 yrs', '2. 15-55 yrs.',
      '1. Number tested', '2. Number Positive', '1. Balance From Previous Month',
      '2. Stocks Received', '3. Unusable Stock', '4. Stock Distributed', '5. Total Stock'.
    """
    if not subgroup_type:
        return True
    clean = subgroup_type.strip()
    if clean.upper() == "TOTAL":
        return True
    if clean in ("4. Total", "3. Total", "Total", "All", "TOTAL"):
        return True
    return False


class DistrictObservation(Base, TimestampMixin):
    """
    First-class District-Level HMIS monthly timeseries observation model.
    Models macro administrative health performance reports (e.g. MoHFW / NHM district item reports)
    without fabricating artificial facility entities.
    """
    __tablename__ = "district_observations"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    state: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    s_no: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    parameter_name: Mapped[str] = mapped_column(String(512), nullable=False)

    # Subgroup disaggregation & total classification
    subgroup_type: Mapped[str] = mapped_column(String(64), default="TOTAL", index=True, nullable=False)
    is_subgroup_total: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    # Optional canonical indicator mapping into CAREFlow indicator catalog
    indicator_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("indicators.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # Temporal coordinates
    financial_year: Mapped[str] = mapped_column(String(16), index=True, nullable=False) # e.g. "2015-16"
    reporting_month: Mapped[str] = mapped_column(String(7), index=True, nullable=False) # ISO YYYY-MM
    observation_date: Mapped[str] = mapped_column(String(10), index=True, nullable=False) # ISO YYYY-MM-01

    # Measurement values with strict preservation of missing vs zero
    value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    value_type: Mapped[str] = mapped_column(String(32), default="VALID", nullable=False) # VALID, ZERO, MISSING, INVALID
    validation_status: Mapped[str] = mapped_column(String(32), default="VALIDATED", nullable=False)
    reported_annual_total: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Provenance tracking
    source_file: Mapped[str] = mapped_column(String(255), nullable=False)
    source_row: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ingested_at: Mapped[str] = mapped_column(String(64), nullable=False)
    transformation_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)
    last_import_job_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("import_jobs.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # Relationships
    indicator: Mapped[Optional["Indicator"]] = relationship("Indicator")
    import_job: Mapped[Optional["ImportJob"]] = relationship("ImportJob")

    __table_args__ = (
        UniqueConstraint("district", "s_no", "subgroup_type", "reporting_month", name="uq_district_obs_natural_key"),
        Index("idx_dist_obs_natural_key", "district", "s_no", "subgroup_type", "reporting_month"),
        Index("idx_dist_obs_query", "district", "s_no", "reporting_month"),
        Index("idx_dist_obs_state_district", "state", "district"),
    )
