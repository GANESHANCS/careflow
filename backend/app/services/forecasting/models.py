import numpy as np
import pandas as pd
from typing import List, Optional
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor

from backend.app.services.forecasting.baselines import BaseForecaster
from backend.app.services.forecasting.features import TimeSeriesFeatureEngine, impute_training_series
from backend.app.services.forecasting.dataset import ForecastingSeries, ForecastingPoint


class SARIMAXForecaster(BaseForecaster):
    """
    SARIMAX (Seasonal Autoregressive Integrated Moving Average) model candidate.
    """
    def __init__(self, order=(1, 1, 1), seasonal_order=(1, 1, 0, 12)):
        super().__init__("SARIMAX")
        self.order = order
        self.seasonal_order = seasonal_order
        self.model_res = None

    def fit(self, history_values: List[float], history_dates: List[str]) -> "SARIMAXForecaster":
        self.history_values = [float(v) for v in history_values]
        self.history_dates = list(history_dates)
        n = len(self.history_values)

        if n >= 24:
            try:
                model = SARIMAX(
                    self.history_values,
                    order=self.order,
                    seasonal_order=self.seasonal_order,
                    enforce_stationarity=False,
                    enforce_invertibility=False
                )
                self.model_res = model.fit(disp=False)
            except Exception:
                try:
                    # Non-seasonal ARIMA fallback
                    model = SARIMAX(self.history_values, order=(1, 1, 1), enforce_stationarity=False)
                    self.model_res = model.fit(disp=False)
                except Exception:
                    self.model_res = None
        elif n >= 6:
            try:
                model = SARIMAX(self.history_values, order=(1, 1, 0), enforce_stationarity=False)
                self.model_res = model.fit(disp=False)
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

        # Fallback to last value if SARIMAX forecast fails
        fallback_val = float(self.history_values[-1]) if self.history_values else 0.0
        return [max(0.0, fallback_val)] * horizon


class SupervisedLagForecaster(BaseForecaster):
    """
    Base class for supervised regression ML forecasters with lag features.
    """
    def __init__(self, name: str, estimator):
        super().__init__(name)
        self.estimator = estimator

    def fit(self, history_values: List[float], history_dates: List[str]) -> "SupervisedLagForecaster":
        self.history_values = [float(v) for v in history_values]
        self.history_dates = list(history_dates)

        if len(self.history_values) < 6:
            self.is_fitted = False
            return self

        # Build synthetic ForecastingSeries for feature engineering
        points = [
            ForecastingPoint(
                observation_month=d[:7],
                observation_date=d if len(d) == 10 else f"{d[:7]}-01",
                observed_value=v,
                is_missing=False
            )
            for d, v in zip(self.history_dates, self.history_values)
        ]
        series = ForecastingSeries(
            facility_id="fit_fac",
            facility_name="Fit Facility",
            indicator_code="IND",
            points=points
        )

        X, y = TimeSeriesFeatureEngine.build_supervised_dataset(series)

        if len(X) > 0:
            try:
                self.estimator.fit(X, y)
                self.is_fitted = True
            except Exception:
                self.is_fitted = False
        else:
            self.is_fitted = False

        return self

    def predict(self, horizon: int) -> List[float]:
        if not self.is_fitted or not self.history_values:
            fallback = float(self.history_values[-1]) if self.history_values else 0.0
            return [max(0.0, fallback)] * horizon

        # Recursive multi-step forecasting
        running_values = list(self.history_values)
        running_dates = list(self.history_dates)

        # Generate future dates
        last_date = running_dates[-1]
        yr, mo = int(last_date[:4]), int(last_date[5:7])

        future_preds = []
        for step in range(1, horizon + 1):
            mo += 1
            if mo > 12:
                mo = 1
                yr += 1
            next_date_str = f"{yr:04d}-{mo:02d}-01"

            # Create features at cutoff t using running history
            feat_dict = TimeSeriesFeatureEngine.create_features_for_cutoff(
                values=running_values,
                dates=running_dates,
                cutoff_idx=len(running_values) - 1
            )
            X_next = pd.DataFrame([feat_dict])
            pred_val = float(self.estimator.predict(X_next)[0])
            pred_val = max(0.0, pred_val)

            future_preds.append(pred_val)
            running_values.append(pred_val)
            running_dates.append(next_date_str)

        return future_preds


class RidgeLagForecaster(SupervisedLagForecaster):
    """
    Ridge (L2 Linear Regression) forecaster with engineered lag features.
    """
    def __init__(self, alpha: float = 1.0):
        super().__init__("Ridge", Ridge(alpha=alpha))


class RandomForestLagForecaster(SupervisedLagForecaster):
    """
    Random Forest Regressor forecaster with engineered lag features.
    """
    def __init__(self, n_estimators: int = 50, random_state: int = 42):
        super().__init__("Random Forest", RandomForestRegressor(n_estimators=n_estimators, random_state=random_state))


class GradientBoostingLagForecaster(SupervisedLagForecaster):
    """
    Gradient Boosting Regressor forecaster with engineered lag features.
    """
    def __init__(self, n_estimators: int = 50, learning_rate: float = 0.05, random_state: int = 42):
        super().__init__("Gradient Boosting", GradientBoostingRegressor(n_estimators=n_estimators, learning_rate=learning_rate, random_state=random_state))
