import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.db.models.model_metadata import ModelMetadata


class ForecastModelRegistry:
    """
    Persists and queries model evaluation metadata in the model_metadata registry table.
    """

    @staticmethod
    def register_model_metadata(
        db: Session,
        model_version: str,
        model_type: str,
        target_indicator: str,
        training_start: str,
        training_end: str,
        mae: float,
        rmse: float,
        mape: float,
        baseline_mae: float,
        features: Optional[Dict[str, Any]] = None
    ) -> ModelMetadata:
        record_id = f"meta_{model_version}_{target_indicator}"

        # Idempotent upsert logic
        existing = db.query(ModelMetadata).filter(ModelMetadata.id == record_id).first()
        if existing:
            existing.model_type = model_type
            existing.training_start = training_start
            existing.training_end = training_end
            existing.mae = mae
            existing.rmse = rmse
            existing.mape = mape
            existing.baseline_mae = baseline_mae
            existing.features = features
            record = existing
        else:
            record = ModelMetadata(
                id=record_id,
                model_version=model_version,
                model_type=model_type,
                target_indicator=target_indicator,
                training_start=training_start,
                training_end=training_end,
                mae=mae,
                rmse=rmse,
                mape=mape,
                baseline_mae=baseline_mae,
                features=features or {}
            )
            db.add(record)

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def get_latest_metadata(db: Session, target_indicator: Optional[str] = None) -> List[ModelMetadata]:
        query = db.query(ModelMetadata)
        if target_indicator:
            query = query.filter(ModelMetadata.target_indicator == target_indicator)
        return query.order_by(ModelMetadata.updated_at.desc()).all()
