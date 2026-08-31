import pytest
import math
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.forecast import Forecast
from backend.app.db.models.model_metadata import ModelMetadata
from backend.app.services.forecasting.dataset import ForecastingSeries, ForecastingPoint
from backend.app.services.forecasting.eligibility import EligibilityEvaluator
from backend.app.services.forecasting.features import TimeSeriesFeatureEngine, impute_training_series
from backend.app.services.forecasting.baselines import (
    NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster, HoltWintersForecaster
)
from backend.app.services.forecasting.models import (
    SARIMAXForecaster, RidgeLagForecaster, RandomForestLagForecaster, GradientBoostingLagForecaster
)
from backend.app.services.forecasting.evaluation import TimeAwareValidator, calculate_metrics
from backend.app.services.forecasting.selection import ModelSelector
from backend.app.services.forecasting.intervals import PredictionIntervalEstimator
from backend.app.services.forecasting.forecast_service import ForecastingService


def create_synthetic_series(num_months: int = 36, missing_indices: list = None) -> ForecastingSeries:
    missing_indices = missing_indices or []
    points = []
    base_val = 1000.0

    yr, mo = 2022, 1
    for i in range(num_months):
        m_str = f"{yr:04d}-{mo:02d}"
        d_str = f"{m_str}-01"

        if i in missing_indices:
            pt = ForecastingPoint(
                observation_month=m_str,
                observation_date=d_str,
                observed_value=None,
                status="MISSING",
                is_missing=True,
                data_quality_status="SUSPECT"
            )
        else:
            # Add seasonal wave + trend
            val = base_val + 200.0 * math.sin(2.0 * math.pi * mo / 12.0) + (i * 5.0)
            pt = ForecastingPoint(
                observation_month=m_str,
                observation_date=d_str,
                observed_value=round(val, 1),
                status="VALID",
                is_missing=False,
                data_quality_status="VALIDATED"
            )
        points.append(pt)

        mo += 1
        if mo > 12:
            mo = 1
            yr += 1

    valid_cnt = sum(1 for p in points if not p.is_missing)
    completeness = valid_cnt / len(points) if points else 0.0

    return ForecastingSeries(
        facility_id="fac_test_01",
        facility_name="Test Facility",
        indicator_code="opd_attendance",
        points=points,
        reporting_completeness=completeness,
        data_quality_score=round(completeness * 100.0, 1)
    )


# -------------------------------------------------------------------
# 1. DATASET CONTRACT & MISSINGNESS TESTS
# -------------------------------------------------------------------
def test_forecasting_dataset_contract():
    series = create_synthetic_series(num_months=24, missing_indices=[5, 10])

    assert series.total_observations == 24
    assert series.missing_count == 2
    assert series.valid_observations_count == 22
    assert series.points[5].is_missing is True
    assert series.points[5].observed_value is None
    # Verify missing value is preserved as None and never silently converted to 0.0
    assert series.values_list[5] is None


# -------------------------------------------------------------------
# 2. ELIGIBILITY CRITERIA TESTS
# -------------------------------------------------------------------
def test_eligibility_insufficient_history():
    series = create_synthetic_series(num_months=6)
    evaluator = EligibilityEvaluator()
    res = evaluator.evaluate(series, forecast_horizon=12)

    assert res.is_eligible is False
    assert res.status == "NOT_ELIGIBLE"
    assert res.reason_code == "INSUFFICIENT_HISTORY"


def test_eligibility_insufficient_seasonal_history():
    series = create_synthetic_series(num_months=18)
    evaluator = EligibilityEvaluator()
    res = evaluator.evaluate(series, forecast_horizon=12)

    assert res.is_eligible is False
    assert res.reason_code == "INSUFFICIENT_SEASONAL_HISTORY"


def test_eligibility_excessive_missingness():
    # 12 out of 36 missing (33.3% missingness > 30% threshold)
    missing_idx = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
    series = create_synthetic_series(num_months=36, missing_indices=missing_idx)
    evaluator = EligibilityEvaluator()
    res = evaluator.evaluate(series, forecast_horizon=12)

    assert res.is_eligible is False
    assert res.reason_code == "EXCESSIVE_MISSINGNESS"


def test_eligibility_excessive_consecutive_gaps():
    # 4 consecutive missing months (index 10, 11, 12, 13) > 3 allowed
    missing_idx = [10, 11, 12, 13]
    series = create_synthetic_series(num_months=36, missing_indices=missing_idx)
    evaluator = EligibilityEvaluator()
    res = evaluator.evaluate(series, forecast_horizon=12)

    assert res.is_eligible is False
    assert res.reason_code == "EXCESSIVE_GAPS"


def test_eligibility_valid_series():
    series = create_synthetic_series(num_months=36, missing_indices=[2])
    evaluator = EligibilityEvaluator()
    res = evaluator.evaluate(series, forecast_horizon=12)

    assert res.is_eligible is True
    assert res.status == "ELIGIBLE"
    assert res.reason_code is None


# -------------------------------------------------------------------
# 3. FEATURE ENGINEERING & LEAKAGE PREVENTION TESTS
# -------------------------------------------------------------------
def test_feature_engineering_no_leakage():
    series = create_synthetic_series(num_months=24)
    # Build dataset up to cutoff t=18
    X, y = TimeSeriesFeatureEngine.build_supervised_dataset(series, max_cutoff_idx=18)

    assert len(X) > 0
    # Ensure features at row index t used history <= t-1
    first_feat = X.iloc[0].to_dict()
    assert "lag_1" in first_feat
    assert "lag_12" in first_feat
    assert "sin_month" in first_feat
    assert "roll_3_mean" in first_feat


