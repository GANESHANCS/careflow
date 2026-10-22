import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation


@pytest.fixture
def seed_api_data(db_session: Session):
    """Seeds test observations for API integration testing."""
    months = [
        ("2015-04", 1000.0), ("2015-05", 1020.0), ("2015-06", 980.0),
        ("2015-07", 1010.0), ("2015-08", 990.0), ("2015-09", 1030.0),
        ("2015-10", 970.0), ("2015-11", 1040.0), ("2015-12", 1000.0),
        ("2016-01", 1015.0), ("2016-02", 995.0), ("2016-03", 1050.0)
    ]
    obs = []
    for m, val in months:
        obs.append(
            DistrictObservation(
                id=f"DOBS_P14_API_Ariyalur_{m}",
                state="Tamil Nadu",
                district="Ariyalur",
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
                source_file="test_api.csv",
                ingested_at="2026-10-22T00:00:00Z"
            )
        )
    # Seed ambiguous indicator
    obs.append(
        DistrictObservation(
            id="DOBS_P14_API_Ambig",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.10.1.c",
            parameter_name="Inpatient admissions",
            subgroup_type="1. Children",
            is_subgroup_total=False,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=300.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test_api.csv",
            ingested_at="2026-10-22T00:00:00Z"
        )
    )
    db_session.add_all(obs)
    db_session.commit()


def test_intelligence_endpoints_require_authentication(client: TestClient):
    """Confirms all three intelligence endpoints return HTTP 401 Unauthorized when unauthenticated."""
    res1 = client.get("/api/analytics/district/intelligence/overview?district=Ariyalur&s_no=1.1")
    assert res1.status_code == 401

    res2 = client.get("/api/analytics/district/intelligence/readiness?district=Ariyalur&s_no=1.1")
    assert res2.status_code == 401

    res3 = client.get("/api/analytics/district/intelligence/anomalies?district=Ariyalur&s_no=1.1")
    assert res3.status_code == 401


def test_intelligence_overview_rejects_ambiguous_indicator(client: TestClient, auth_headers: dict, seed_api_data):
    """Confirms /intelligence/overview returns HTTP 400 Bad Request when passed ambiguous indicator 14.10.1.c."""
    res = client.get(
        "/api/analytics/district/intelligence/overview?district=Ariyalur&s_no=14.10.1.c",
        headers=auth_headers
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "AMBIGUOUS" in detail
    assert "Only VERIFIED indicators are eligible" in detail


def test_intelligence_overview_success(client: TestClient, auth_headers: dict, seed_api_data):
    """Confirms /intelligence/overview succeeds for verified indicator 1.1 with full metadata."""
    res = client.get(
        "/api/analytics/district/intelligence/overview?district=Ariyalur&s_no=1.1",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["s_no"] == "1.1"
    assert data["canonical_id"] == "IND_antenatal_visits"
    assert data["mapping_status"] == "VERIFIED"
    assert data["total_expected_months"] == 12
    assert data["reported_months_count"] == 12
    assert data["completeness_ratio"] == 1.0
    assert len(data["points"]) == 12


def test_forecasting_readiness_endpoint(client: TestClient, auth_headers: dict, seed_api_data):
    """Confirms /intelligence/readiness returns baseline evaluation for horizon=3 and insufficient-history for horizon=12."""
    # Short horizon (3m) -> Eligible
    res3 = client.get(
        "/api/analytics/district/intelligence/readiness?district=Ariyalur&s_no=1.1&horizon=3",
        headers=auth_headers
    )
    assert res3.status_code == 200
    d3 = res3.json()
    assert d3["is_ready"] is True
    assert d3["readiness_status"] == "ELIGIBLE_FOR_BASELINE_EVALUATION"
    assert d3["training_period"]["months_count"] == 9
    assert d3["evaluation_period"]["months_count"] == 3
    assert len(d3["baseline_forecast"]) == 3

    # Long horizon (12m) -> Insufficient history
    res12 = client.get(
        "/api/analytics/district/intelligence/readiness?district=Ariyalur&s_no=1.1&horizon=12",
        headers=auth_headers
    )
    assert res12.status_code == 200
    d12 = res12.json()
    assert d12["is_ready"] is False
    assert d12["readiness_status"] == "INSUFFICIENT_HISTORY"


def test_anomalies_endpoint_success(client: TestClient, auth_headers: dict, seed_api_data):
    """Confirms /intelligence/anomalies returns structured response with governance disclaimers."""
    res = client.get(
        "/api/analytics/district/intelligence/anomalies?district=Ariyalur&s_no=1.1",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert "total_signals_detected" in data
    assert "signals" in data
    assert "evaluation_summary" in data
    assert "governance_disclaimer" in data
    assert "Median Absolute Deviation" in data["governance_disclaimer"]
