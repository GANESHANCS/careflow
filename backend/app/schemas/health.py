from typing import Optional
from pydantic import BaseModel


class DatabaseHealthStatus(BaseModel):
    status: str # "healthy" or "unhealthy"
    engine: str
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app_name: str
    version: str
    environment: str
    python_version: str
    database_status: str
    timestamp: str
    database: DatabaseHealthStatus
