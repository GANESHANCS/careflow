import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.core.security import create_access_token, hash_password
from backend.app.core.rate_limit import login_rate_limiter
from backend.app.db.models.user import User


def test_protected_endpoint_authentication(client: TestClient, auth_headers: dict):
    # Missing token -> 401
    res_no_token = client.get("/api/analytics/summary")
    assert res_no_token.status_code == 401
    assert "UNAUTHORIZED" in res_no_token.json()["error"]["code"]

    # Invalid token -> 401
    res_bad_token = client.get("/api/analytics/summary", headers={"Authorization": "Bearer invalid_token_123"})
    assert res_bad_token.status_code == 401

    # Expired token -> 401
    expired_token = create_access_token(subject=1, role="ANALYST", expires_delta=timedelta(seconds=-3600))
    res_expired = client.get("/api/analytics/summary", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401

    # Valid token -> 200
    res_valid = client.get("/api/analytics/summary", headers=auth_headers)
    assert res_valid.status_code == 200


def test_request_id_middleware(client: TestClient, auth_headers: dict):
    # Auto-generate Request ID
    res = client.get("/api/health")
    assert "X-Request-ID" in res.headers
    auto_id = res.headers["X-Request-ID"]
    assert len(auto_id) > 10

    # Custom Request ID Propagation
    custom_id = "req_custom_trace_9999"
    res_custom = client.get("/api/health", headers={"X-Request-ID": custom_id})
    assert res_custom.headers["X-Request-ID"] == custom_id


def test_security_headers(client: TestClient):
    res = client.get("/api/health")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


def test_sanitized_validation_error(client: TestClient, auth_headers: dict):
    # Invalid horizon (5) returns sanitized validation error
    res = client.get("/api/forecast?facility_id=fac1&indicator_code=opd&horizon=5", headers=auth_headers)
    assert res.status_code == 400
    data = res.json()
    assert "detail" in data
    assert "error" in data
    assert data["error"]["code"] == "HTTP_400"
    assert "X-Request-ID" in res.headers


def test_cors_behavior(client: TestClient):
    # Disallowed origin check
    res = client.options("/api/health", headers={
        "Origin": "http://malicious-domain.com",
        "Access-Control-Request-Method": "GET"
    })
    # CORSMiddleware does not attach Access-Control-Allow-Origin for unauthorized origins
    assert "Access-Control-Allow-Origin" not in res.headers or res.headers.get("Access-Control-Allow-Origin") != "http://malicious-domain.com"


def test_health_endpoint_public_safety(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("healthy", "degraded")
    assert data["database"]["status"] == "healthy"
    # Verify no database URLs, passwords, or secret paths are disclosed
    res_str = res.text
    assert "sqlite:///" not in res_str
    assert "postgresql://" not in res_str
    assert "password" not in res_str.lower()


def test_login_rate_limiting(client: TestClient):
    login_rate_limiter.clear()

    # Perform 5 failed attempts
    for i in range(5):
        res = client.post("/api/auth/login", json={
            "username": "rate_limit_test_user",
            "password": "wrong_password"
        })
        assert res.status_code == 401

    # 6th attempt should be blocked with 429 Too Many Requests
    res_blocked = client.post("/api/auth/login", json={
        "username": "rate_limit_test_user",
        "password": "wrong_password"
    })
    assert res_blocked.status_code == 429
    assert "Too many login attempts" in res_blocked.json()["detail"]
    assert res_blocked.json()["error"]["code"] == "TOO_MANY_REQUESTS"

    login_rate_limiter.clear()


def test_api_versioning_compatibility(client: TestClient, auth_headers: dict):
    # /api/health and /api/v1/health both resolve
    res1 = client.get("/api/health")
    res2 = client.get("/api/v1/health")
    assert res1.status_code == 200
    assert res2.status_code == 200

    # Protected endpoints resolve under both prefixes
    res_api = client.get("/api/analytics/summary", headers=auth_headers)
    res_v1 = client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert res_api.status_code == 200
    assert res_v1.status_code == 200
