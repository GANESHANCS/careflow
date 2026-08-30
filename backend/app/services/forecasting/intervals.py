import numpy as np
from typing import List
from pydantic import BaseModel


class PredictionIntervalResult(BaseModel):
    """
    Uncertainty prediction interval estimation result.
    """
    predicted_values: List[float]
    lower_bounds: List[float]
    upper_bounds: List[float]
    interval_type: str = "95% prediction interval (approximate)"
    residual_std_error: float


class PredictionIntervalEstimator:
    """
    Estimates ~95% prediction intervals based on historical validation residuals.
    Formula: y_hat +/- 1.96 * s_residual (with non-negative lower bound constraint).
    """

    @staticmethod
    def calculate_intervals(
        predictions: List[float],
        validation_residuals: List[float]
    ) -> PredictionIntervalResult:
        preds = [float(p) for p in predictions]

        if len(validation_residuals) > 1:
            res_std = float(np.std(validation_residuals, ddof=1))
        elif len(validation_residuals) == 1:
            res_std = abs(float(validation_residuals[0])) * 0.1
        else:
            # Default fallback 10% proportional standard error if residuals not available
            res_std = float(np.mean(preds)) * 0.1 if preds else 1.0

        res_std = max(res_std, 1e-4)
        z_multiplier = 1.96  # ~95% two-tailed normal critical value

        lower_bounds = [max(0.0, round(p - z_multiplier * res_std, 2)) for p in preds]
        upper_bounds = [round(p + z_multiplier * res_std, 2) for p in preds]

        return PredictionIntervalResult(
            predicted_values=[round(p, 2) for p in preds],
            lower_bounds=lower_bounds,
            upper_bounds=upper_bounds,
            residual_std_error=round(res_std, 4)
        )
