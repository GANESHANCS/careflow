from fastapi import APIRouter, Depends
from backend.app.api.deps import get_current_active_user
from backend.app.api.endpoints import health, auth, facilities, indicators, analytics, forecasts, imports

api_router = APIRouter()

# Public Endpoints
api_router.include_router(health.router, tags=["Health & System"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Security"])

# Protected Operational Workspaces (Requires Valid Authenticated User)
api_router.include_router(
    facilities.router,
    tags=["Facilities"],
    dependencies=[Depends(get_current_active_user)]
)
api_router.include_router(
    indicators.router,
    tags=["Indicators"],
    dependencies=[Depends(get_current_active_user)]
)
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics Engine"],
    dependencies=[Depends(get_current_active_user)]
)
api_router.include_router(
    forecasts.router,
    tags=["Forecasting & ML Engine"],
    dependencies=[Depends(get_current_active_user)]
)
api_router.include_router(
    imports.router,
    prefix="/imports",
    tags=["HMIS Data Imports"],
    dependencies=[Depends(get_current_active_user)]
)
