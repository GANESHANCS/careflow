from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HistoricalPointSchema(BaseModel):
    observation_month: str
    observation_date: str
    observed_value: Optional[float] = None
    is_missing: bool = False
    is_imputed: bool = False
    status: Optional[str] = None


class CandidateEvaluationSchema(BaseModel):
    model_name: str
    is_baseline: bool
    mae: float
    rmse: float
    smape: float
    wape: float


class ForecastPointSchema(BaseModel):
    forecast_month: str
    forecast_date: str
    predicted_value: float
    lower_bound: float
    upper_bound: float


class ModelMetricsSchema(BaseModel):
    model_version: str
    model_type: str
    target_indicator: str
    training_start: str
    training_end: str
    mae: Optional[float] = None
    rmse: Optional[float] = None
    mape: Optional[float] = None
    baseline_mae: Optional[float] = None
    improvement_over_baseline_pct: Optional[float] = None
    created_at: Optional[str] = None


class ForecastResponseSchema(BaseModel):
    status: str
    facility: Dict[str, Any]
    indicator: Dict[str, Any]
    forecast_horizon: int
    model: Optional[Dict[str, Any]] = None
    training_period: Optional[Dict[str, Any]] = None
    historical_points: List[HistoricalPointSchema] = Field(default_factory=list)
    forecast_points: List[ForecastPointSchema] = Field(default_factory=list)
    prediction_intervals: Optional[Dict[str, Any]] = None
    validation_metrics: Optional[Dict[str, Any]] = None
    baseline_metrics: Optional[Dict[str, Any]] = None
    candidate_evaluations: List[CandidateEvaluationSchema] = Field(default_factory=list)
    improvement_over_baseline_pct: Optional[float] = None
    eligibility: Dict[str, Any]
    data_quality: Optional[Dict[str, Any]] = None
    explainability: Optional[Dict[str, Any]] = None
    disclaimer: str

