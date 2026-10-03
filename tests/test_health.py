from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from backend.app.main import app
from backend.app.db.session import get_db

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "CAREFlow" in data["message"]


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "CAREFlow India"
    assert data["database_status"] == "healthy"
    assert "python_version" in data


def test_healthz_liveness_endpoint():
    response = client.get("/api/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "CAREFlow" in data["app_name"]


def test_readyz_readiness_endpoint():
    response = client.get("/api/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database"] == "connected"


def test_degraded_health_returns_503():
    def mock_broken_db():
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Simulated DB connection failure")
        yield mock_session

    app.dependency_overrides[get_db] = mock_broken_db
    try:
        # /api/health should return 503
        resp_health = client.get("/api/health")
        assert resp_health.status_code == 503
        data_health = resp_health.json()
        assert data_health["status"] == "degraded"
        assert data_health["database_status"] == "unhealthy"

        # /api/readyz should return 503
        resp_readyz = client.get("/api/readyz")
        assert resp_readyz.status_code == 503
        data_readyz = resp_readyz.json()
        assert data_readyz["status"] == "not_ready"

        # /api/healthz (liveness) should still return 200
        resp_healthz = client.get("/api/healthz")
        assert resp_healthz.status_code == 200
        assert resp_healthz.json()["status"] == "alive"
    finally:
        app.dependency_overrides.pop(get_db, None)
