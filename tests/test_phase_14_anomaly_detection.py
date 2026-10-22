import pytest
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.analytics.healthcare_intelligence import HealthcareIntelligenceService


@pytest.fixture
def seed_anomaly_test_data(db_session: Session):
    """
    Seeds isolated, deterministic synthetic test observations:
    - District 'Salem' indicator '1.1': 11 normal months (values 950-1050), Month 12 outlier (value 4500.0)
    - District 'Dharmapuri' indicator '1.1': 10 normal months, Month 11 missing, Month 12 abrupt jump (500 -> 2200)
    """
    obs = []
    months = [
        "2015-04", "2015-05", "2015-06", "2015-07",
        "2015-08", "2015-09", "2015-10", "2015-11",
        "2015-12", "2016-01", "2016-02", "2016-03"
    ]

    # Salem: stable baseline ~1000, 2016-03 is 4500.0
    for m in months:
        val = 4500.0 if m == "2016-03" else 1000.0
        obs.append(
            DistrictObservation(
                id=f"DOBS_P14_ANOM_Salem_{m}",
                state="Tamil Nadu",
                district="Salem",
                s_no="1.1",
                parameter_name="Total pregnant women registered for ANC",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                financial_year="2015-16",
                reporting_month=m,
                observation_date=f"{m}-01",
                value=val,
                value_type="VALID",
                validation_status="VALIDATED",
                source_file="synthetic_test.csv",
                ingested_at="2026-10-22T00:00:00Z"
            )
        )

    # Dharmapuri: missing 2016-02, and abrupt jump 500 -> 2200 at 2016-03
    for m in months:
        if m == "2016-02":
            continue  # Intentional missing month
        val = 2200.0 if m == "2016-03" else 500.0
        obs.append(
            DistrictObservation(
                id=f"DOBS_P14_ANOM_Dharmapuri_{m}",
                state="Tamil Nadu",
                district="Dharmapuri",
                s_no="1.1",
                parameter_name="Total pregnant women registered for ANC",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                financial_year="2015-16",
                reporting_month=m,
                observation_date=f"{m}-01",
                value=val,
                value_type="VALID",
                validation_status="VALIDATED",
                source_file="synthetic_test.csv",
                ingested_at="2026-10-22T00:00:00Z"
            )
        )

    db_session.add_all(obs)
    db_session.commit()


def test_mad_outlier_detection_with_synthetic_fixture(db_session: Session, seed_anomaly_test_data):
    """
    Confirms robust Median Absolute Deviation outlier detection flags 2016-03
    with modified Z-score > 3.5 without false positives on normal months.
    """
    service = HealthcareIntelligenceService(db_session)
    report = service.detect_anomalies(
        district="Salem",
        s_no="1.1",
        financial_year="2015-16"
    )

    mad_signals = [s for s in report.signals if s.signal_type == "HISTORICAL_OUTLIER_MAD"]
    assert len(mad_signals) == 1

    outlier = mad_signals[0]
    assert outlier.reporting_month == "2016-03"
    assert outlier.observed_value == 4500.0
    assert outlier.expected_baseline == 1000.0
    assert outlier.deviation_score > 3.5
    assert outlier.severity == "ELEVATED"
    assert "Median Absolute Deviation" in outlier.statistical_method
    assert "STATISTICAL_SIGNAL" in outlier.disclaimer


def test_missing_period_anomaly_detection(db_session: Session, seed_anomaly_test_data):
    """Verifies that missing calendar return in Dharmapuri triggers MISSING_REPORTING_PERIOD signal."""
    service = HealthcareIntelligenceService(db_session)
    report = service.detect_anomalies(
        district="Dharmapuri",
        s_no="1.1",
        financial_year="2015-16"
    )

    missing_signals = [s for s in report.signals if s.signal_type == "MISSING_REPORTING_PERIOD"]
    assert len(missing_signals) >= 1

    feb_sig = next(s for s in missing_signals if s.reporting_month == "2016-02")
    assert feb_sig.observed_value is None
    assert feb_sig.severity == "WARNING"
    assert "missing or unreported" in feb_sig.rationale


def test_month_over_month_abrupt_shift(db_session: Session, seed_anomaly_test_data):
    """Verifies that abrupt jump (500 -> 2200) triggers MONTH_OVER_MONTH_SHIFT signal."""
    service = HealthcareIntelligenceService(db_session)
    report = service.detect_anomalies(
        district="Dharmapuri",
        s_no="1.1",
        financial_year="2015-16"
    )

    mom_signals = [s for s in report.signals if s.signal_type == "MONTH_OVER_MONTH_SHIFT"]
    assert len(mom_signals) >= 1

    jump_sig = next(s for s in mom_signals if s.reporting_month == "2016-03")
    assert jump_sig.observed_value == 2200.0
    assert jump_sig.expected_baseline == 500.0
    assert jump_sig.deviation_score > 50.0  # Percentage change


def test_small_sample_safety_prevents_false_alarms(db_session: Session):
    """Verifies that time series with only 3 months does NOT generate spurious MAD outlier alarms."""
    obs = []
    for mo, val in [("2015-04", 100.0), ("2015-05", 200.0), ("2015-06", 150.0)]:
        obs.append(
            DistrictObservation(
                id=f"DOBS_P14_SMALL_{mo}",
                state="Tamil Nadu",
                district="Erode",
                s_no="1.1",
                parameter_name="ANC registration",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                financial_year="2015-16",
                reporting_month=mo,
                observation_date=f"{mo}-01",
                value=val,
                value_type="VALID",
                validation_status="VALIDATED",
                source_file="test.csv",
                ingested_at="2026-10-22T00:00:00Z"
            )
        )
    db_session.add_all(obs)
    db_session.commit()

    service = HealthcareIntelligenceService(db_session)
    report = service.detect_anomalies(
        district="Erode",
        s_no="1.1",
        financial_year="2015-16"
    )

    # MAD detector requires >= 6 months, so 0 MAD outliers should be produced
    mad_signals = [s for s in report.signals if s.signal_type == "HISTORICAL_OUTLIER_MAD"]
    assert len(mad_signals) == 0
