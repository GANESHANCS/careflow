from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.db.models.observation import Observation
    from backend.app.db.models.forecast import Forecast


class Facility(Base, TimestampMixin):
    """
    Facility Entity representing hospitals, PHCs, CHCs, DHs, and health centers.
    """
    __tablename__ = "facilities"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    facility_code: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    facility_name: Mapped[str] = mapped_column(String(255), nullable=False)
    facility_type: Mapped[str] = mapped_column(String(64), default="UNKNOWN", index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(128), default="India", index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(128), default="Unknown District", index=True, nullable=False)
    sub_district: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    raw_facility_name: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_district_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # Relationships
    observations: Mapped[List["Observation"]] = relationship("Observation", back_populates="facility", cascade="all, delete-orphan")
    forecasts: Mapped[List["Forecast"]] = relationship("Forecast", back_populates="facility", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_facility_state_district", "state", "district"),
    )
