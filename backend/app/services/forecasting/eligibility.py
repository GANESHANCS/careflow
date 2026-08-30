from typing import Optional, Dict, Any
from pydantic import BaseModel
from backend.app.services.forecasting.dataset import ForecastingSeries


class EligibilityResult(BaseModel):
    """
    Structured time-series eligibility result.
    """
    is_eligible: bool
    status: str  # ELIGIBLE or NOT_ELIGIBLE
    reason_code: Optional[str] = None  # e.g. INSUFFICIENT_HISTORY, EXCESSIVE_MISSINGNESS
    reason_message: str
    details: Dict[str, Any] = {}


class EligibilityEvaluator:
    """
    Determines whether a time-series has sufficient length and quality for model training.
    """
    def __init__(
        self,
        min_observations: int = 12,
        min_seasonal_observations: int = 24,
        max_missing_ratio: float = 0.30,
        max_consecutive_gaps: int = 3,
        min_reporting_completeness: float = 0.70
    ):
        self.min_observations = min_observations
        self.min_seasonal_observations = min_seasonal_observations
        self.max_missing_ratio = max_missing_ratio
        self.max_consecutive_gaps = max_consecutive_gaps
        self.min_reporting_completeness = min_reporting_completeness

    def evaluate(self, series: ForecastingSeries, forecast_horizon: int = 12) -> EligibilityResult:
        total_obs = series.total_observations
        missing_count = series.missing_count
        valid_count = series.valid_observations_count

        # 1. Total observations check
        if total_obs < self.min_observations:
            return EligibilityResult(
                is_eligible=False,
                status="NOT_ELIGIBLE",
                reason_code="INSUFFICIENT_HISTORY",
                reason_message=f"Series has only {total_obs} observation(s), minimum required is {self.min_observations}.",
                details={"total_observations": total_obs, "required": self.min_observations}
            )

        # 2. Primary 12-month horizon seasonal history check
        if forecast_horizon == 12 and total_obs < self.min_seasonal_observations:
            return EligibilityResult(
                is_eligible=False,
                status="NOT_ELIGIBLE",
                reason_code="INSUFFICIENT_SEASONAL_HISTORY",
                reason_message=f"For a 12-month forecast horizon, at least {self.min_seasonal_observations} months of history are required (series has {total_obs}).",
                details={"total_observations": total_obs, "required": self.min_seasonal_observations}
            )

        # 3. Missing ratio check
        missing_ratio = missing_count / total_obs if total_obs > 0 else 1.0
        if missing_ratio > self.max_missing_ratio:
            return EligibilityResult(
                is_eligible=False,
                status="NOT_ELIGIBLE",
                reason_code="EXCESSIVE_MISSINGNESS",
                reason_message=f"Missing observation ratio ({missing_ratio:.1%}) exceeds maximum threshold ({self.max_missing_ratio:.1%}).",
                details={"missing_ratio": round(missing_ratio, 3), "max_allowed": self.max_missing_ratio}
            )

        # 4. Consecutive missing gaps check
        current_gap = 0
        max_gap = 0
        for pt in series.points:
            if pt.is_missing or pt.observed_value is None:
                current_gap += 1
                if current_gap > max_gap:
                    max_gap = current_gap
            else:
                current_gap = 0

        if max_gap > self.max_consecutive_gaps:
            return EligibilityResult(
                is_eligible=False,
                status="NOT_ELIGIBLE",
                reason_code="EXCESSIVE_GAPS",
                reason_message=f"Max consecutive missing months ({max_gap}) exceeds allowed limit ({self.max_consecutive_gaps}).",
                details={"max_consecutive_gaps": max_gap, "allowed": self.max_consecutive_gaps}
            )

        # 5. Reporting completeness check
        if series.reporting_completeness < self.min_reporting_completeness:
            return EligibilityResult(
                is_eligible=False,
                status="NOT_ELIGIBLE",
                reason_code="LOW_REPORTING_COMPLETENESS",
                reason_message=f"Reporting completeness ({series.reporting_completeness:.1%}) is below minimum threshold ({self.min_reporting_completeness:.1%}).",
                details={"reporting_completeness": round(series.reporting_completeness, 3), "required": self.min_reporting_completeness}
            )

        return EligibilityResult(
            is_eligible=True,
            status="ELIGIBLE",
            reason_code=None,
            reason_message="Series meets all time-series forecasting eligibility criteria.",
            details={
                "total_observations": total_obs,
                "valid_observations": valid_count,
                "missing_ratio": round(missing_ratio, 3),
                "max_consecutive_gaps": max_gap,
                "reporting_completeness": round(series.reporting_completeness, 3)
            }
        )
