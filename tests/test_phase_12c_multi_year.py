import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.db.models.district_observation import DistrictObservation


@pytest.fixture
def seed_multi_year_data(db_session: Session):
    """Seeds multi-year test data across 2015-16 and 2016-17."""
    obs = [
        # FY 2015-16 observations for Ariyalur OPD
        DistrictObservation(
            id="DOBS_MY_1",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-06",
            observation_date="2015-06-01",
            value=100.0,
            value_type="VALID",
            validation_status="VALIDATED",
            reported_annual_total=1200.0,
            source_file="fy1516.csv",
            ingested_at="2026-10-21T00:00:00Z"
        ),
        DistrictObservation(
            id="DOBS_MY_2",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-07",
            observation_date="2015-07-01",
            value=110.0,
            value_type="VALID",
            validation_status="VALIDATED",
            reported_annual_total=1200.0,
            source_file="fy1516.csv",
            ingested_at="2026-10-21T00:00:00Z"
        ),
        # FY 2016-17 observations for Ariyalur OPD
        DistrictObservation(
            id="DOBS_MY_3",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2016-17",
            reporting_month="2016-06",
            observation_date="2016-06-01",
            value=250.0,
            value_type="VALID",
            validation_status="VALIDATED",
            reported_annual_total=3000.0,
            source_file="fy1617.csv",
            ingested_at="2026-10-21T00:00:00Z"
        ),
        DistrictObservation(
            id="DOBS_MY_4",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2016-17",
            reporting_month="2016-07",
            observation_date="2016-07-01",
            value=260.0,
            value_type="VALID",
            validation_status="VALIDATED",
            reported_annual_total=3000.0,
            source_file="fy1617.csv",
            ingested_at="2026-10-21T00:00:00Z"
        ),
    ]
    db_session.add_all(obs)
    db_session.commit()


# ---------------------------------------------------------------------------
# Multi-Year Catalog & Trends Queries
# ---------------------------------------------------------------------------

def test_catalog_exposes_multiple_financial_years(client: TestClient, auth_headers: dict, seed_multi_year_data):
    res = client.get("/api/analytics/district/catalog", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "2015-16" in data["financial_years"]
    assert "2016-17" in data["financial_years"]
    assert len(data["financial_years"]) == 2


def test_trends_filters_by_financial_year(client: TestClient, auth_headers: dict, seed_multi_year_data):
    # Query 2015-16 only
    res_1516 = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.12.1&subgroup_type=TOTAL&financial_year=2015-16",
        headers=auth_headers
    )
    assert res_1516.status_code == 200
    d_1516 = res_1516.json()
    assert len(d_1516["observations"]) == 2
    assert all(o["reporting_month"].startswith("2015") for o in d_1516["observations"])
    assert d_1516["calculated_sum"] == 210.0

    # Query 2016-17 only
    res_1617 = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.12.1&subgroup_type=TOTAL&financial_year=2016-17",
        headers=auth_headers
    )
    assert res_1617.status_code == 200
    d_1617 = res_1617.json()
    assert len(d_1617["observations"]) == 2
    assert all(o["reporting_month"].startswith("2016") for o in d_1617["observations"])
    assert d_1617["calculated_sum"] == 510.0


def test_export_trends_multi_year_filter(client: TestClient, auth_headers: dict, seed_multi_year_data):
    res = client.get(
        "/api/analytics/district/export/trends?district=Ariyalur&s_no=14.12.1&subgroup_type=TOTAL&financial_year=2016-17",
        headers=auth_headers
    )
    assert res.status_code == 200
    content = res.text
    # Should only contain 2016-17 rows
    assert "2016-06" in content
    assert "2016-07" in content
    assert "2015-06" not in content
    assert "2015-07" not in content


# ---------------------------------------------------------------------------
# Multi-Year Natural Key Uniqueness Test
# ---------------------------------------------------------------------------

def test_natural_key_uniqueness_with_financial_year(db_session: Session):
    """
    Verifies that the database allows the exact same reporting_month if financial_year differs,
    but rejects duplicates within the same financial_year.
    """
    dup1 = DistrictObservation(
        id="DOBS_DUP_1",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="14.12.1",
        parameter_name="Outpatient attendance - All",
        subgroup_type="TOTAL",
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=50.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="test1.csv",
        ingested_at="2026-10-21T00:00:00Z"
    )
    dup2 = DistrictObservation(
        id="DOBS_DUP_2",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="14.12.1",
        parameter_name="Outpatient attendance - All",
        subgroup_type="TOTAL",
        financial_year="2015-16",
        reporting_month="2015-04",  # Duplicate natural key in same FY!
        observation_date="2015-04-01",
        value=60.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="test2.csv",
        ingested_at="2026-10-21T00:00:00Z"
    )

    db_session.add(dup1)
    db_session.flush()

    db_session.add(dup2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
