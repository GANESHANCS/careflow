import sys
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.db.session import get_db, engine
from backend.app.schemas.health import HealthResponse, DatabaseHealthStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(response: Response, db: Session = Depends(get_db)):
    """
    Public System Health Endpoint. Performs real database connectivity verification via 'SELECT 1'.
    Returns HTTP 200 when healthy, or HTTP 503 Service Unavailable when database connection fails.
    Safe for production status monitoring without exposing database URLs or internal credentials.
    """
    db_status = "unhealthy"
    db_error = None
    engine_name = engine.dialect.name

    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
        db_error = "Database connection failed"

    overall_status = "healthy" if db_status == "healthy" else "degraded"
    if overall_status != "healthy":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=overall_status,
        app_name=settings.PROJECT_NAME,
        version=settings.PROJECT_VERSION,
        environment=settings.ENVIRONMENT,
        python_version=sys.version.split()[0],
        database_status=db_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=DatabaseHealthStatus(
            status=db_status,
            engine=engine_name,
            error=db_error
        )
    )


@router.get("/healthz")
def liveness_check():
    """
    Liveness probe for container orchestrators (Kubernetes / Docker).
    Returns 200 OK immediately if the web process is running.
    """
    return {
        "status": "alive",
        "app_name": settings.PROJECT_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/readyz")
def readiness_check(response: Response, db: Session = Depends(get_db)):
    """
    Readiness probe for container orchestrators.
    Returns 200 OK if critical dependencies (database) are accessible,
    or 503 Service Unavailable if dependencies are unreachable.
    """
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

