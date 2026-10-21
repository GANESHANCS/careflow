import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.import_job import ImportJob


@pytest.fixture
def seed_district_data(db_session: Session):
    """Seeds minimal, isolated district observations into test database."""
    # Add canonical indicators
    ind = Indicator(id="IND_opd_attendance", code="opd_attendance", name="Outpatient Attendance", category="OPD", unit="count", active=True)
    db_session.add(ind)

    # Add import job
    job = ImportJob(
        id=101,
        job_code="JOB_DIST_TEST_101",
        original_filename="hmis-item-rpt-tn-for-2015-16.csv",
        storage_path="data/uploads/JOB_DIST_TEST_101/hmis.csv",
        file_hash="dummy_hash_101",
        file_size_bytes=1000,
        status="COMPLETED",
        total_records=36,
        records_imported=36,
        records_rejected=0,
        schema_profile="district_monthly_tabular_v1"
    )
    db_session.add(job)
    db_session.flush()

    months = ["2015-04", "2015-05", "2015-06", "2015-07", "2015-08", "2015-09",
              "2015-10", "2015-11", "2015-12", "2016-01", "2016-02", "2016-03"]

    obs_list = []
    # 1. Ariyalur OPD (additive activity metric)
    for idx, m in enumerate(months):
        v = float((idx + 1) * 100)
        obs_list.append(
            DistrictObservation(
                id=f"DOBS_TN_Ariyalur_14.12.1_TOTAL_{m}",
                state="Tamil Nadu",
                district="Ariyalur",
                s_no="14.12.1",
                parameter_name="Outpatient attendance - All",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                indicator_id="IND_opd_attendance",
                financial_year="2015-16",
                reporting_month=m,
                observation_date=f"{m}-01",
                value=v,
                value_type="VALID",
                validation_status="VALIDATED",
                reported_annual_total=7800.0,
                source_file="test.csv",
                source_row=idx + 1,
                ingested_at="2026-10-21T00:00:00Z",
                transformation_version="1.0.0",
                last_import_job_id=101
            )
        )

    # 2. Chennai OPD (additive activity metric with a zero and a missing)
    for idx, m in enumerate(months):
        if idx == 0:
            v, vt = 0.0, "ZERO"
        elif idx == 1:
            v, vt = None, "MISSING"
        else:
            v, vt = float((idx + 1) * 200), "VALID"

        obs_list.append(
            DistrictObservation(
                id=f"DOBS_TN_Chennai_14.12.1_TOTAL_{m}",
                state="Tamil Nadu",
                district="Chennai",
                s_no="14.12.1",
                parameter_name="Outpatient attendance - All",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                indicator_id="IND_opd_attendance",
                financial_year="2015-16",
                reporting_month=m,
                observation_date=f"{m}-01",
                value=v,
                value_type=vt,
                validation_status="VALIDATED",
                reported_annual_total=15000.0,
                source_file="test.csv",
                source_row=idx + 13,
                ingested_at="2026-10-21T00:00:00Z",
                transformation_version="1.0.0",
                last_import_job_id=101
            )
        )

    # 3. Ariyalur Stock Metric (14.01 - Non-additive stock)
    for idx, m in enumerate(months):
        obs_list.append(
            DistrictObservation(
                id=f"DOBS_TN_Ariyalur_14.01_TOTAL_{m}",
                state="Tamil Nadu",
                district="Ariyalur",
                s_no="14.01",
                parameter_name="Sub Centres functioning in Govt buildings",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                indicator_id=None,
                financial_year="2015-16",
                reporting_month=m,
                observation_date=f"{m}-01",
                value=15.0,
                value_type="VALID",
                validation_status="VALIDATED",
                reported_annual_total=None,  # Stock metric total is None
                source_file="test.csv",
                source_row=idx + 25,
                ingested_at="2026-10-21T00:00:00Z",
                transformation_version="1.0.0",
                last_import_job_id=101
            )
        )

    db_session.add_all(obs_list)
    db_session.commit()
    return db_session


# ---------------------------------------------------------------------------
# API Tests: District Analytics Endpoints
# ---------------------------------------------------------------------------

