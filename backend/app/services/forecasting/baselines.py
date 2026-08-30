import numpy as np
from typing import List, Optional
from statsmodels.tsa.holtwinters import ExponentialSmoothing


class BaseForecaster:
    """
    Abstract Base Class for all Time-Series Forecasters.
    """
    def __init__(self, name: str):
        self.name = name
        self.is_fitted = False
        self.history_values: List[float] = []
        self.history_dates: List[str] = []

    def fit(self, history_values: List[float], history_dates: List[str]) -> "BaseForecaster":
        raise NotImplementedError

    def predict(self, horizon: int) -> List[float]:
        raise NotImplementedError


class NaiveForecaster(BaseForecaster):
    """
    Naive baseline: forecasts future value as equal to the most recent historical observation.
    """
    def __init__(self):
        super().__init__("Naive")

    def fit(self, history_values: List[float], history_dates: List[str]) -> "NaiveForecaster":
        self.history_values = [float(v) for v in history_values]
        self.history_dates = list(history_dates)
        self.is_fitted = True
        return self

    def predict(self, horizon: int) -> List[float]:
        if not self.history_values:
            return [0.0] * horizon
        last_val = self.history_values[-1]
        return [max(0.0, float(last_val))] * horizon


class SeasonalNaiveForecaster(BaseForecaster):
    """
    Seasonal Naive baseline: forecasts future month as equal to the observation from 12 months prior.
    """
    def __init__(self, season_length: int = 12):
        super().__init__("Seasonal Naive")
        self.season_length = season_length

    def fit(self, history_values: List[float], history_dates: List[str]) -> "SeasonalNaiveForecaster":
        self.history_values = [float(v) for v in history_values]
        self.history_dates = list(history_dates)
        self.is_fitted = True
        return self

    def predict(self, horizon: int) -> List[float]:
        n = len(self.history_values)
        if n == 0:
            return [0.0] * horizon

        preds = []
        for h in range(horizon):
            # Pick value from season_length ago in repeating cycle
            idx = n - self.season_length + (h % self.season_length)
            if idx >= 0 and idx < n:
                val = self.history_values[idx]
            else:
                val = self.history_values[-1]
            preds.append(max(0.0, float(val)))
        return preds


class MovingAverageForecaster(BaseForecaster):
    """
    Moving Average baseline: forecasts future values as the rolling average of the last K observations.
    """
    def __init__(self, window_size: int = 3):
        super().__init__(f"Moving Average ({window_size}m)")
        self.window_size = window_size

    def fit(self, history_values: List[float], history_dates: List[str]) -> "MovingAverageForecaster":
        self.history_values = [float(v) for v in history_values]
        self.history_dates = list(history_dates)
        self.is_fitted = True
        return self

    def predict(self, horizon: int) -> List[float]:
        if not self.history_values:
            return [0.0] * horizon

        window = self.history_values[-self.window_size:] if len(self.history_values) >= self.window_size else self.history_values
        avg_val = float(np.mean(window))
        return [max(0.0, avg_val)] * horizon


class HoltWintersForecaster(BaseForecaster):
    """
    Holt-Winters Exponential Smoothing baseline with trend and seasonality.
    """
    def __init__(self, seasonal_periods: int = 12):
        super().__init__("Holt-Winters")
        self.seasonal_periods = seasonal_periods
        self.model_res = None

    def fit(self, history_values: List[float], history_dates: List[str]) -> "HoltWintersForecaster":
        self.history_values = [float(v) for v in history_values]
        self.history_dates = list(history_dates)
        n = len(self.history_values)

        if n >= 2 * self.seasonal_periods:
            try:
                model = ExponentialSmoothing(
                    self.history_values,
                    trend="add",
                    seasonal="add",
                    seasonal_periods=self.seasonal_periods,
                    initialization_method="estimated"
                )
                self.model_res = model.fit()
            except Exception:
                # Fallback to additive trend without seasonal component if fit fails
                try:
                    model = ExponentialSmoothing(self.history_values, trend="add", initialization_method="estimated")
                    self.model_res = model.fit()
                except Exception:
                    self.model_res = None
        elif n >= 3:
            try:
                model = ExponentialSmoothing(self.history_values, trend="add", initialization_method="estimated")
                self.model_res = model.fit()
            except Exception:
                self.model_res = None
        else:
            self.model_res = None

        self.is_fitted = True
        return self

    def predict(self, horizon: int) -> List[float]:
        if self.model_res is not None:
            try:
                preds = self.model_res.forecast(horizon)
                return [max(0.0, float(p)) for p in preds]
            except Exception:
                pass

        # Fallback to Naive prediction if model fit/prediction failed
        fallback_val = float(self.history_values[-1]) if self.history_values else 0.0
        return [max(0.0, fallback_val)] * horizon
