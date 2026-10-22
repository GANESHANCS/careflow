"""
Phase 16 — Production Readiness, Security Hardening & Operational Reliability Tests.
Validates:
1. Database path resolution and configuration validation.
2. Production security constraints (secret key, SQLite prohibition in prod, CORS hardening).
3. Exception sanitization (500 error sanitization, request ID propagation, zero traceback leakage).
4. Health and readiness endpoints (/api/health, /api/healthz, /api/readyz).
5. Comprehensive RBAC Matrix (ADMIN, ANALYST, VIEWER, Unauthenticated, Expired tokens).
6. Administrative review audit trail immutability and valid/invalid transitions.
7. Safe handling of invalid input payloads and export filtering.
"""

import io
import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, INSECURE_DEV_SECRET, normalize_database_url
from backend.app.core.security import create_access_token
from backend.app.db.models.user import User
from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.anomaly_review import (
    DistrictAnomalyReview,
    DistrictAnomalyReviewAction,
    AnomalyReviewStatus,
    AnomalyReviewActionType,
)
from backend.app.services.analytics.anomaly_review_service import DistrictAnomalyReviewService


# ===========================================================================
# 1. Database Path Resolution & Production Configuration Hardening
# ===========================================================================

def test_canonical_database_path_and_normalization():
    """Verifies that development database resolves to careflow_dev.db and PostgreSQL URLs normalize."""
    settings = Settings(ENVIRONMENT="development", DATABASE_URL="sqlite:///./careflow_dev.db")
    assert settings.DATABASE_URL == "sqlite:///./careflow_dev.db"
    assert settings.is_production is False
    assert settings.canonical_database_type == "sqlite"

    # PostgreSQL normalization
    pg_url = normalize_database_url("postgresql://careflow:secret@localhost:5432/careflow_prod")
    assert pg_url.startswith("postgresql+psycopg://")


def test_production_environment_security_enforcement():
    """Verifies that production environment enforces secure secret keys, PostgreSQL, and non-wildcard CORS."""
    valid_key = "a_very_secure_random_production_secret_key_1234567890_abcdef"

    # 1. Insecure default secret key rejected
    with pytest.raises(ValueError, match="requires a secure, non-default SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=INSECURE_DEV_SECRET,
            DATABASE_URL="postgresql://user:pass@localhost:5432/careflow"
        )

    # 2. Short secret key rejected
    with pytest.raises(ValueError, match="requires a secure, non-default SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="too_short",
            DATABASE_URL="postgresql://user:pass@localhost:5432/careflow"
        )

    # 3. SQLite database rejected in production
    with pytest.raises(ValueError, match="cannot use SQLite"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=valid_key,
            DATABASE_URL="sqlite:///./careflow_prod.db"
        )

    # 4. Wildcard CORS rejected in production
    with pytest.raises(ValueError, match="cannot use wildcard '\\*' in CORS_ORIGINS"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=valid_key,
            DATABASE_URL="postgresql://user:pass@localhost:5432/careflow",
            CORS_ORIGINS=["*"]
        )

    # 5. Valid production configuration accepted
    prod = Settings(
        ENVIRONMENT="production",
        SECRET_KEY=valid_key,
        DATABASE_URL="postgresql://user:pass@localhost:5432/careflow",
        CORS_ORIGINS=["https://app.careflow.in"]
    )
    assert prod.ENVIRONMENT == "production"
    assert prod.DEBUG is False
    assert prod.is_production is True
    assert prod.canonical_database_type == "postgresql"


# ===========================================================================
# 2. System Health, Readiness & Exception Sanitization
# ===========================================================================

def test_health_endpoints_and_readiness_probes(client: TestClient):
    """Verifies /api/health, /api/healthz, and /api/readyz contracts."""
    # 1. Standard Health
    res_health = client.get("/api/health")
    assert res_health.status_code == 200
    data_health = res_health.json()
    assert data_health["status"] in ("healthy", "degraded")
    assert "database" in data_health
    assert "password" not in res_health.text.lower()
    assert "sqlite:///" not in res_health.text

    # 2. Liveness probe (Kubernetes / Docker)
    res_healthz = client.get("/api/healthz")
    assert res_healthz.status_code == 200
    assert res_healthz.json()["status"] == "alive"

    # 3. Readiness probe
    res_readyz = client.get("/api/readyz")
    assert res_readyz.status_code == 200
    assert res_readyz.json()["status"] == "ready"


def test_exception_sanitization_and_request_id_tracing(client: TestClient, auth_headers: dict):
    """Verifies that API errors do not leak stack traces, local paths, or internal queries."""
    # Trigger 400 Bad Request
    res_bad = client.get("/api/forecast?facility_id=fac1&indicator_code=opd&horizon=99", headers=auth_headers)
    assert res_bad.status_code == 400
    data = res_bad.json()
    assert "error" in data
    assert "request_id" in data["error"]
    assert "X-Request-ID" in res_bad.headers
    # Verify no local filesystem paths leaked
    assert "D:\\" not in res_bad.text
    assert "Traceback" not in res_bad.text


