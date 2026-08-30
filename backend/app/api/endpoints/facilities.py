from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.facility_service import FacilityService
from backend.app.services.observation_service import ObservationService
from backend.app.schemas.facility import FacilityResponse, FacilityListResponse
from backend.app.schemas.observation import ObservationListResponse

router = APIRouter()


@router.get("/facilities", response_model=FacilityListResponse)
def list_facilities(
    state: Optional[str] = Query(None, description="Filter by state name"),
    district: Optional[str] = Query(None, description="Filter by district name"),
    facility_type: Optional[str] = Query(None, description="Filter by facility type (DH, CHC, PHC, SC, etc.)"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    db: Session = Depends(get_db)
):
    """
    List healthcare facilities with pagination and state/district filters.
    """
    service = FacilityService(db)
    items, total = service.list_facilities(
        state=state, district=district, facility_type=facility_type, skip=skip, limit=limit
    )
    return FacilityListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/facilities/{facility_id}", response_model=FacilityResponse)
def get_facility(
    facility_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed facility metadata by facility_id (or 404 error response).
    """
    service = FacilityService(db)
    facility = service.get_facility(facility_id)
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with ID '{facility_id}' not found."
        )
    return facility


@router.get("/facilities/{facility_id}/observations", response_model=ObservationListResponse)
def get_facility_observations(
    facility_id: str,
    indicator_code: Optional[str] = Query(None, description="Filter by indicator code (e.g. opd_attendance)"),
    start_month: Optional[str] = Query(None, description="Filter start month (YYYY-MM)"),
    end_month: Optional[str] = Query(None, description="Filter end month (YYYY-MM)"),
    skip: int = Query(0, ge=0, description="Pagination skip offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    db: Session = Depends(get_db)
):
    """
    List monthly observations for a specific facility with indicator & date filtering.
    """
    service = ObservationService(db)
    res = service.get_facility_observations(
        facility_id=facility_id,
        indicator_code=indicator_code,
        start_month=start_month,
        end_month=end_month,
        skip=skip,
        limit=limit
    )
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with ID '{facility_id}' not found."
        )
    items, total = res
    return ObservationListResponse(
        facility_id=facility_id,
        items=items,
        total=total,
        skip=skip,
        limit=limit
    )
