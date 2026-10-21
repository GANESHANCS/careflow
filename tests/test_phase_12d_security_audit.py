import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.analytics.district_export import MAX_EXPORT_ROWS


@pytest.fixture
def seed_security_test_data(db_session: Session):
    obs = DistrictObservation(
        id="DOBS_SEC_1",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="14.12.1",
        parameter_name="Outpatient attendance - All",
        subgroup_type="TOTAL",
        is_subgroup_total=True,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=100.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="test.csv",
        ingested_at="2026-10-21T00:00:00Z"
    )
    db_session.add(obs)
    db_session.commit()


# ---------------------------------------------------------------------------
# Security & Access Control Audits
# ---------------------------------------------------------------------------

def test_all_district_endpoints_require_authentication(client: TestClient, seed_security_test_data):
    """Verifies that all 9 district analytics, registry, and export routes strictly require authentication."""
    endpoints = [
        "/api/analytics/district/catalog",
        "/api/analytics/district/indicators",
        "/api/analytics/district/indicators/registry",
        "/api/analytics/district/indicators/audit",
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.12.1",
        "/api/analytics/district/compare?s_no=14.12.1&reporting_month=2015-04",
        "/api/analytics/district/export/trends?district=Ariyalur&s_no=14.12.1",
        "/api/analytics/district/export/compare?s_no=14.12.1&reporting_month=2015-04",
        "/api/analytics/district/quality",
    ]

    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 401, f"Endpoint {ep} failed to enforce authentication: returned {res.status_code}"


def test_sql_injection_resilience(client: TestClient, auth_headers: dict, seed_security_test_data):
    """Verifies that SQL injection payload attempts return 404 cleanly rather than executing or 500 erroring."""
    malicious_inputs = [
        "' OR '1'='1",
        "'; DROP TABLE district_observations; --",
        "Ariyalur' UNION SELECT * FROM users --",
    ]

    for payload in malicious_inputs:
        res = client.get(
            f"/api/analytics/district/trends?district={payload}&s_no=14.12.1",
            headers=auth_headers
        )
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()


def test_invalid_parameters_handled_gracefully(client: TestClient, auth_headers: dict, seed_security_test_data):
    # Non-existent district
    res_dist = client.get(
        "/api/analytics/district/trends?district=NonExistentDistrictXYZ&s_no=14.12.1",
        headers=auth_headers
    )
    assert res_dist.status_code == 404

    # Non-existent indicator S.No.
    res_sno = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=999.999.999",
        headers=auth_headers
    )
    assert res_sno.status_code == 404


def test_max_export_rows_boundary_constant():
    """Confirms bounded exports constant is defined and enforces a safe ceiling."""
    assert MAX_EXPORT_ROWS == 10000