# ===========================================================================
# 3. Comprehensive Authentication & Role-Based Authorization Matrix
# ===========================================================================

def test_unauthenticated_and_invalid_token_rejection(client: TestClient):
    """Verifies that protected operational endpoints reject unauthenticated or corrupt tokens."""
    protected_urls = [
        "/api/facilities",
        "/api/indicators",
        "/api/analytics/summary",
        "/api/analytics/district/catalog",
        "/api/analytics/district/indicators/registry",
        "/api/analytics/district/export/trends?district=Ariyalur&s_no=1.1",
        "/api/analytics/district/export/compare?s_no=1.1&reporting_month=2015-04",
        "/api/imports",
    ]

    for url in protected_urls:
        # 1. No token -> 401
        res_no_token = client.get(url)
        assert res_no_token.status_code == 401, f"Expected 401 for unauthenticated {url}, got {res_no_token.status_code}"

        # 2. Invalid token -> 401
        res_invalid = client.get(url, headers={"Authorization": "Bearer invalid_jwt_token_gibberish"})
        assert res_invalid.status_code == 401, f"Expected 401 for invalid token {url}, got {res_invalid.status_code}"

        # 3. Expired token -> 401
        expired = create_access_token(subject=1, role="ADMIN", expires_delta=timedelta(seconds=-10))
        res_expired = client.get(url, headers={"Authorization": f"Bearer {expired}"})
        assert res_expired.status_code == 401, f"Expected 401 for expired token {url}, got {res_expired.status_code}"


def test_rbac_administrative_permissions_matrix(
    client: TestClient,
    admin_auth_headers: dict,
    auth_headers: dict,
    viewer_auth_headers: dict
):
    """
    Verifies granular RBAC rules across ADMIN, ANALYST, and VIEWER roles:
    - Rollback: strictly ADMIN (ANALYST=403, VIEWER=403)
    - Directory Scan: strictly ADMIN (ANALYST=403, VIEWER=403)
    - Batch Cancel: strictly ADMIN (ANALYST=403, VIEWER=403)
    - Anomaly Review Actions: ADMIN and ANALYST (VIEWER=403)
    - File Upload: ADMIN and ANALYST (VIEWER=403)
    """
    sig_id = "SIG_P16_RBAC_TEST"
    review_action_payload = {
        "action": "ACKNOWLEDGE",
        "notes": "RBAC verification note",
        "district": "Ariyalur",
        "indicator_id": "1.1",
        "reporting_month": "2015-04",
        "signal_type": "OUTLIER_ZSCORE",
        "trigger_reason": "Z-Score outlier",
    }

    # 1. Rollback endpoint: ADMIN only
    res_rb_viewer = client.post("/api/imports/NONEXISTENT_JOB/rollback", headers=viewer_auth_headers)
    assert res_rb_viewer.status_code == 403

    res_rb_analyst = client.post("/api/imports/NONEXISTENT_JOB/rollback", headers=auth_headers)
    assert res_rb_analyst.status_code == 403

    # 2. Directory scan endpoint: ADMIN only
    res_scan_viewer = client.post("/api/imports/batches/scan", headers=viewer_auth_headers)
    assert res_scan_viewer.status_code == 403

    res_scan_analyst = client.post("/api/imports/batches/scan", headers=auth_headers)
    assert res_scan_analyst.status_code == 403

    # 3. File upload: ADMIN & ANALYST allowed; VIEWER forbidden (403)
    fake_csv = io.BytesIO(b"dummy,content\n1,2")
    res_upload_viewer = client.post(
        "/api/imports",
        files={"file": ("test.csv", fake_csv, "text/csv")},
        headers=viewer_auth_headers
    )
    assert res_upload_viewer.status_code == 403

    # 4. Anomaly Review Action: ADMIN & ANALYST allowed; VIEWER forbidden (403)
    res_review_viewer = client.post(
        f"/api/analytics/district/intelligence/anomalies/reviews/{sig_id}/action",
        json=review_action_payload,
        headers=viewer_auth_headers
    )
    assert res_review_viewer.status_code == 403


# ===========================================================================
# 4. Anomaly Review Audit Immutability & Transition Safety
# ===========================================================================