def test_district_catalog_endpoint(client: TestClient, auth_headers: dict, seed_district_data):
    # Unauthenticated rejected
    unauth = client.get("/api/analytics/district/catalog")
    assert unauth.status_code == 401

    # Authenticated success
    res = client.get("/api/analytics/district/catalog", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert "districts" in data
    assert "Ariyalur" in data["districts"]
    assert "Chennai" in data["districts"]
    assert len(data["reporting_periods"]) == 12
    assert "2015-04" in data["reporting_periods"]
    assert "2016-03" in data["reporting_periods"]
    assert data["total_observed_records"] == 36
    assert len(data["limitations"]) > 0


def test_district_indicators_endpoint(client: TestClient, auth_headers: dict, seed_district_data):
    res = client.get("/api/analytics/district/indicators", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_indicators"] >= 2
    s_nos = [ind["s_no"] for ind in data["indicators"]]
    assert "14.12.1" in s_nos
    assert "14.01" in s_nos

    # Verify mapped vs unmapped indicator flags
    opd = next(i for i in data["indicators"] if i["s_no"] == "14.12.1")
    assert opd["is_mapped"] is True
    assert opd["canonical_indicator_id"] == "IND_opd_attendance"
    assert opd["is_stock_metric"] is False

    stock = next(i for i in data["indicators"] if i["s_no"] == "14.01")
    assert stock["is_mapped"] is False
    assert stock["canonical_indicator_id"] is None
    assert stock["is_stock_metric"] is True


def test_district_monthly_trends_endpoint(client: TestClient, auth_headers: dict, seed_district_data):
    # Valid additive metric
    res = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.12.1",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()

    assert data["district"] == "Ariyalur"
    assert data["s_no"] == "14.12.1"
    assert data["is_stock_metric"] is False
    assert len(data["observations"]) == 12
    assert data["annual_total_reported"] == 7800.0
    assert data["calculated_sum"] == 7800.0  # Sum of 100+200+...+1200
    assert data["valid_months_count"] == 12
    assert data["missing_months_count"] == 0

    # Test non-additive stock metric
    res_stock = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.01",
        headers=auth_headers
    )
    assert res_stock.status_code == 200
    stock_data = res_stock.json()
    assert stock_data["is_stock_metric"] is True
    assert stock_data["annual_total_reported"] is None
    assert stock_data["calculated_sum"] is None  # Summing stock metrics is prohibited

    # Test zero and missing preservation
    res_chennai = client.get(
        "/api/analytics/district/trends?district=Chennai&s_no=14.12.1",
        headers=auth_headers
    )
    assert res_chennai.status_code == 200
    chennai_data = res_chennai.json()
    assert chennai_data["zero_months_count"] == 1
    assert chennai_data["missing_months_count"] == 1
    assert chennai_data["observations"][0]["value"] == 0.0
    assert chennai_data["observations"][0]["value_type"] == "ZERO"
    assert chennai_data["observations"][1]["value"] is None
    assert chennai_data["observations"][1]["value_type"] == "MISSING"

    # Non-existent district -> 404
    res_404_dist = client.get(
        "/api/analytics/district/trends?district=InvalidDistrict&s_no=14.12.1",
        headers=auth_headers
    )
    assert res_404_dist.status_code == 404

    # Non-existent S.No. -> 404
    res_404_sno = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=99.99.99",
        headers=auth_headers
    )
    assert res_404_sno.status_code == 404


def test_district_compare_endpoint(client: TestClient, auth_headers: dict, seed_district_data):
    # Compare Ariyalur and Chennai for 2015-06
    res = client.get(
        "/api/analytics/district/compare?s_no=14.12.1&reporting_month=2015-06",
        headers=auth_headers
    )
    assert res.status_code == 200
    data = res.json()

    assert data["s_no"] == "14.12.1"
    assert data["reporting_month"] == "2015-06"
    assert data["total_districts"] == 2
    assert len(data["items"]) == 2

    # Ranking: Chennai (600) > Ariyalur (300)
    chennai_item = next(i for i in data["items"] if i["district"] == "Chennai")
    ariyalur_item = next(i for i in data["items"] if i["district"] == "Ariyalur")
    assert chennai_item["value"] == 600.0
    assert chennai_item["rank"] == 1
    assert ariyalur_item["value"] == 300.0
    assert ariyalur_item["rank"] == 2

    # Summary stats
    assert data["state_mean"] == 450.0
    assert data["state_median"] == 450.0
    assert data["state_total"] == 900.0

    # Compare with subset of districts
    res_subset = client.get(
        "/api/analytics/district/compare?s_no=14.12.1&reporting_month=2015-06&districts=Ariyalur",
        headers=auth_headers
    )
    assert res_subset.status_code == 200
    assert res_subset.json()["total_districts"] == 1


def test_district_quality_endpoint(client: TestClient, auth_headers: dict, seed_district_data):
    res = client.get("/api/analytics/district/quality", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_records"] == 36
    assert data["value_counts"]["VALID"] == 34
    assert data["value_counts"]["ZERO"] == 1
    assert data["value_counts"]["MISSING"] == 1
    assert data["districts_count"] == 2
    assert data["import_job"]["job_code"] == "JOB_DIST_TEST_101"
    assert len(data["district_coverage"]) == 2
