from typing import List, Optional
from pydantic import BaseModel, Field


class ForecastingPoint(BaseModel):
    """
    Standardized time-series observation data point preserving missingness semantics.
    """
    observation_month: str  # YYYY-MM
    observation_date: str   # YYYY-MM-01
    observed_value: Optional[float] = None
    status: str = "VALID"   # OBSERVED_ZERO, MISSING, INVALID, VALID, IMPUTED
    is_missing: bool = False
    is_imputed: bool = False
    data_quality_status: str = "VALIDATED"


class ForecastingSeries(BaseModel):
    """
    Standardized Forecasting Data Contract for facility/indicator time-series.
    """
    facility_id: str
    facility_name: str
    district: str = "Unknown"
    indicator_code: str
    points: List[ForecastingPoint] = Field(default_factory=list)
    reporting_completeness: float = 1.0  # 0.0 to 1.0
    data_quality_score: float = 100.0   # 0.0 to 100.0

    @property
    def total_observations(self) -> int:
        return len(self.points)

    @property
    def valid_observations_count(self) -> int:
        return sum(1 for p in self.points if not p.is_missing and p.observed_value is not None)

    @property
    def missing_count(self) -> int:
        return sum(1 for p in self.points if p.is_missing or p.observed_value is None)

    @property
    def values_list(self) -> List[Optional[float]]:
        return [p.observed_value for p in self.points]

    @property
    def months_list(self) -> List[str]:
        return [p.observation_month for p in self.points]
