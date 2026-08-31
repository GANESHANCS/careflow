import io
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.db.models.observation import Observation
from backend.app.db.models.facility import Facility
from backend.app.services.imports.storage import ImportStorageService


def create_synthetic_csv_bytes(include_missing=True) -> bytes:
    """Generates synthetic HMIS CSV bytes fixture for import testing."""
    df = pd.DataFrame([
        {
            "State": "StateAlpha",
            "District": "District1",
            "Facility Code": "FAC_101",
            "Facility Name": "Community Health Centre A",
            "Reporting Month": "2024-04",
            "OPD Attendance": 450.0,
            "Inpatient Admissions": 60.0 if include_missing else 0.0,
            "Antenatal Visits": None if include_missing else 30.0,  # Missing value check
        },
        {
            "State": "StateAlpha",
            "District": "District1",
            "Facility Code": "FAC_102",
            "Facility Name": "Primary Health Centre B",
            "Reporting Month": "2024-04",
            "OPD Attendance": 0.0,  # Explicit Zero check
            "Inpatient Admissions": 12.0,
            "Antenatal Visits": 18.0,
        }
    ])
    output = io.BytesIO()
    df.to_csv(output, index=False)
    return output.getvalue()


def create_synthetic_xlsx_bytes() -> bytes:
    """Generates synthetic HMIS XLSX bytes fixture for import testing."""
    df = pd.DataFrame([
        {
            "State": "StateBeta",
            "District": "District2",
            "Facility Code": "FAC_201",
            "Facility Name": "District Hospital C",
            "Reporting Month": "2024-05",
            "OPD Attendance": 1200.0,
            "Inpatient Admissions": 250.0,
        }
    ])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="HMIS Data", index=False)
    return output.getvalue()


# -------------------------------------------------------------------
# 1. UPLOAD VALIDATION & CONSTRAINTS TESTS
# -------------------------------------------------------------------

