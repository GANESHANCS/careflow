import numpy as np
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel

from backend.app.services.forecasting.dataset import ForecastingSeries
from backend.app.services.forecasting.baselines import BaseForecaster, NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster, HoltWintersForecaster
from backend.app.services.forecasting.features import impute_training_series


class EvaluationMetrics(BaseModel):
    """
    Time-series model evaluation metrics.
    """
    mae: float
    rmse: float
    smape: float
    wape: float
    mape: float


def calculate_metrics(y_true: List[float], y_pred: List[float]) -> EvaluationMetrics:
    """
    Calculates MAE, RMSE, sMAPE, WAPE, and zero-safe MAPE metrics.
    """
    arr_true = np.array(y_true, dtype=float)
    arr_pred = np.array(y_pred, dtype=float)
    n = len(arr_true)

    if n == 0:
        return EvaluationMetrics(mae=0.0, rmse=0.0, smape=0.0, wape=0.0, mape=0.0)

    errors = arr_true - arr_pred
    abs_errors = np.abs(errors)

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(errors ** 2)))

    # sMAPE calculation with small epsilon to prevent divide-by-zero
    denom_smape = (np.abs(arr_true) + np.abs(arr_pred)) / 2.0 + 1e-8
    smape = float(np.mean(abs_errors / denom_smape) * 100.0)

    # WAPE calculation
    sum_true = float(np.sum(np.abs(arr_true)))
    wape = float((np.sum(abs_errors) / (sum_true + 1e-8)) * 100.0)

    # Zero-safe MAPE
    denom_mape = np.where(np.abs(arr_true) < 1e-5, 1.0, np.abs(arr_true))
    mape = float(np.mean(abs_errors / denom_mape) * 100.0)

    return EvaluationMetrics(
        mae=round(mae, 4),
        rmse=round(rmse, 4),
        smape=round(smape, 4),
        wape=round(wape, 4),
        mape=round(mape, 4)
    )


class TimeAwareValidator:
    """
    Performs expanding-window chronological validation guarantee no future data leakage.
    For every fold: training_end < validation_start.
    """

    @classmethod
    def validate_forecaster(
        cls,
        forecaster: BaseForecaster,
        series: ForecastingSeries,
        val_horizon: int = 12
    ) -> Tuple[EvaluationMetrics, List[float], List[float]]:
        """
        Validates forecaster on chronological holdout split.
        Splits series: history (0 .. N - val_horizon - 1) and test (N - val_horizon .. N - 1).
        """
        vals = series.values_list
        dates = series.months_list
        imputed_vals = impute_training_series(vals)
        n = len(imputed_vals)

        if n <= val_horizon:
            # Series too short for specified validation split; use last 3 months
            val_horizon = max(1, min(3, n - 1))

        train_cutoff = n - val_horizon
        train_vals = imputed_vals[:train_cutoff]
        train_dates = dates[:train_cutoff]
        val_true = imputed_vals[train_cutoff:]
        val_dates = dates[train_cutoff:]

        # Fit model ONLY on training values up to train_cutoff
        forecaster.fit(train_vals, train_dates)
        val_pred = forecaster.predict(len(val_true))

        metrics = calculate_metrics(val_true, val_pred)
        return metrics, val_true, val_pred
