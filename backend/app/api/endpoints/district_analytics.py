from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.analytics.district_analytics import DistrictAnalyticsService
from backend.app.schemas.district_analytics import (
    DistrictCatalogResponse,
    DistrictIndicatorCatalogResponse,
    DistrictMonthlyTrendsResponse,
    DistrictComparisonResponse,
    DistrictDataQualitySummaryResponse,
)

router = APIRouter()


@router.get("/catalog", response_model=DistrictCatalogResponse)
def get_district_catalog(db: Session = Depends(get_db)):
    """
    Returns all 32 official districts present in the dataset, available reporting periods,
    and explicit governance and scope limitations.
    """
    service = DistrictAnalyticsService(db)
    return service.get_catalog_and_coverage()


@router.get("/indicators", response_model=DistrictIndicatorCatalogResponse)
def get_district_indicators(db: Session = Depends(get_db)):
    """
    Returns all 261 distinct S.No. items, official parameter descriptions, available
    subgroups, stock metric designations, and canonical crosswalk mappings.
    """
    service = DistrictAnalyticsService(db)
    return service.get_indicator_catalog()


@router.get("/trends", response_model=DistrictMonthlyTrendsResponse)
def get_district_monthly_trends(
    district: str = Query(..., description="Target district name (e.g. Ariyalur, Chennai)"),
    s_no: str = Query(..., description="Source parameter S.No. code (e.g. 14.12.1, 1.1)"),
    subgroup_type: Optional[str] = Query(None, description="Optional subgroup filter (defaults to TOTAL or 4. Total)"),
    start_month: Optional[str] = Query(None, description="Start reporting month (ISO YYYY-MM)"),
    end_month: Optional[str] = Query(None, description="End reporting month (ISO YYYY-MM)"),
    db: Session = Depends(get_db)
):
    """
    Fetches chronological 12-month observations (April 2015–March 2016) for a district and indicator,
    strictly distinguishing numeric zeroes from missing data and preserving non-additive stock totals.
    """
    service = DistrictAnalyticsService(db)
    return service.get_monthly_trends(
        district=district,
        s_no=s_no,
        subgroup_type=subgroup_type,
        start_month=start_month,
        end_month=end_month
    )


@router.get("/compare", response_model=DistrictComparisonResponse)
def get_district_comparison(
    s_no: str = Query(..., description="Source parameter S.No. code"),
    reporting_month: str = Query(..., description="Target reporting period (ISO YYYY-MM, e.g. 2015-06)"),
    subgroup_type: Optional[str] = Query(None, description="Subgroup slice (e.g. TOTAL)"),
    districts: Optional[List[str]] = Query(None, description="Optional subset of districts to compare"),
    db: Session = Depends(get_db)
):
    """
    Performs cross-district comparison for a single indicator and period.
    Rejects or explicitly flags incomparable metrics; calculates valid state mean/median.
    """
    service = DistrictAnalyticsService(db)
    return service.get_district_comparison(
        s_no=s_no,
        reporting_month=reporting_month,
        subgroup_type=subgroup_type,
        districts=districts
    )


@router.get("/quality", response_model=DistrictDataQualitySummaryResponse)
def get_district_data_quality_summary(db: Session = Depends(get_db)):
    """
    Provides data quality analytics, validation counts (VALID, ZERO, MISSING, INVALID),
    subgroup distributions, and import job audit provenance.
    """
    service = DistrictAnalyticsService(db)
    return service.get_data_quality_summary()