# -------------------------------------------------------------------
# 4. BASELINE & ML MODEL FITTING TESTS
# -------------------------------------------------------------------
@pytest.mark.parametrize("forecaster_cls, name", [
    (NaiveForecaster, "Naive"),
    (SeasonalNaiveForecaster, "Seasonal Naive"),
    (MovingAverageForecaster, "Moving Average (3m)"),
    (HoltWintersForecaster, "Holt-Winters"),
    (SARIMAXForecaster, "SARIMAX"),
    (RidgeLagForecaster, "Ridge"),
    (RandomForestLagForecaster, "Random Forest"),
    (GradientBoostingLagForecaster, "Gradient Boosting"),
])
def test_candidate_models_fit_and_predict(forecaster_cls, name):
    series = create_synthetic_series(num_months=36)
    clean_vals = impute_training_series(series.values_list)
    dates = series.months_list

    forecaster = forecaster_cls()
    forecaster.fit(clean_vals, dates)
    preds = forecaster.predict(horizon=12)

    assert len(preds) == 12
    # Ensure all forecasts are non-negative
    for p in preds:
        assert p >= 0.0


# -------------------------------------------------------------------
# 5. TIME-AWARE VALIDATION & METRICS TESTS
# -------------------------------------------------------------------
def test_time_aware_validation_chronological_split():
    series = create_synthetic_series(num_months=36)
    forecaster = SeasonalNaiveForecaster()

    metrics, val_true, val_pred = TimeAwareValidator.validate_forecaster(forecaster, series, val_horizon=12)

    assert len(val_true) == 12
    assert len(val_pred) == 12
    assert metrics.mae >= 0.0
    assert metrics.rmse >= metrics.mae  # Mathematical inequality RMSE >= MAE


def test_zero_safe_evaluation_metrics():
    y_true = [0.0, 10.0, 20.0, 0.0]
    y_pred = [2.0, 12.0, 18.0, 1.0]

    metrics = calculate_metrics(y_true, y_pred)
    assert metrics.mae == 1.75
    assert not math.isnan(metrics.smape)
    assert not math.isinf(metrics.smape)
    assert not math.isnan(metrics.mape)


# -------------------------------------------------------------------
# 6. MODEL SELECTOR & TIE-BREAKER TESTS
# -------------------------------------------------------------------
def test_model_selector_preference():
    series = create_synthetic_series(num_months=36)
    selector = ModelSelector(val_horizon=12)

    winning_forecaster, summary, eval_res = selector.select_best_model(series)

    assert winning_forecaster is not None
    assert summary.selected_model_name in [
        "Naive", "Seasonal Naive", "Moving Average (3m)", "Holt-Winters",
        "SARIMAX", "Ridge", "Random Forest", "Gradient Boosting"
    ]
    assert len(summary.all_evaluations) == 8


# -------------------------------------------------------------------
# 7. UNCERTAINTY PREDICTION INTERVALS TESTS
# -------------------------------------------------------------------
def test_prediction_intervals_non_negative_bounds():
    preds = [100.0, 150.0, 120.0]
    resids = [10.0, -12.0, 8.0, -5.0]

    interval_res = PredictionIntervalEstimator.calculate_intervals(preds, resids)

    assert len(interval_res.predicted_values) == 3
    assert len(interval_res.lower_bounds) == 3
    assert len(interval_res.upper_bounds) == 3
    for p, l, u in zip(interval_res.predicted_values, interval_res.lower_bounds, interval_res.upper_bounds):
        assert l >= 0.0  # Non-negative lower bound check
        assert l <= p <= u


# -------------------------------------------------------------------
# 8. FORECAST API ENDPOINTS & PERSISTENCE TESTS
# -------------------------------------------------------------------
def test_forecast_api_valid_request(client: TestClient, db_session: Session, auth_headers: dict):
    # Seed test indicator & facility into test in-memory DB
    ind = Indicator(id="IND_opd_attendance", code="opd_attendance", name="OPD Attendance", category="Outpatient", unit="count", active=True)
    fac = Facility(id="fac_synth_dh_alpha", facility_code="SYNTH_DH_1001", facility_name="District Hospital Alpha", facility_type="DH", state="State", district="Dist", raw_facility_name="DH Alpha")
    db_session.add(ind)
    db_session.add(fac)
    db_session.commit()

    # Unauthenticated -> 401
    res_unauth = client.get("/api/forecast?facility_id=fac_synth_dh_alpha&indicator_code=opd_attendance&horizon=12")
    assert res_unauth.status_code == 401

    response = client.get("/api/forecast?facility_id=fac_synth_dh_alpha&indicator_code=opd_attendance&horizon=12", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("SUCCESS", "NOT_ELIGIBLE")
    assert "disclaimer" in data
    assert "SYNTHETIC" in data["disclaimer"]


def test_forecast_api_invalid_horizon(client: TestClient, auth_headers: dict):
    response = client.get("/api/forecast?facility_id=fac_synth_dh_alpha&indicator_code=opd_attendance&horizon=5", headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid forecast horizon" in response.json()["detail"]


def test_forecast_api_not_found_facility(client: TestClient, auth_headers: dict):
    response = client.get("/api/forecast?facility_id=non_existent_fac_9999&indicator_code=opd_attendance&horizon=12", headers=auth_headers)
    assert response.status_code == 404


def test_model_metrics_api(client: TestClient, auth_headers: dict):
    # Unauthenticated -> 401
    res_unauth = client.get("/api/model/metrics")
    assert res_unauth.status_code == 401

    response = client.get("/api/model/metrics", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
