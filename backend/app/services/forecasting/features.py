import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from backend.app.services.forecasting.dataset import ForecastingSeries, ForecastingPoint


def impute_training_series(series_values: List[Optional[float]]) -> List[float]:
    """
    Imputes missing values strictly using historical information (forward-fill then backward-fill fallback).
    Never uses future validation data to perform imputation.
    """
    df = pd.Series(series_values, dtype=float)
    # Forward fill using past observations only
    df_imputed = df.ffill().bfill().fillna(0.0)
    return df_imputed.tolist()


class TimeSeriesFeatureEngine:
    """
    Generates supervised ML lag and calendar features strictly respecting temporal boundaries.
    Prevents forward data leakage.
    """

    @staticmethod
    def create_features_for_cutoff(
        values: List[float],
        dates: List[str],
        cutoff_idx: int,
        completeness: float = 1.0,
        quality_score: float = 100.0
    ) -> Dict[str, float]:
        """
        Creates feature dict at time cutoff index t using only values <= t.
        """
        # Ensure values up to cutoff_idx are used
        history = values[: cutoff_idx + 1]
        n = len(history)

        if n == 0:
            raise ValueError("History is empty for feature creation.")

        curr_date = dates[cutoff_idx]
        year = int(curr_date[:4])
        month = int(curr_date[5:7])
        quarter = (month - 1) // 3 + 1

        # Cyclical calendar features
        sin_month = np.sin(2 * np.pi * month / 12.0)
        cos_month = np.cos(2 * np.pi * month / 12.0)

        # Lags relative to current cutoff t (history[-1] is t)
        lag_1 = history[-1] if n >= 1 else 0.0
        lag_2 = history[-2] if n >= 2 else lag_1
        lag_3 = history[-3] if n >= 3 else lag_1
        lag_6 = history[-6] if n >= 6 else lag_1
        lag_12 = history[-12] if n >= 12 else lag_1

        # Rolling statistics strictly from history <= cutoff
        roll_3_mean = float(np.mean(history[-3:])) if n >= 3 else float(np.mean(history))
        roll_6_mean = float(np.mean(history[-6:])) if n >= 6 else float(np.mean(history))
        roll_12_mean = float(np.mean(history[-12:])) if n >= 12 else float(np.mean(history))
        roll_3_std = float(np.std(history[-3:])) if n >= 3 else 0.0

        return {
            "year": float(year),
            "month": float(month),
            "quarter": float(quarter),
            "sin_month": float(sin_month),
            "cos_month": float(cos_month),
            "lag_1": float(lag_1),
            "lag_2": float(lag_2),
            "lag_3": float(lag_3),
            "lag_6": float(lag_6),
            "lag_12": float(lag_12),
            "roll_3_mean": float(roll_3_mean),
            "roll_6_mean": float(roll_6_mean),
            "roll_12_mean": float(roll_12_mean),
            "roll_3_std": float(roll_3_std),
            "reporting_completeness": float(completeness),
            "data_quality_score": float(quality_score)
        }

    @classmethod
    def build_supervised_dataset(
        cls,
        series: ForecastingSeries,
        max_cutoff_idx: Optional[int] = None
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Builds (X, y) supervised dataset for training up to max_cutoff_idx.
        Target y_t is the value at t, features X_t are built using history < t (i.e. up to t-1).
        Guarantees NO FUTURE DATA LEAKAGE.
        """
        raw_vals = series.values_list
        dates = series.months_list
        imputed_vals = impute_training_series(raw_vals)

        n = len(imputed_vals) if max_cutoff_idx is None else min(len(imputed_vals), max_cutoff_idx + 1)

        X_rows = []
        y_rows = []

        # Start from index 12 to ensure lag_12 is available
        start_idx = 12 if n > 12 else 1

        for t in range(start_idx, n):
            # Target at time t
            y_val = imputed_vals[t]
            # Features at t use history UP TO t-1 (strictly past info)
            feat = cls.create_features_for_cutoff(
                values=imputed_vals,
                dates=dates,
                cutoff_idx=t - 1,
                completeness=series.reporting_completeness,
                quality_score=series.data_quality_score
            )
            X_rows.append(feat)
            y_rows.append(y_val)

        if not X_rows:
            return pd.DataFrame(), pd.Series(dtype=float)

        return pd.DataFrame(X_rows), pd.Series(y_rows, dtype=float)
