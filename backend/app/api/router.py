from fastapi import APIRouter
from backend.app.api.endpoints import health, auth, facilities, indicators, analytics, forecasts

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Security"])
api_router.include_router(facilities.router, tags=["Facilities"])
api_router.include_router(indicators.router, tags=["Indicators"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics Engine"])
api_router.include_router(forecasts.router, tags=["Forecasting & ML Engine"])
