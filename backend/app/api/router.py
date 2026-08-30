from fastapi import APIRouter
from backend.app.api.endpoints import health, facilities, indicators, analytics

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(facilities.router, tags=["Facilities"])
api_router.include_router(indicators.router, tags=["Indicators"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics Engine"])
