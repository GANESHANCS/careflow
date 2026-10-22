import pytest
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.analytics.healthcare_intelligence import HealthcareIntelligenceService


@pytest.fixture
def seed_full_12_months_data(db_session: Session):
    """Seeds full 12 months of observations for Ariyalur indicator 1.1."""
    vals = [1033.0, 1015.0, 959.0, 1019.0, 948.0, 1024.0, 1016.0, 946.0, 1026.0, 1034.0, 1000.0, 1110.0]
    months = [
        "2015-04", "2015-05", "2015-06", "2015-07",
        "2015-08", "2015-09", "2015-10", "2015-11",
        "2015-12", "2016-01", "2016-02", "2016-03"
    ]
    obs = []
    for m, v in zip(months, vals):
        obs.append(
            DistrictObservation(
                id=f"DOBS_P14_FR_{m}",
                state="Tamil Nadu",
                district="Ariyalur",
                s_no="1.1",
                parameter_name="Total number of pregnant women Registered for ANC",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                financial_year="2015-16",
                reporting_month=m,
                observation_date=f"{m}-01",
                value=v,
                value_type="VALID",
                validation_status="VALIDATED",
                source_file="test.csv",
                ingested_at="2026-10-22T00:00:00Z"
            )
        )
    db_session.add_all(obs)
    db_session.commit()


def test_insufficient_history_for_long_horizon(db_session: Session, seed_full_12_months_data):
    """
    Confirms that requesting horizon > 3 (e.g. 12 months) on single-year data
    transparently returns is_ready=False and INSUFFICIENT_HISTORY rather than a fabricated forecast.
    """
    service = HealthcareIntelligenceService(db_session)
    res = service.evaluate_forecasting_readiness(
        district="Ariyalur",
        s_no="1.1",
        horizon=12,
        financial_year="2015-16"
    )

    assert res.is_ready is False
    assert res.readiness_status == "INSUFFICIENT_HISTORY"
    assert "requires at least 24 months" in res.readiness_reason
    assert "Single-year data cannot establish reliable multi-year seasonal cycles" in res.dataset_limitation
    assert len(res.baseline_forecast) == 0


def test_chronological_split_and_zero_future_leakage(db_session: Session, seed_full_12_months_data):
    """
    Verifies expanding-window chronological separation:
    For horizon=3: train window is 9 months, hold-out evaluation window is 3 months.
    Guarantees train_end < eval_start and zero future data leakage.
    """
    service = HealthcareIntelligenceService(db_session)
    res = service.evaluate_forecasting_readiness(
        district="Ariyalur",
        s_no="1.1",
        horizon=3,
        financial_year="2015-16"
    )

    assert res.is_ready is True
    assert res.readiness_status == "ELIGIBLE_FOR_BASELINE_EVALUATION"

    # Train / Eval periods
    assert res.training_period is not None
    assert res.training_period["start_month"] == "2015-04"
    assert res.training_period["end_month"] == "2015-12"
    assert res.training_period["months_count"] == 9

    assert res.evaluation_period is not None
    assert res.evaluation_period["start_month"] == "2016-01"
    assert res.evaluation_period["end_month"] == "2016-03"
    assert res.evaluation_period["months_count"] == 3

    # Strict chronological boundary check
    assert res.training_period["end_month"] < res.evaluation_period["start_month"]

    # Verify baseline models evaluated on hold-out
    assert len(res.baseline_models_evaluated) == 3
    model_names = [m["model_name"] for m in res.baseline_models_evaluated]
    assert "Naive Forecaster" in model_names
    assert "Moving Average (3m)" in model_names
    assert "Linear Drift" in model_names

    # Ground truth in evaluation should be [1034.0, 1000.0, 1110.0]
    for m in res.baseline_models_evaluated:
        assert m["ground_truth"] == [1034.0, 1000.0, 1110.0]
        assert "mae" in m["evaluation_metrics"]
        assert "rmse" in m["evaluation_metrics"]


def test_forward_forecast_with_conservative_bounds(db_session: Session, seed_full_12_months_data):
    """
    Verifies that the winning baseline model generates forward predictions
    with conservative 95% uncertainty intervals and clinical disclaimers.
    """
    service = HealthcareIntelligenceService(db_session)
    res = service.evaluate_forecasting_readiness(
        district="Ariyalur",
        s_no="1.1",
        horizon=3,
        financial_year="2015-16"
    )

    assert res.is_ready is True
    assert res.selected_baseline_model is not None
    assert len(res.baseline_forecast) == 3

    # Forward months must be 2016-04, 2016-05, 2016-06
    months = [f["month"] for f in res.baseline_forecast]
    assert months == ["2016-04", "2016-05", "2016-06"]

    for pt in res.baseline_forecast:
        assert pt["predicted_value"] >= 0.0
        assert pt["lower_bound"] <= pt["predicted_value"]
        assert pt["upper_bound"] >= pt["predicted_value"]

    assert "not clinically validated" in res.clinical_validation_disclaimer.lower()


def test_excessive_missingness_handling(db_session: Session):
    """Verifies that time series with only 4 observations is rejected for forecasting."""
    obs = []
    for mo in ["2015-04", "2015-05", "2015-06", "2015-07"]:
        obs.append(
            DistrictObservation(
                id=f"DOBS_P14_MISS_{mo}",
                state="Tamil Nadu",
                district="Ariyalur",
                s_no="1.1",
                parameter_name="ANC registration",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                financial_year="2015-16",
                reporting_month=mo,
                observation_date=f"{mo}-01",
                value=500.0,
                value_type="VALID",
                validation_status="VALIDATED",
                source_file="test.csv",
                ingested_at="2026-10-22T00:00:00Z"
            )
        )
    db_session.add_all(obs)
    db_session.commit()

    service = HealthcareIntelligenceService(db_session)
    res = service.evaluate_forecasting_readiness(
        district="Ariyalur",
        s_no="1.1",
        horizon=3,
        financial_year="2015-16"
    )

    assert res.is_ready is False
    assert res.readiness_status == "EXCESSIVE_MISSINGNESS"
    assert "minimum required is 9" in res.readiness_reason
