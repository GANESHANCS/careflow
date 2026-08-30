from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.forecast import ForecastResponseSchema, ModelMetricsSchema
from backend.app.services.forecasting import ForecastingService, ForecastModelRegistry

router = APIRouter()


@router.get("/forecast", response_model=ForecastResponseSchema, summary="Get Healthcare Demand Forecast")
def get_forecast(
    facility_id: str = Query(..., description="ID or Facility Code of the target facility"),
    indicator_code: str = Query("OPD_ATTENDANCE", description="HMIS Indicator Code (e.g. OPD_ATTENDANCE)"),
    horizon: int = Query(12, description="Forecast horizon in months (allowed: 3, 6, 12)"),
    db: Session = Depends(get_db)
):
    """
    Generates or retrieves monthly healthcare demand forecasts for a facility/indicator.
    Supports horizons of 3, 6, or 12 months (primary: 12 months).
    Returns prediction points, ~95% prediction intervals, validation metrics, baseline comparison, and explainability info.
    """
    if horizon not in (3, 6, 12):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid forecast horizon: {horizon}. Must be one of [3, 6, 12]."
        )

    res = ForecastingService.generate_forecast(
        db=db,
        facility_id=facility_id,
        indicator_code=indicator_code,
        horizon=horizon
    )

    if res.get("status") == "ERROR":
        error_code = res.get("error_code")
        if error_code in ("FACILITY_NOT_FOUND", "INDICATOR_NOT_FOUND"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=res.get("message")
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message")
        )

    return res


@router.get("/model/metrics", response_model=List[ModelMetricsSchema], summary="Get Model Registry Metrics")
def get_model_metrics(
    target_indicator: Optional[str] = Query(None, description="Optional filter by target indicator code"),
    db: Session = Depends(get_db)
):
    """
    Returns registered forecasting model metadata, evaluation metrics, and baseline improvement records.
    """
    records = ForecastModelRegistry.get_latest_metadata(db, target_indicator=target_indicator)
    results = []

    for r in records:
        base_mae = r.baseline_mae or 0.0
        mae = r.mae or 0.0
        imp_pct = ((base_mae - mae) / (base_mae + 1e-8)) * 100.0 if base_mae > 0 else 0.0

        results.append(
            ModelMetricsSchema(
                model_version=r.model_version,
                model_type=r.model_type,
                target_indicator=r.target_indicator,
                training_start=r.training_start,
                training_end=r.training_end,
                mae=r.mae,
                rmse=r.rmse,
                mape=r.mape,
                baseline_mae=r.baseline_mae,
                improvement_over_baseline_pct=round(imp_pct, 2),
                created_at=r.created_at.isoformat() if r.created_at else None
            )
        )

    return results
