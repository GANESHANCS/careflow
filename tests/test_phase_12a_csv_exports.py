import pytest
import csv
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.import_job import ImportJob
from backend.app.services.analytics.district_export import sanitize_csv_cell, DistrictExportService


@pytest.fixture
def seed_export_data(db_session: Session):
    """Seeds test data for export tests including zeroes, missing, and injection-like strings."""
    job = ImportJob(
        id=201,
        job_code="JOB_EXPORT_TEST_201",
        original_filename="hmis-item-rpt-tn-for-2015-16.csv",
        storage_path="data/uploads/JOB_EXPORT_TEST_201/hmis.csv",
        file_hash="dummy_hash_201",
        file_size_bytes=1000,
        status="COMPLETED",
        total_records=24,
        records_imported=24,
        records_rejected=0,
        schema_profile="district_monthly_tabular_v1"
    )
    db_session.add(job)
    db_session.flush()

    months = ["2015-04", "2015-05", "2015-06"]

    # Ariyalur records: normal, zero, missing
    obs = [
        DistrictObservation(
            id="DOBS_EXP_1",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=150.0,
            value_type="VALID",
            validation_status="VALIDATED",
            reported_annual_total=150.0,
            source_file="test.csv",
            source_row=1,
            last_import_job_id=201,
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0"
        ),
        DistrictObservation(
            id="DOBS_EXP_2",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-05",
            observation_date="2015-05-01",
            value=0.0,
            value_type="ZERO",
            validation_status="VALIDATED",
            reported_annual_total=150.0,
            source_file="test.csv",
            source_row=2,
            last_import_job_id=201,
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0"
        ),
        DistrictObservation(
            id="DOBS_EXP_3",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-06",
            observation_date="2015-06-01",
            value=None,
            value_type="MISSING",
            validation_status="VALIDATED",
            reported_annual_total=150.0,
            source_file="test.csv",
            source_row=3,
            last_import_job_id=201,
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0"
        ),
        # Formula injection edge case district name
        DistrictObservation(
            id="DOBS_EXP_4",
            state="Tamil Nadu",
            district="=Chennai+Malicious",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-06",
            observation_date="2015-06-01",
            value=200.0,
            value_type="VALID",
            validation_status="VALIDATED",
            reported_annual_total=200.0,
            source_file="test.csv",
            source_row=4,
            last_import_job_id=201,
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0"
        ),
    ]
    db_session.add_all(obs)
    db_session.commit()


# ---------------------------------------------------------------------------
# Unit Tests: Formula Injection Sanitization
# ---------------------------------------------------------------------------

def test_sanitize_csv_cell_normal():
    assert sanitize_csv_cell("Ariyalur") == "Ariyalur"
    assert sanitize_csv_cell(123) == "123"
    assert sanitize_csv_cell(45.67) == "45.67"
    assert sanitize_csv_cell(None) == ""
    assert sanitize_csv_cell(True) == "true"
    assert sanitize_csv_cell(False) == "false"


def test_sanitize_csv_cell_injection_protection():
    # Equals sign prefix
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    # Plus sign prefix
    assert sanitize_csv_cell("+SUM(A1:A10)") == "'+SUM(A1:A10)"
    # Minus sign prefix
    assert sanitize_csv_cell("-10+20") == "'-10+20"
    # At sign prefix
    assert sanitize_csv_cell("@SUM(B1:B5)") == "'@SUM(B1:B5)"
    # Tab / Carriage return prefix
    assert sanitize_csv_cell("\tsomething") == "'\tsomething"
    assert sanitize_csv_cell("\rsomething") == "'\rsomething"


# ---------------------------------------------------------------------------
# API Tests: Trends Export
# ---------------------------------------------------------------------------

def test_export_trends_unauthenticated(client: TestClient, seed_export_data):
    res = client.get("/api/analytics/district/export/trends?district=Ariyalur&s_no=14.12.1")
    assert res.status_code == 401


def test_export_trends_authenticated(client: TestClient, auth_headers: dict, seed_export_data):
    res = client.get(
        "/api/analytics/district/export/trends?district=Ariyalur&s_no=14.12.1&subgroup_type=TOTAL",
        headers=auth_headers
    )
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert 'attachment; filename="district_trends_ariyalur_14_12_1.csv"' in res.headers["content-disposition"]

    content = res.text
    # Check provenance banner comments
    assert "# CAREFlow India — District HMIS Observations Export" in content
    assert "# District: Ariyalur | Indicator S.No: 14.12.1" in content
    assert "# Integrity Rule: Missing values are represented as empty cells" in content

    # Parse CSV lines
    lines = [line for line in content.splitlines() if not line.startswith("#")]
    reader = csv.reader(lines)
    header = next(reader)
    assert "district" in header
    assert "s_no" in header
    assert "reporting_month" in header
    assert "value" in header
    assert "value_type" in header

    rows = list(reader)
    assert len(rows) == 3

    # Row 1: Valid value (150.0)
    assert rows[0][0] == "Ariyalur"
    assert rows[0][6] == "150.0"
    assert rows[0][7] == "VALID"

    # Row 2: Zero value (0.0 preserved, NOT empty string)
    assert rows[1][0] == "Ariyalur"
    assert rows[1][6] == "0.0"
    assert rows[1][7] == "ZERO"

    # Row 3: Missing value (empty string preserved, NOT 0.0)
    assert rows[2][0] == "Ariyalur"
    assert rows[2][6] == ""
    assert rows[2][7] == "MISSING"


# ---------------------------------------------------------------------------
# API Tests: Comparison Export
# ---------------------------------------------------------------------------

def test_export_comparison_unauthenticated(client: TestClient, seed_export_data):
    res = client.get("/api/analytics/district/export/compare?s_no=14.12.1&reporting_month=2015-06")
    assert res.status_code == 401


def test_export_comparison_authenticated_and_injection(client: TestClient, auth_headers: dict, seed_export_data):
    res = client.get(
        "/api/analytics/district/export/compare?s_no=14.12.1&reporting_month=2015-06&subgroup_type=TOTAL",
        headers=auth_headers
    )
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert 'attachment; filename="district_compare_14_12_1_2015-06.csv"' in res.headers["content-disposition"]

    content = res.text
    assert "# CAREFlow India — Cross-District HMIS Comparison Export" in content

    lines = [line for line in content.splitlines() if not line.startswith("#")]
    reader = csv.reader(lines)
    header = next(reader)
    assert header == [
        "district", "s_no", "parameter_name", "reporting_month", "financial_year",
        "value", "value_type", "rank", "reported_annual_total", "state_mean", "state_median", "state_total"
    ]

    rows = list(reader)
    # 2 districts reporting in 2015-06: Ariyalur (missing) and =Chennai+Malicious (200.0)
    assert len(rows) == 2

    # Verify formula injection mitigation: =Chennai+Malicious is escaped to '=Chennai+Malicious
    malicious_row = next(r for r in rows if "Chennai" in r[0])
    assert malicious_row[0] == "'=Chennai+Malicious"
    assert malicious_row[5] == "200.0"
    assert malicious_row[7] == "1"  # rank 1
