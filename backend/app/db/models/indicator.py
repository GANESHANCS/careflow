from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.db.models.observation import Observation
    from backend.app.db.models.forecast import Forecast


class Indicator(Base, TimestampMixin):
    """
    Extensible HMIS Indicator Catalog Model.
    """
    __tablename__ = "indicators"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), default="count", nullable=False)
    source_system: Mapped[str] = mapped_column(String(64), default="HMIS", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    observations: Mapped[List["Observation"]] = relationship("Observation", back_populates="indicator", cascade="all, delete-orphan")
    forecasts: Mapped[List["Forecast"]] = relationship("Forecast", back_populates="indicator", cascade="all, delete-orphan")
