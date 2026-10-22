"""
Tests for Phase 15 REST Endpoints:
- GET /api/analytics/district/intelligence/source-registry
- GET /api/analytics/district/intelligence/cross-year-comparability
- GET /api/analytics/district/intelligence/anomalies/reviews
- POST /api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.anomaly_review import DistrictAnomalyReview


@pytest.fixture
def seed_test_observation(db_session: Session):
    """Seeds a single observation for endpoint testing."""
    obs = DistrictObservation(
        id="DOBS_P15_Ariyalur_2015-04",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="1.1",
        parameter_name="Total pregnant women registered for ANC",
        subgroup_type="TOTAL",
        is_subgroup_total=True,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=1000.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="test.csv",
        ingested_at="2026-10-22T00:00:00Z"
    )
    db_session.add(obs)
    db_session.commit()


def test_source_registry_endpoint(client: TestClient, auth_headers: dict, seed_test_observation):
    """Verifies GET /intelligence/source-registry requires auth and returns registered source list."""
    unauth = client.get("/api/analytics/district/intelligence/source-registry")
    assert unauth.status_code == 401

    res = client.get("/api/analytics/district/intelligence/source-registry", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "Tamil Nadu"
    assert data["total_registered_years"] == 3
    assert len(data["sources"]) == 3
    assert any(s["financial_year"] == "2015-16" and s["status"] == "INGESTED" for s in data["sources"])
    assert any(s["financial_year"] == "2016-17" and s["status"] == "BLOCKED_MISSING_OFFICIAL_FILE" for s in data["sources"])


def test_cross_year_comparability_endpoint(client: TestClient, auth_headers: dict, seed_test_observation):
    """Verifies GET /intelligence/cross-year-comparability returns boundary and comparability analysis."""
    unauth = client.get("/api/analytics/district/intelligence/cross-year-comparability")
    assert unauth.status_code == 401

    res = client.get("/api/analytics/district/intelligence/cross-year-comparability", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "Tamil Nadu"
    assert "2015-16" in data["available_financial_years"]
    assert len(data["boundary_shifts_catalog"]) >= 6
    assert any(b["bifurcated_district"] == "Tenkasi" for b in data["boundary_shifts_catalog"])


def test_anomaly_review_action_endpoint_rbac(
    client: TestClient,
    auth_headers: dict,
    admin_auth_headers: dict,
    viewer_auth_headers: dict,
    seed_test_observation
):
    """Verifies POST /intelligence/anomalies/reviews/{signal_id}/action enforces RBAC and transitions."""
    sig_id = "SIG_EP_TEST_01"
    payload = {
        "action": "ACKNOWLEDGE",
        "notes": "Acknowledged by testing team",
        "district": "Ariyalur",
        "indicator_id": "1.1",
        "reporting_month": "2015-04",
        "signal_type": "MOM_SHIFT",
        "trigger_reason": "Test trigger reason",
        "metric_value": 1500.0,
        "expected_range": "[900.0 - 1100.0]"
    }

    # 1. Unauthenticated request
    unauth = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{sig_id}/action",
        json=payload
    )
    assert unauth.status_code == 401

    # 2. Viewer role request -> 403 Forbidden
    viewer_res = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{sig_id}/action",
        json=payload,
        headers=viewer_auth_headers
    )
    assert viewer_res.status_code == 403
    assert "not authorized" in viewer_res.json()["detail"].lower()

    # 3. Analyst role request -> 200 OK
    analyst_res = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{sig_id}/action",
        json=payload,
        headers=auth_headers
    )
    assert analyst_res.status_code == 200
    data = analyst_res.json()
    assert data["signal_id"] == sig_id
    assert data["current_status"] == "ACKNOWLEDGED"
    assert len(data["actions"]) == 1
    assert data["actions"][0]["action"] == "ACKNOWLEDGE"
    assert data["actions"][0]["from_status"] == "OPEN"
    assert data["actions"][0]["to_status"] == "ACKNOWLEDGED"

    # 4. Resolve via Admin
    resolve_payload = {
        "action": "RESOLVE",
        "notes": "Confirmed valid outlier by admin",
    }
    admin_res = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{sig_id}/action",
        json=resolve_payload,
        headers=admin_auth_headers
    )
    assert admin_res.status_code == 200
    resolved_data = admin_res.json()
    assert resolved_data["current_status"] == "RESOLVED"
    assert len(resolved_data["actions"]) == 2
    assert resolved_data["resolution_reason"] == "Confirmed valid outlier by admin"

    # 5. List reviews endpoint
    list_res = client.get(
        "/api/analytics/district/intelligence/anomalies/reviews?district=Ariyalur",
        headers=auth_headers
    )
    assert list_res.status_code == 200
    reviews = list_res.json()
    assert len(reviews) >= 1
    assert any(r["signal_id"] == sig_id for r in reviews)
