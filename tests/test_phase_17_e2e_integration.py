"""
CAREFlow India — Phase 17: End-to-End Integration, Clinical Data Validation & Demonstration Readiness Tests.

Covers:
1. End-to-end Authentication & Session Verification (Admin, Analyst, Viewer, Invalid Credentials, Expired/Malformed Tokens).
2. Role-Based Access Control (RBAC) across imports, rollbacks, and anomaly review workflows.
3. Clinical Indicator Registry Audit & Strict Ambiguity Handling (Demarcating verified vs ambiguous indicators such as 14.10.1.c).
4. Data Integrity: Strict distinction between numeric zero (0.0) and missing values (None), financial year filtering, and non-additive stock metrics.
5. Cross-District Comparisons: Accurate summary statistics (mean, median, total) and ranking excluding missing observations.
6. CSV Export Governance: RFC 4180 compliance, streaming response, and OWASP formula-injection sanitization.
7. Anomaly Review State Machine: Complete lifecycle transitions (OPEN -> ACKNOWLEDGED -> UNDER_REVIEW -> RESOLVED -> REOPENED), note additions, and invalid transition rejection.
8. HMIS Ingestion Validation & Idempotency: File format validation, SHA-256 duplicate detection.
9. Health & System Readiness Probes (/api/health, /api/healthz, /api/readyz).
"""

import io
import csv
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password, create_access_token
from backend.app.db.models.user import User
from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.anomaly_review import (
    DistrictAnomalyReview,
    DistrictAnomalyReviewAction,
    AnomalyReviewStatus,
    AnomalyReviewActionType,
)
from backend.app.services.analytics.indicator_registry import IndicatorMappingRegistry, MappingStatus
from backend.app.services.analytics.district_export import sanitize_csv_cell


# ===========================================================================
# 1. End-to-End Authentication & Session Verification
# ===========================================================================

def test_auth_login_all_roles(client: TestClient, db_session: Session):
    """Verifies that all three standard roles (ADMIN, ANALYST, VIEWER) can authenticate."""
    users_data = [
        ("admin_user", "admin@careflow.gov.in", "AdminPass123!", "ADMIN"),
        ("analyst_user", "analyst@careflow.gov.in", "AnalystPass123!", "ANALYST"),
        ("viewer_user", "viewer@careflow.gov.in", "ViewerPass123!", "VIEWER"),
    ]

    for username, email, password, role in users_data:
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role=role,
            is_active=True,
        )
        db_session.add(user)
    db_session.commit()

    for username, email, password, role in users_data:
        response = client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == 200, f"Login failed for {role}"
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["role"] == role
        assert body["user"]["username"] == username


