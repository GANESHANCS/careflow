from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.api.deps import get_current_active_user
from backend.app.services.analytics.district_analytics import DistrictAnalyticsService
from backend.app.services.analytics.district_export import DistrictExportService
from backend.app.schemas.district_analytics import (
    DistrictCatalogResponse,
    DistrictIndicatorCatalogResponse,
    DistrictMonthlyTrendsResponse,
    DistrictComparisonResponse,
    DistrictDataQualitySummaryResponse,
    IndicatorRegistryResponse,
    IndicatorAuditReportResponse,
)

router = APIRouter()


@router.get("/catalog", response_model=DistrictCatalogResponse)
def get_district_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns all 32 official districts present in the dataset, available reporting periods,
    and explicit governance and scope limitations.
    """
    service = DistrictAnalyticsService(db)
    return service.get_catalog_and_coverage()


@router.get("/indicators", response_model=DistrictIndicatorCatalogResponse)
def get_district_indicators(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns all 261 distinct S.No. items, official parameter descriptions, available
    subgroups, stock metric designations, and canonical crosswalk mappings.
    """
    service = DistrictAnalyticsService(db)
    return service.get_indicator_catalog()


@router.get("/indicators/registry", response_model=IndicatorRegistryResponse)
def get_indicator_registry(
    status: Optional[str] = Query(None, description="Optional status filter: VERIFIED, PROVISIONAL, UNMAPPED"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 12B Verified Indicator Registry: Lists clinical indicators with explicit crosswalk
    rationales, clinical definitions, units, and non-additive stock classification.
    """
    service = DistrictAnalyticsService(db)
    return service.get_indicator_registry(status_filter=status)


@router.get("/indicators/audit", response_model=IndicatorAuditReportResponse)
def get_indicator_audit_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 12B Indicator Audit Report: High-integrity breakdown of verified, provisional,
    and unmapped indicator counts, percentages, and governance notes.
    """
    service = DistrictAnalyticsService(db)
    return service.get_indicator_audit_report()


@router.get("/trends", response_model=DistrictMonthlyTrendsResponse)
def get_district_monthly_trends(
    district: str = Query(..., description="Target district name (e.g. Ariyalur, Chennai)"),
    s_no: str = Query(..., description="Source parameter S.No. code (e.g. 14.12.1, 1.1)"),
    subgroup_type: Optional[str] = Query(None, description="Optional subgroup filter (defaults to TOTAL or 4. Total)"),
    start_month: Optional[str] = Query(None, description="Start reporting month (ISO YYYY-MM)"),
    end_month: Optional[str] = Query(None, description="End reporting month (ISO YYYY-MM)"),
    financial_year: Optional[str] = Query(None, description="Optional financial year filter (e.g. 2015-16)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Fetches chronological monthly observations for a district and indicator,
    strictly distinguishing numeric zeroes from missing data and preserving non-additive stock totals.
    """
    service = DistrictAnalyticsService(db)
    return service.get_monthly_trends(
        district=district,
        s_no=s_no,
        subgroup_type=subgroup_type,
        start_month=start_month,
        end_month=end_month,
        financial_year=financial_year
    )


@router.get("/compare", response_model=DistrictComparisonResponse)
def get_district_comparison(
    s_no: str = Query(..., description="Source parameter S.No. code"),
    reporting_month: str = Query(..., description="Target reporting period (ISO YYYY-MM, e.g. 2015-06)"),
    subgroup_type: Optional[str] = Query(None, description="Subgroup slice (e.g. TOTAL)"),
    districts: Optional[List[str]] = Query(None, description="Optional subset of districts to compare"),
    financial_year: Optional[str] = Query(None, description="Optional financial year filter (e.g. 2015-16)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
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
        districts=districts,
        financial_year=financial_year
    )


@router.get("/export/trends")
def export_district_trends_csv(
    district: str = Query(..., description="Target district name"),
    s_no: str = Query(..., description="Source parameter S.No. code"),
    subgroup_type: Optional[str] = Query(None, description="Optional subgroup filter"),
    start_month: Optional[str] = Query(None, description="Start month (YYYY-MM)"),
    end_month: Optional[str] = Query(None, description="End month (YYYY-MM)"),
    financial_year: Optional[str] = Query(None, description="Financial year (e.g. 2015-16)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 12A CSV Export: Streams RFC 4180 compliant CSV of filtered district observations.
    Includes formula-injection mitigation, audit headers, and bounded query results.
    """
    export_service = DistrictExportService(db)
    clean_dist = district.replace(" ", "_").lower()
    clean_sno = s_no.replace(".", "_")
    filename = f"district_trends_{clean_dist}_{clean_sno}.csv"

    return StreamingResponse(
        export_service.export_trends_csv(
            district=district,
            s_no=s_no,
            subgroup_type=subgroup_type,
            start_month=start_month,
            end_month=end_month,
            financial_year=financial_year
        ),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/export/compare")
def export_district_comparison_csv(
    s_no: str = Query(..., description="Source parameter S.No. code"),
    reporting_month: str = Query(..., description="Target reporting period (YYYY-MM)"),
    subgroup_type: Optional[str] = Query(None, description="Subgroup slice"),
    districts: Optional[List[str]] = Query(None, description="Optional list of districts"),
    financial_year: Optional[str] = Query(None, description="Financial year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 12A CSV Export: Streams RFC 4180 compliant cross-district comparison CSV.
    Includes rankings, state mean, median, total, and formula-injection mitigation.
    """
    export_service = DistrictExportService(db)
    clean_sno = s_no.replace(".", "_")
    filename = f"district_compare_{clean_sno}_{reporting_month}.csv"

    return StreamingResponse(
        export_service.export_comparison_csv(
            s_no=s_no,
            reporting_month=reporting_month,
            subgroup_type=subgroup_type,
            districts=districts,
            financial_year=financial_year
        ),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/quality", response_model=DistrictDataQualitySummaryResponse)
def get_district_data_quality_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Provides data quality analytics, validation counts (VALID, ZERO, MISSING, INVALID),
    subgroup distributions, and import job audit provenance.
    """
    service = DistrictAnalyticsService(db)
    return service.get_data_quality_summary()
