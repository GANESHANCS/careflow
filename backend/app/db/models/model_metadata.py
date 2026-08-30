from typing import Optional, Any, Dict
from sqlalchemy import String, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.models.base import Base, TimestampMixin


class ModelMetadata(Base, TimestampMixin):
    """
    ML Forecasting Model Metadata and Registry tracking evaluation metrics.
    """
    __tablename__ = "model_metadata"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    model_version: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False)
    target_indicator: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    training_start: Mapped[str] = mapped_column(String(10), nullable=False)
    training_end: Mapped[str] = mapped_column(String(10), nullable=False)
    features: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    mae: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rmse: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mape: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    baseline_mae: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