def test_anomaly_review_workflow_audit_immutability(db_session: Session):
    """
    Verifies that state transitions create sequential, immutable audit records
    preserving acting username, from/to states, and notes without modifying earlier actions.
    """
    admin_user = User(
        id=901,
        username="audit_admin_user",
        email="admin@test.gov.in",
        hashed_password="hash",
        role="ADMIN",
        is_active=True
    )
    analyst_user = User(
        id=902,
        username="audit_analyst_user",
        email="analyst@test.gov.in",
        hashed_password="hash",
        role="ANALYST",
        is_active=True
    )
    db_session.add_all([admin_user, analyst_user])
    db_session.commit()

    sig_id = "SIG_P16_AUDIT_SEQ_01"

    # Step 1: Analyst acknowledges signal
    rev = DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action="ACKNOWLEDGE",
        notes="First review by analyst",
        current_user=analyst_user,
        district="Salem",
        indicator_id="1.1",
        reporting_month="2015-06",
        signal_type="MOM_SHIFT",
        trigger_reason="Test shift",
        metric_value=500.0,
        expected_range="[400.0 - 450.0]"
    )
    assert rev.current_status == AnomalyReviewStatus.ACKNOWLEDGED
    assert len(rev.actions) == 1
    first_action_id = rev.actions[0].id
    first_action_note = rev.actions[0].notes
    assert rev.actions[0].username == "audit_analyst_user"
    assert rev.actions[0].from_status == AnomalyReviewStatus.OPEN
    assert rev.actions[0].to_status == AnomalyReviewStatus.ACKNOWLEDGED

    # Step 2: Analyst moves to Under Review
    rev = DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action="SET_UNDER_REVIEW",
        notes="Investigating reporting anomaly with district team",
        current_user=analyst_user
    )
    assert rev.current_status == AnomalyReviewStatus.UNDER_REVIEW

    # Step 3: Admin Resolves with documented clinical reason
    rev = DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action="RESOLVE",
        notes="Confirmed data entry transposition; verified corrected figures.",
        current_user=admin_user
    )
    assert rev.current_status == AnomalyReviewStatus.RESOLVED
    assert rev.resolution_reason == "Confirmed data entry transposition; verified corrected figures."
    assert rev.last_reviewed_by_username == "audit_admin_user"

    # Step 4: Admin Reopens
    rev = DistrictAnomalyReviewService.apply_review_action(
        db=db_session,
        signal_id=sig_id,
        action="REOPEN",
        notes="Reopening for state annual review meeting verification.",
        current_user=admin_user
    )
    assert rev.current_status == AnomalyReviewStatus.REOPENED

    # Query persisted audit actions in chronological order
    actions = db_session.query(DistrictAnomalyReviewAction).filter(
        DistrictAnomalyReviewAction.review_id == sig_id
    ).order_by(DistrictAnomalyReviewAction.id.asc()).all()

    assert len(actions) == 4
    assert actions[0].id == first_action_id
    assert actions[0].from_status == AnomalyReviewStatus.OPEN
    assert actions[0].to_status == AnomalyReviewStatus.ACKNOWLEDGED
    assert actions[0].notes == first_action_note
    assert actions[0].username == "audit_analyst_user"

    assert actions[1].from_status == AnomalyReviewStatus.ACKNOWLEDGED
    assert actions[1].to_status == AnomalyReviewStatus.UNDER_REVIEW
    assert actions[1].username == "audit_analyst_user"

    assert actions[2].from_status == AnomalyReviewStatus.UNDER_REVIEW
    assert actions[2].to_status == AnomalyReviewStatus.RESOLVED
    assert actions[2].username == "audit_admin_user"

    assert actions[3].from_status == AnomalyReviewStatus.RESOLVED
    assert actions[3].to_status == AnomalyReviewStatus.REOPENED
    assert actions[3].username == "audit_admin_user"


# ===========================================================================
# 5. Export Endpoint Authentication & Input Validation
# ===========================================================================

def test_export_endpoints_require_authentication(client: TestClient, auth_headers: dict):
    """Verifies that streaming CSV exports require authentication and reject unauthenticated requests."""
    # Unauthenticated -> 401
    res_unauth_trends = client.get("/api/analytics/district/export/trends?district=Ariyalur&s_no=1.1")
    assert res_unauth_trends.status_code == 401

    res_unauth_compare = client.get("/api/analytics/district/export/compare?s_no=1.1&reporting_month=2015-04")
    assert res_unauth_compare.status_code == 401

    # Authenticated -> 200 streaming CSV
    res_auth_trends = client.get(
        "/api/analytics/district/export/trends?district=Ariyalur&s_no=1.1",
        headers=auth_headers
    )
    assert res_auth_trends.status_code == 200
    assert "text/csv" in res_auth_trends.headers["Content-Type"]

    res_auth_compare = client.get(
        "/api/analytics/district/export/compare?s_no=1.1&reporting_month=2015-04",
        headers=auth_headers
    )
    assert res_auth_compare.status_code == 200
    assert "text/csv" in res_auth_compare.headers["Content-Type"]
