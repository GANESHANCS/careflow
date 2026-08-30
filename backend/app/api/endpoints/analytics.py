from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.analytics.summary import ExecutiveSummaryService
from backend.app.services.analytics.trends import TimeSeriesTrendsService
from backend.app.services.analytics.regional import RegionalAnalyticsService
from backend.app.services.analytics.facility import FacilityAnalyticsService
from backend.app.services.analytics.comparison import FacilityComparisonService
from backend.app.services.analytics.data_quality import DataQualityAnalyticsService

from backend.app.schemas.analytics import (
    ExecutiveSummaryResponse,
    MonthlyTrendsResponse,
    RegionalAnalyticsResponse,
    FacilityAnalyticsResponse,
    FacilityComparisonResponse,
    DataQualityAnalyticsResponse
)

router = APIRouter()


@router.get("/summary", response_model=ExecutiveSummaryResponse)
def get_executive_summary(
    state: Optional[str] = Query(None, description="Filter summary by state"),
    district: Optional[str] = Query(None, description="Filter summary by district"),
    db: Session = Depends(get_db)
):
    """
    Get executive summary indicators, active facility counts, reporting completeness %, and MoM growth.
    """
    service = ExecutiveSummaryService(db)
    return service.get_summary(state=state, district=district)


@router.get("/trends", response_model=MonthlyTrendsResponse)
def get_monthly_trends(
    indicator_code: Optional[str] = Query(None, description="Filter by indicator code (e.g. opd_attendance)"),
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    facility_id: Optional[str] = Query(None, description="Filter by facility ID"),
    start_month: Optional[str] = Query(None, description="Filter start month (YYYY-MM)"),
    end_month: Optional[str] = Query(None, description="Filter end month (YYYY-MM)"),
    db: Session = Depends(get_db)
):
    """
    Get monthly time-series aggregations (totals, averages, completeness, facility counts).
    """
    service = TimeSeriesTrendsService(db)
    return service.get_monthly_trends(
        indicator_code=indicator_code,
        state=state,
        district=district,
        facility_id=facility_id,
        start_month=start_month,
        end_month=end_month
    )


@router.get("/regional", response_model=RegionalAnalyticsResponse)
def get_regional_analytics(
    level: str = Query("district", description="Aggregation level: 'state' or 'district'"),
    indicator_code: Optional[str] = Query(None, description="Filter by indicator code"),
    state: Optional[str] = Query(None, description="Filter by state"),
    district: Optional[str] = Query(None, description="Filter by district"),
    reporting_month: Optional[str] = Query(None, description="Target reporting month (YYYY-MM)"),
    db: Session = Depends(get_db)
):
    """
    Get regional state or district analytics including total utilization, average per facility, and growth rates.
    """
    if level.lower() not in ["state", "district"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'level' must be either 'state' or 'district'."
        )
    service = RegionalAnalyticsService(db)
    return service.get_regional_analytics(
        level=level,
        indicator_code=indicator_code,
        state=state,
        district=district,
        reporting_month=reporting_month
    )


@router.get("/facilities", response_model=FacilityAnalyticsResponse)
def get_facility_analytics(
    facility_id: str = Query(..., description="Target facility ID"),
    indicator_code: Optional[str] = Query(None, description="Optional indicator code filter"),
    db: Session = Depends(get_db)
):
    """
    Get facility-level analytics, historical indicator trends, completeness, missing months, and MoM growth.
    """
    service = FacilityAnalyticsService(db)
    result = service.get_facility_analytics(facility_id=facility_id, indicator_code=indicator_code)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with ID '{facility_id}' not found."
        )
    return result


@router.get("/compare", response_model=FacilityComparisonResponse)
def compare_facilities(
    facility_ids: List[str] = Query(..., description="List of facility IDs to compare"),
    indicator_code: str = Query(..., description="Target indicator code (e.g. opd_attendance)"),
    start_month: Optional[str] = Query(None, description="Start month (YYYY-MM)"),
    end_month: Optional[str] = Query(None, description="End month (YYYY-MM)"),
    db: Session = Depends(get_db)
):
    """
    Compare multiple facilities side-by-side for a target indicator with summary statistics.
    """
    if not facility_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one facility_id must be provided for comparison."
        )
    service = FacilityComparisonService(db)
    res = service.compare_facilities(
        facility_ids=facility_ids,
        indicator_code=indicator_code,
        start_month=start_month,
        end_month=end_month
    )
    if "error" in res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res["error"]
        )
    return res


@router.get("/data-quality", response_model=DataQualityAnalyticsResponse)
def get_data_quality_analytics(
    db: Session = Depends(get_db)
):
    """
    Get database-backed data quality metrics, issue counts, audit score, and incomplete reporting facilities.
    """
    service = DataQualityAnalyticsService(db)
    return service.get_quality_analytics()