def test_auth_login_invalid_credentials(client: TestClient, db_session: Session):
    """Verifies that incorrect passwords and non-existent users are rejected."""
    user = User(
        username="valid_user",
        email="valid@careflow.gov.in",
        hashed_password=hash_password("CorrectPassword123!"),
        role="ANALYST",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    # Wrong password
    res1 = client.post("/api/auth/login", json={"username": "valid_user", "password": "WrongPassword!"})
    assert res1.status_code in (400, 401)

    # Unknown user
    res2 = client.post("/api/auth/login", json={"username": "ghost_user", "password": "AnyPassword!"})
    assert res2.status_code in (400, 401)


def test_auth_login_inactive_user(client: TestClient, db_session: Session):
    """Verifies that inactive accounts cannot authenticate."""
    inactive_user = User(
        username="disabled_user",
        email="disabled@careflow.gov.in",
        hashed_password=hash_password("Pass123!"),
        role="VIEWER",
        is_active=False,
    )
    db_session.add(inactive_user)
    db_session.commit()

    res = client.post("/api/auth/login", json={"username": "disabled_user", "password": "Pass123!"})
    assert res.status_code in (400, 401)


def test_unauthenticated_and_expired_token_handling(client: TestClient, db_session: Session):
    """Verifies that missing or expired JWT tokens return HTTP 401."""
    # 1. No token provided
    res1 = client.get("/api/analytics/district/catalog")
    assert res1.status_code == 401

    # 2. Expired token provided
    user = User(
        username="active_user",
        email="active@careflow.gov.in",
        hashed_password=hash_password("Pass123!"),
        role="ANALYST",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    expired_token = create_access_token(
        subject=user.id,
        role=user.role,
        expires_delta=timedelta(seconds=-60),
    )
    res2 = client.get(
        "/api/analytics/district/catalog",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res2.status_code == 401


# ===========================================================================
# 2. Role-Based Access Control (RBAC) Matrix
# ===========================================================================

def test_rbac_import_upload_permissions(client: TestClient, admin_auth_headers: dict, auth_headers: dict, viewer_auth_headers: dict):
    """Verifies that ADMIN and ANALYST can upload datasets, while VIEWER is forbidden."""
    dummy_csv = b"s_no,indicator\n1.1,Test\n"

    # ADMIN: Allowed (HTTP 201)
    admin_res = client.post(
        "/api/imports?sync=true",
        files={"file": ("hmis_admin.csv", io.BytesIO(dummy_csv), "text/csv")},
        headers=admin_auth_headers,
    )
    assert admin_res.status_code == 201

    # ANALYST: Allowed (HTTP 201)
    analyst_res = client.post(
        "/api/imports?sync=true",
        files={"file": ("hmis_analyst.csv", io.BytesIO(b"s_no,indicator\n2.2,Test2\n"), "text/csv")},
        headers=auth_headers,
    )
    assert analyst_res.status_code == 201

    # VIEWER: Forbidden (HTTP 403)
    viewer_res = client.post(
        "/api/imports?sync=true",
        files={"file": ("hmis_viewer.csv", io.BytesIO(dummy_csv), "text/csv")},
        headers=viewer_auth_headers,
    )
    assert viewer_res.status_code == 403


def test_rbac_rollback_requires_admin(client: TestClient, db_session: Session, admin_auth_headers: dict, auth_headers: dict, viewer_auth_headers: dict):
    """Verifies that only ADMIN can trigger import rollback, while ANALYST and VIEWER are forbidden."""
    job = ImportJob(
        id=701,
        job_code="JOB_ROLLBACK_RBAC",
        original_filename="rollback_test.csv",
        storage_path="data/uploads/JOB_ROLLBACK_RBAC/rollback_test.csv",
        file_hash="hash_rollback_rbac",
        file_size_bytes=500,
        status="COMPLETED",
        total_records=10,
        records_imported=10,
        records_rejected=0,
    )
    db_session.add(job)
    db_session.commit()

    # VIEWER: 403 Forbidden
    res_viewer = client.post(
        f"/api/imports/{job.job_code}/rollback",
        json={"reason": "Testing viewer rejection"},
        headers=viewer_auth_headers,
    )
    assert res_viewer.status_code == 403

    # ANALYST: 403 Forbidden
    res_analyst = client.post(
        f"/api/imports/{job.job_code}/rollback",
        json={"reason": "Testing analyst rejection"},
        headers=auth_headers,
    )
    assert res_analyst.status_code == 403

    # ADMIN: Permitted to attempt rollback
    res_admin = client.post(
        f"/api/imports/{job.job_code}/rollback",
        json={"reason": "Authorized admin rollback test"},
        headers=admin_auth_headers,
    )
    assert res_admin.status_code == 200


# ===========================================================================
# 3. Clinical Indicator Registry Verification & Ambiguity Handling
# ===========================================================================

def test_indicator_mapping_registry_specifications():
    """Verifies that the indicator mapping registry distinguishes verified and ambiguous indicators."""
    # 1. Verified indicators have valid canonical IDs and VERIFIED status
    anc = IndicatorMappingRegistry.get_mapping("1.1")
    assert anc.status == MappingStatus.VERIFIED
    assert anc.canonical_id == "IND_antenatal_visits"
    assert "ANC" in anc.canonical_name

    opd = IndicatorMappingRegistry.get_mapping("14.12.1")
    assert opd.status == MappingStatus.VERIFIED
    assert opd.canonical_id == "IND_opd_attendance"

    # 2. Inpatient admissions (14.10.1.c) is explicitly AMBIGUOUS due to lack of unified total
    ipd = IndicatorMappingRegistry.get_mapping("14.10.1.c")
    assert ipd.status == MappingStatus.AMBIGUOUS
    assert "AMBIGUOUS" in ipd.rationale
    assert "disaggregated" in ipd.rationale.lower() or "partitioned" in ipd.rationale.lower()

    # 3. Stock metrics are flagged as non-additive
    stock = IndicatorMappingRegistry.get_mapping("14.01")
    assert stock.is_stock_metric is True


def test_healthcare_intelligence_rejects_ambiguous_and_unmapped_indicators(client: TestClient, db_session: Session, auth_headers: dict):
    """
    Verifies that the Healthcare Intelligence engine strictly rejects ambiguous indicators
    (like 14.10.1.c) and unmapped indicators, refusing to treat them as authoritative.
    """
    # 1. Attempting intelligence overview with ambiguous indicator 14.10.1.c -> HTTP 400
    res_ambiguous = client.get(
        "/api/analytics/district/intelligence/overview?district=Ariyalur&s_no=14.10.1.c",
        headers=auth_headers,
    )
    assert res_ambiguous.status_code == 400
    assert "ambiguous" in res_ambiguous.json()["detail"].lower()

    # 2. Attempting intelligence overview with unmapped indicator -> HTTP 400
    res_unmapped = client.get(
        "/api/analytics/district/intelligence/overview?district=Ariyalur&s_no=99.99",
        headers=auth_headers,
    )
    assert res_unmapped.status_code == 400
    assert "ineligible" in res_unmapped.json()["detail"].lower() or "unmapped" in res_unmapped.json()["detail"].lower()


# ===========================================================================
# 4. Data Integrity: Zero vs Missing, Financial-Year Filters, Stock Metrics
# ===========================================================================

@pytest.fixture
def seed_clinical_test_data(db_session: Session):
    """Seeds test observations covering valid numbers, numeric zero, and missing values."""
    records = [
        DistrictObservation(
            id="CLIN_OBS_1",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=250.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0.0",
        ),
        DistrictObservation(
            id="CLIN_OBS_2",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-05",
            observation_date="2015-05-01",
            value=0.0,
            value_type="ZERO",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0.0",
        ),
        DistrictObservation(
            id="CLIN_OBS_3",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-06",
            observation_date="2015-06-01",
            value=None,
            value_type="MISSING",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0.0",
        ),
        DistrictObservation(
            id="CLIN_OBS_4",
            state="Tamil Nadu",
            district="Chennai",
            s_no="14.12.1",
            parameter_name="Outpatient attendance",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=1000.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0.0",
        ),
        # Stock metric observation
        DistrictObservation(
            id="CLIN_OBS_5",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.01",
            parameter_name="Available Beds",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=45.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z",
            transformation_version="1.0.0",
        ),
    ]
    db_session.add_all(records)
    db_session.commit()


def test_trends_zero_vs_missing_integrity(client: TestClient, seed_clinical_test_data, auth_headers: dict):
    """Verifies that monthly trends correctly distinguish 0.0 (ZERO) from None (MISSING)."""
    res = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.12.1&subgroup_type=TOTAL",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    observations = data["observations"]

    obs_map = {o["reporting_month"]: o for o in observations}

    # Month 2015-04: Valid numeric (250.0)
    assert obs_map["2015-04"]["value"] == 250.0
    assert obs_map["2015-04"]["value_type"] == "VALID"

    # Month 2015-05: Genuine zero (0.0)
    assert obs_map["2015-05"]["value"] == 0.0
    assert obs_map["2015-05"]["value_type"] == "ZERO"

    # Month 2015-06: Missing value (None)
    assert obs_map["2015-06"]["value"] is None
    assert obs_map["2015-06"]["value_type"] == "MISSING"


def test_financial_year_filtering(client: TestClient, seed_clinical_test_data, auth_headers: dict):
    """Verifies that financial year filter isolates the requested year and rejects non-existent years."""
    # Match 2015-16
    res_match = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.12.1&financial_year=2015-16",
        headers=auth_headers,
    )
    assert res_match.status_code == 200
    assert len(res_match.json()["observations"]) == 3

    # No match for future year 2029-30 returns HTTP 404 (no observations found for specified period filter)
    res_none = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.12.1&financial_year=2029-30",
        headers=auth_headers,
    )
    assert res_none.status_code == 404


def test_non_additive_stock_metric_tagging(client: TestClient, seed_clinical_test_data, auth_headers: dict):
    """Verifies that stock metrics (like bed capacity 14.01) are tagged as non-additive."""
    res = client.get(
        "/api/analytics/district/trends?district=Ariyalur&s_no=14.01",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_stock_metric"] is True


# ===========================================================================
# 5. Cross-District Comparisons & Calculations
# ===========================================================================

def test_district_comparison_summary_statistics(client: TestClient, seed_clinical_test_data, auth_headers: dict):
    """Verifies that cross-district comparison calculates correct state mean, median, total, and ranks."""
    res = client.get(
        "/api/analytics/district/compare?s_no=14.12.1&reporting_month=2015-04&subgroup_type=TOTAL",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    items = data["items"]

    assert len(items) >= 2
    item_map = {it["district"]: it for it in items}

    # Chennai: 1000.0 (Rank 1)
    assert item_map["Chennai"]["value"] == 1000.0
    assert item_map["Chennai"]["rank"] == 1

    # Ariyalur: 250.0 (Rank 2)
    assert item_map["Ariyalur"]["value"] == 250.0
    assert item_map["Ariyalur"]["rank"] == 2

    # State Summary fields directly on response model
    assert data["state_total"] == 1250.0
    assert data["state_mean"] == 625.0
    assert data["state_median"] == 625.0


# ===========================================================================
# 6. CSV Export Governance & Formula Injection Protection
# ===========================================================================

def test_csv_cell_sanitization_owasp():
    """Verifies formula injection mitigation for dangerous prefixes (=, +, -, @, tab, newline)."""
    assert sanitize_csv_cell("Ariyalur") == "Ariyalur"
    assert sanitize_csv_cell(100) == "100"
    assert sanitize_csv_cell(0) == "0"
    assert sanitize_csv_cell(None) == ""

    # Dangerous prefixes neutralized with leading single quote
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-10+20") == "'-10+20"
    assert sanitize_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert sanitize_csv_cell("\tMALICIOUS") == "'\tMALICIOUS"
    assert sanitize_csv_cell("\rMALICIOUS") == "'\rMALICIOUS"


def test_export_trends_streaming_csv(client: TestClient, seed_clinical_test_data, auth_headers: dict):
    """Verifies that trends CSV export streams valid RFC 4180 format with audit headers."""
    res = client.get(
        "/api/analytics/district/export/trends?district=Ariyalur&s_no=14.12.1&subgroup_type=TOTAL",
        headers=auth_headers,
    )
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment; filename=" in res.headers["content-disposition"]

    content = res.text
    # Verify provenance comments
    assert "CAREFlow India" in content
    assert "District HMIS Observations Export" in content
    assert "District: Ariyalur" in content
    assert "Indicator S.No: 14.12.1" in content

    # Parse rows
    lines = [line for line in content.splitlines() if not line.startswith("#")]
    reader = csv.DictReader(lines)
    rows = list(reader)

    assert len(rows) == 3
    row_map = {r["reporting_month"]: r for r in rows}

    # Month 1: 250.0
    assert row_map["2015-04"]["value"] == "250.0"
    assert row_map["2015-04"]["value_type"] == "VALID"

    # Month 2: 0.0
    assert row_map["2015-05"]["value"] == "0.0"
    assert row_map["2015-05"]["value_type"] == "ZERO"

    # Month 3: empty string for missing value
    assert row_map["2015-06"]["value"] == ""
    assert row_map["2015-06"]["value_type"] == "MISSING"


# ===========================================================================
# 7. Anomaly Review State Machine & Audit Provenance
# ===========================================================================

def test_anomaly_review_full_state_lifecycle(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """
    Tests the complete anomaly review lifecycle:
    OPEN -> ACKNOWLEDGED -> UNDER_REVIEW -> RESOLVED -> REOPENED -> ADD_NOTE
    and validates immutable audit action history.
    """
    signal_id = "SIG_P17_TEST_001"

    # 1. Acknowledge the signal (OPEN -> ACKNOWLEDGED)
    res1 = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action",
        json={
            "action": "ACKNOWLEDGE",
            "notes": "Acknowledged by supervisor",
            "district": "Ariyalur",
            "indicator_id": "14.12.1",
            "reporting_month": "2015-05",
            "signal_type": "STATISTICAL_SHIFT",
            "trigger_reason": "Drop to zero observed",
        },
        headers=admin_auth_headers,
    )
    assert res1.status_code == 200
    review1 = res1.json()
    assert review1["current_status"] == "ACKNOWLEDGED"
    assert len(review1["actions"]) == 1
    assert review1["actions"][0]["action"] == "ACKNOWLEDGE"

    # 2. Put under review (ACKNOWLEDGED -> UNDER_REVIEW)
    res2 = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action",
        json={"action": "SET_UNDER_REVIEW", "notes": "Auditing facility logs"},
        headers=admin_auth_headers,
    )
    assert res2.status_code == 200
    assert res2.json()["current_status"] == "UNDER_REVIEW"

    # 3. Resolve the review (UNDER_REVIEW -> RESOLVED)
    res3 = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action",
        json={"action": "RESOLVE", "notes": "Confirmed valid holiday closure"},
        headers=admin_auth_headers,
    )
    assert res3.status_code == 200
    assert res3.json()["current_status"] == "RESOLVED"

    # 4. Reopen the review (RESOLVED -> REOPENED)
    res4 = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action",
        json={"action": "REOPEN", "notes": "Reopening due to conflicting regional report"},
        headers=admin_auth_headers,
    )
    assert res4.status_code == 200
    assert res4.json()["current_status"] == "REOPENED"

    # 5. Add a note without altering status (REOPENED -> REOPENED)
    res5 = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action",
        json={"action": "ADD_NOTE", "notes": "Additional inquiry submitted to CMO"},
        headers=admin_auth_headers,
    )
    assert res5.status_code == 200
    review5 = res5.json()
    assert review5["current_status"] == "REOPENED"
    assert len(review5["actions"]) == 5