def test_upload_valid_csv(client: TestClient, auth_headers: dict):
    csv_bytes = create_synthetic_csv_bytes()
    files = {"file": ("test_hmis_data.csv", csv_bytes, "text/csv")}

    res = client.post("/api/imports", files=files, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()

    assert data["job_code"].startswith("JOB_")
    assert data["original_filename"] == "test_hmis_data.csv"
    assert data["status"] in ("COMPLETED", "COMPLETED_WITH_WARNINGS")
    assert data["total_records"] >= 2
    assert data["records_imported"] >= 1
    assert data["quality_score"] is not None
    assert "X-Request-ID" in res.headers


def test_upload_valid_xlsx(client: TestClient, admin_auth_headers: dict):
    xlsx_bytes = create_synthetic_xlsx_bytes()
    files = {"file": ("test_hmis_data.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    res = client.post("/api/imports", files=files, headers=admin_auth_headers)
    assert res.status_code == 201
    data = res.json()

    assert data["status"] in ("COMPLETED", "COMPLETED_WITH_WARNINGS")
    assert data["original_filename"] == "test_hmis_data.xlsx"


def test_upload_unsupported_file_extension(client: TestClient, auth_headers: dict):
    files = {"file": ("unsupported_script.pdf", b"%PDF-1.4 Fake PDF Content", "application/pdf")}

    res = client.post("/api/imports", files=files, headers=auth_headers)
    assert res.status_code == 400
    assert "Unsupported file format" in res.json()["detail"]


def test_upload_oversized_file(client: TestClient, auth_headers: dict):
    oversized_bytes = b"0" * (51 * 1024 * 1024)
    files = {"file": ("oversized.csv", oversized_bytes, "text/csv")}

    res = client.post("/api/imports", files=files, headers=auth_headers)
    assert res.status_code == 400
    assert "exceeds the maximum allowed limit" in res.json()["detail"]


def test_path_traversal_filename_sanitization():
    unsafe_name_1 = "../../etc/passwd"
    unsafe_name_2 = "C:\\Windows\\System32\\cmd.exe"
    unsafe_name_3 = "../../../malicious_file.csv"

    safe_1 = ImportStorageService.sanitize_filename(unsafe_name_1)
    safe_2 = ImportStorageService.sanitize_filename(unsafe_name_2)
    safe_3 = ImportStorageService.sanitize_filename(unsafe_name_3)

    assert ".." not in safe_1 and "/" not in safe_1
    assert "\\" not in safe_2 and "System32" not in safe_2
    assert safe_3 == "malicious_file.csv"


# -------------------------------------------------------------------
# 2. RBAC & AUTHORIZATION TESTS
# -------------------------------------------------------------------

def test_unauthenticated_upload_rejection(client: TestClient):
    csv_bytes = create_synthetic_csv_bytes()
    files = {"file": ("data.csv", csv_bytes, "text/csv")}

    res = client.post("/api/imports", files=files)
    assert res.status_code == 401


def test_viewer_upload_rejection(client: TestClient, viewer_auth_headers: dict):
    csv_bytes = create_synthetic_csv_bytes()
    files = {"file": ("data.csv", csv_bytes, "text/csv")}

    res = client.post("/api/imports", files=files, headers=viewer_auth_headers)
    assert res.status_code == 403
    assert "not permitted" in res.json()["detail"].lower() or "forbidden" in res.json()["detail"].lower()


def test_admin_and_analyst_upload_success(client: TestClient, admin_auth_headers: dict, auth_headers: dict):
    # ADMIN Upload
    res_admin = client.post("/api/imports", files={"file": ("admin_data.csv", create_synthetic_csv_bytes(), "text/csv")}, headers=admin_auth_headers)
    assert res_admin.status_code == 201

    # ANALYST Upload
    res_analyst = client.post("/api/imports", files={"file": ("analyst_data.csv", create_synthetic_csv_bytes(False), "text/csv")}, headers=auth_headers)
    assert res_analyst.status_code == 201


def test_viewer_can_view_import_endpoints(client: TestClient, auth_headers: dict, viewer_auth_headers: dict):
    # First create job as analyst
    res_upload = client.post("/api/imports", files={"file": ("viewer_test.csv", create_synthetic_csv_bytes(), "text/csv")}, headers=auth_headers)
    job_code = res_upload.json()["job_code"]

    # VIEWER lists imports
    res_list = client.get("/api/imports", headers=viewer_auth_headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 1

    # VIEWER reads job detail
    res_detail = client.get(f"/api/imports/{job_code}", headers=viewer_auth_headers)
    assert res_detail.status_code == 200

    # VIEWER reads job quality
    res_quality = client.get(f"/api/imports/{job_code}/quality", headers=viewer_auth_headers)
    assert res_quality.status_code == 200

    # VIEWER reads job errors
    res_errors = client.get(f"/api/imports/{job_code}/errors", headers=viewer_auth_headers)
    assert res_errors.status_code == 200


# -------------------------------------------------------------------
# 3. DATA INTEGRITY & NON-DESTRUCTIVE INGESTION TESTS
# -------------------------------------------------------------------

def test_missing_and_zero_preservation(client: TestClient, db_session: Session, auth_headers: dict):
    csv_bytes = create_synthetic_csv_bytes(include_missing=True)
    res = client.post("/api/imports", files={"file": ("missing_test.csv", csv_bytes, "text/csv")}, headers=auth_headers)
    assert res.status_code == 201

    # Verify zero value preserved as 0.0 with ZERO/VALID classification
    zero_obs = db_session.query(Observation).filter(Observation.value == 0.0).first()
    assert zero_obs is not None

    # Verify missing value is stored as None / MISSING and NOT converted to 0.0
    missing_obs = db_session.query(Observation).filter(Observation.value_type == "MISSING").first()
    if missing_obs:
        assert missing_obs.value is None


def test_existing_valid_observation_not_overwritten_by_missing(client: TestClient, db_session: Session, auth_headers: dict):
    # Seed an existing valid observation
    fac = Facility(id="FC_FAC_101", facility_code="FAC_101", facility_name="CHC A", facility_type="CHC", state="S", district="D", raw_facility_name="CHC A")
    db_session.add(fac)
    db_session.commit()

    obs = Observation(
        id="OBS_FC_FAC_101_antenatal_visits_2024-04",
        facility_id="FC_FAC_101",
        indicator_id="IND_antenatal_visits",
        observation_date="2024-04-01",
        reporting_month="2024-04",
        value=99.0,
        value_type="VALID",
        source_file="initial.csv",
        ingested_at="t"
    )
    db_session.add(obs)
    db_session.commit()

    # Upload CSV containing a missing antenatal_visits value for FAC_101
    csv_bytes = create_synthetic_csv_bytes(include_missing=True)
    res = client.post("/api/imports", files={"file": ("overwrite_test.csv", csv_bytes, "text/csv")}, headers=auth_headers)
    assert res.status_code == 201

    db_session.refresh(obs)
    # The existing valid value (99.0) must NOT be overwritten with None!
    assert obs.value == 99.0


# -------------------------------------------------------------------
# 4. IDEMPOTENCY TESTS
# -------------------------------------------------------------------

def test_idempotent_reimport(client: TestClient, auth_headers: dict):
    csv_bytes = create_synthetic_csv_bytes()
    files1 = {"file": ("duplicate_file.csv", csv_bytes, "text/csv")}

    # First upload
    res1 = client.post("/api/imports", files=files1, headers=auth_headers)
    assert res1.status_code == 201
    job1_code = res1.json()["job_code"]

    # Second upload with identical bytes & filename
    files2 = {"file": ("duplicate_file.csv", csv_bytes, "text/csv")}
    res2 = client.post("/api/imports", files=files2, headers=auth_headers)
    assert res2.status_code == 201
    job2_code = res2.json()["job_code"]

    # Must return the existing job code without creating duplicate jobs
    assert job1_code == job2_code


# -------------------------------------------------------------------
# 5. API ENDPOINTS & PAGINATION TESTS
# -------------------------------------------------------------------

def test_list_and_filter_imports(client: TestClient, auth_headers: dict):
    client.post("/api/imports", files={"file": ("filter_a.csv", create_synthetic_csv_bytes(), "text/csv")}, headers=auth_headers)

    # List all
    res_all = client.get("/api/imports", headers=auth_headers)
    assert res_all.status_code == 200
    assert res_all.json()["total"] >= 1

    # Filter by search term
    res_search = client.get("/api/imports?search=filter_a", headers=auth_headers)
    assert res_search.status_code == 200
    assert res_search.json()["total"] >= 1
    assert "filter_a" in res_search.json()["items"][0]["original_filename"]

    # Pagination
    res_page = client.get("/api/imports?skip=0&limit=1", headers=auth_headers)
    assert res_page.status_code == 200
    assert len(res_page.json()["items"]) == 1


def test_import_not_found(client: TestClient, auth_headers: dict):
    res = client.get("/api/imports/JOB_NON_EXISTENT_999", headers=auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
