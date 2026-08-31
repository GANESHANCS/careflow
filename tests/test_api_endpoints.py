import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation


def test_health_endpoint(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "healthy"
    assert "sqlite" in data["database"]["engine"].lower() or "postgresql" in data["database"]["engine"].lower()


def test_facilities_endpoints(client: TestClient, db_session: Session, auth_headers: dict):
    # Seed facility
    fac = Facility(
        id="FC_TEST_99",
        facility_code="T99",
        facility_name="Test General Hospital",
        facility_type="DH",
        state="Test_State",
        district="Test_District",
        raw_facility_name="Test General Hospital"
    )
    db_session.add(fac)
    db_session.commit()

    # Unauthenticated list facilities -> 401
    res_unauth = client.get("/api/facilities?state=Test_State")
    assert res_unauth.status_code == 401

    # Authenticated list facilities
    res_list = client.get("/api/facilities?state=Test_State", headers=auth_headers)
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["total"] >= 1
    assert list_data["items"][0]["id"] == "FC_TEST_99"

    # Authenticated get facility detail
    res_detail = client.get("/api/facilities/FC_TEST_99", headers=auth_headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["facility_name"] == "Test General Hospital"

    # Get invalid facility 404
    res_404 = client.get("/api/facilities/FC_NONEXISTENT", headers=auth_headers)
    assert res_404.status_code == 404
    assert "not found" in res_404.json()["detail"].lower()


def test_indicators_endpoint(client: TestClient, db_session: Session, auth_headers: dict):
    ind = Indicator(
        id="IND_opd_att",
        code="opd_attendance",
        name="OPD Attendance",
        category="Outpatient",
        unit="visits"
    )
    db_session.add(ind)
    db_session.commit()

    # Unauthenticated -> 401
    res_unauth = client.get("/api/indicators")
    assert res_unauth.status_code == 401

    # Authenticated -> 200
    res = client.get("/api/indicators", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any(i["code"] == "opd_attendance" for i in data["items"])


def test_facility_observations_endpoint(client: TestClient, db_session: Session, auth_headers: dict):
    fac = Facility(id="FC_OBS_1", facility_code="O1", facility_name="Obs Hospital", facility_type="DH", state="S", district="D", raw_facility_name="Obs Hospital")
    ind = Indicator(id="IND_opd_obs", code="opd_attendance", name="OPD", category="Gen", unit="count")
    db_session.add_all([fac, ind])
    db_session.commit()

    obs = Observation(
        id="OBS_TEST_1",
        facility_id="FC_OBS_1",
        indicator_id="IND_opd_obs",
        observation_date="2024-04-01",
        reporting_month="2024-04",
        value=500.0,
        value_type="VALID",
        source_file="test.csv",
        ingested_at="t"
    )
    db_session.add(obs)
    db_session.commit()

    res = client.get("/api/facilities/FC_OBS_1/observations", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["value"] == 500.0

    # 404 for invalid facility
    res_404 = client.get("/api/facilities/INVALID_FAC/observations", headers=auth_headers)
    assert res_404.status_code == 404
