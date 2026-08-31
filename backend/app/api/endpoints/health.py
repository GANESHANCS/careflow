import sys
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.db.session import get_db, engine
from backend.app.schemas.health import HealthResponse, DatabaseHealthStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def get_health(db: Session = Depends(get_db)):
    """
    Public System Health Endpoint. Performs real database connectivity verification via 'SELECT 1'.
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