def test_anomaly_review_invalid_transition_rejected(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Verifies that invalid state transitions (e.g. attempting to resolve from resolved without reopen) are rejected."""
    signal_id = "SIG_P17_INVALID_002"

    # First resolve directly from OPEN
    client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action",
        json={
            "action": "RESOLVE",
            "notes": "Direct resolve",
            "district": "Chennai",
            "indicator_id": "14.12.1",
            "reporting_month": "2015-05",
            "signal_type": "MAD_OUTLIER",
            "trigger_reason": "High outlier",
        },
        headers=admin_auth_headers,
    )

    # Attempting to acknowledge an already RESOLVED review without reopening -> HTTP 400
    res_bad = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action",
        json={"action": "ACKNOWLEDGE", "notes": "Invalid transition from resolved"},
        headers=admin_auth_headers,
    )
    assert res_bad.status_code == 400
    assert "invalid transition" in res_bad.json()["detail"].lower()


# ===========================================================================
# 8. HMIS Ingestion Validation & Idempotency
# ===========================================================================

def test_import_validation_and_idempotency(client: TestClient, admin_auth_headers: dict):
    """Verifies that file uploads validate file extension and detect SHA-256 duplicate uploads."""
    # 1. Invalid file extension rejected
    bad_res = client.post(
        "/api/imports?sync=true",
        files={"file": ("malicious.exe", io.BytesIO(b"binary"), "application/octet-stream")},
        headers=admin_auth_headers,
    )
    assert bad_res.status_code == 400
    assert "unsupported file format" in bad_res.json()["detail"].lower()

    # 2. Upload valid facility HMIS CSV
    valid_csv = (
        b"State,District,Facility Code,Facility Name,Reporting Month,OPD Attendance,Inpatient Admissions,Antenatal Visits\n"
        b"Tamil Nadu,Ariyalur,FAC_P17_01,Primary Health Centre One,2015-04,300,20,15\n"
    )
    res1 = client.post(
        "/api/imports?sync=true",
        files={"file": ("first_upload.csv", io.BytesIO(valid_csv), "text/csv")},
        headers=admin_auth_headers,
    )
    assert res1.status_code == 201
    job1 = res1.json()
    assert "job_code" in job1
    assert "file_hash" in job1
    assert job1["status"] in ("COMPLETED", "COMPLETED_WITH_WARNINGS")

    # 3. Upload identical content -> idempotency check recognizes existing completed job
    res2 = client.post(
        "/api/imports?sync=true",
        files={"file": ("second_upload.csv", io.BytesIO(valid_csv), "text/csv")},
        headers=admin_auth_headers,
    )
    assert res2.status_code == 201
    job2 = res2.json()
    assert job2["job_code"] == job1["job_code"]
    assert job2["file_hash"] == job1["file_hash"]


# ===========================================================================
# 9. Health & System Readiness Probes
# ===========================================================================

def test_system_health_and_readiness_probes(client: TestClient):
    """Verifies high-frequency liveness (/api/healthz) and readiness (/api/readyz)."""
    # Liveness probe
    res_liveness = client.get("/api/healthz")
    assert res_liveness.status_code == 200
    assert res_liveness.json()["status"] == "alive"

    # Readiness probe
    res_readiness = client.get("/api/readyz")
    assert res_readiness.status_code == 200
    assert res_readiness.json()["status"] == "ready"

    # Standard health probe
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "healthy"

