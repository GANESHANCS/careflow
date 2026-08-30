from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.db.models.facility import Facility
    from backend.app.db.models.indicator import Indicator


class Forecast(Base, TimestampMixin):
    """
    Healthcare Demand Forecast timeseries model with uncertainty bounds.
    """
    __tablename__ = "forecasts"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    facility_id: Mapped[str] = mapped_column(String(64), ForeignKey("facilities.id", ondelete="CASCADE"), index=True, nullable=False)
    indicator_id: Mapped[str] = mapped_column(String(64), ForeignKey("indicators.id", ondelete="CASCADE"), index=True, nullable=False)
    forecast_date: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    lower_bound: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    upper_bound: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    model_version: Mapped[str] = mapped_column(String(32), default="1.0.0", nullable=False)

    # Relationships
    facility: Mapped["Facility"] = relationship("Facility", back_populates="forecasts")
    indicator: Mapped["Indicator"] = relationship("Indicator", back_populates="forecasts")

    __table_args__ = (
        Index("idx_forecast_fac_ind_date", "facility_id", "indicator_id", "forecast_date"),
    )
