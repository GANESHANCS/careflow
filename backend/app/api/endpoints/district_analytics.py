from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.user import User
from backend.app.api.deps import get_current_active_user
from backend.app.services.analytics.district_analytics import DistrictAnalyticsService
from backend.app.services.analytics.district_export import DistrictExportService
from backend.app.services.analytics.healthcare_intelligence import (
    HealthcareIntelligenceService,
    IneligibleIndicatorError,
)
from backend.app.services.analytics.source_registry import SourceRegistryCatalog, SourceRegistrySummary
from backend.app.services.analytics.cross_year_comparability import (
    CrossYearComparabilityService,
    CrossYearComparabilityReport,
)
from backend.app.services.analytics.anomaly_review_service import DistrictAnomalyReviewService
from backend.app.schemas.district_analytics import (
    DistrictCatalogResponse,
    DistrictIndicatorCatalogResponse,
    DistrictMonthlyTrendsResponse,
    DistrictComparisonResponse,
    DistrictDataQualitySummaryResponse,
    IndicatorRegistryResponse,
    IndicatorAuditReportResponse,
    VerifiedIndicatorOverviewResponse,
    ForecastingReadinessResponse,
    DistrictAnomalyReportResponse,
    DistrictAnomalyReviewSchema,
    DistrictAnomalyReviewActionSchema,
    AnomalyReviewActionRequest,
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


# ===========================================================================
# Phase 14: Healthcare Intelligence, Forecasting Readiness & Early-Warning APIs
# ===========================================================================

@router.get("/intelligence/overview", response_model=VerifiedIndicatorOverviewResponse)
def get_verified_intelligence_overview(
    district: str = Query(..., description="Target district name (e.g. Ariyalur)"),
    s_no: str = Query(..., description="Target verified indicator S.No. (e.g. 1.1, 14.12.1)"),
    subgroup_type: Optional[str] = Query(None, description="Optional subgroup slice (e.g. TOTAL)"),
    financial_year: Optional[str] = Query("2015-16", description="Optional financial year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 14B: Fetches complete chronological time-series for a verified indicator,
    strictly distinguishing zero from missing, reporting completeness, non-additive stock alerts,
    and official MoHFW provenance. Rejects unmapped or ambiguous indicators.
    """
    service = HealthcareIntelligenceService(db)
    try:
        return service.get_verified_indicator_timeseries(
            district=district,
            s_no=s_no,
            subgroup_type=subgroup_type,
            financial_year=financial_year
        )
    except IneligibleIndicatorError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/intelligence/readiness", response_model=ForecastingReadinessResponse)
def evaluate_forecasting_readiness(
    district: str = Query(..., description="Target district name"),
    s_no: str = Query(..., description="Target verified indicator S.No."),
    horizon: int = Query(3, ge=1, le=12, description="Forecast horizon in months (1-12)"),
    subgroup_type: Optional[str] = Query(None, description="Optional subgroup slice"),
    financial_year: Optional[str] = Query("2015-16", description="Optional financial year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 14C: Evaluates forecasting readiness for a verified indicator on single-year data.
    Enforces chronological hold-out train/test split with zero future-data leakage.
    Evaluates naïve and moving average baselines on hold-out data. Returns explicit
    insufficient-data status when long horizons (>3m) or seasonal requirements are not met.
    """
    service = HealthcareIntelligenceService(db)
    try:
        return service.evaluate_forecasting_readiness(
            district=district,
            s_no=s_no,
            horizon=horizon,
            subgroup_type=subgroup_type,
            financial_year=financial_year
        )
    except IneligibleIndicatorError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/intelligence/anomalies", response_model=DistrictAnomalyReportResponse)
def detect_district_anomalies(
    district: Optional[str] = Query(None, description="Optional target district"),
    s_no: Optional[str] = Query(None, description="Optional target verified indicator S.No."),
    reporting_month: Optional[str] = Query(None, description="Optional target reporting period (YYYY-MM)"),
    subgroup_type: Optional[str] = Query(None, description="Optional subgroup slice"),
    financial_year: Optional[str] = Query("2015-16", description="Optional financial year"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 14D: Conservative statistical early-warning and change detection.
    Detects MAD outliers (>3.5 modified z-score), abrupt MoM shifts, missing reporting periods,
    and spatial deviations relative to state distributions.
    All alerts labeled as statistical signals requiring human review (not clinical diagnoses).
    """
    service = HealthcareIntelligenceService(db)
    try:
        return service.detect_anomalies(
            district=district,
            s_no=s_no,
            reporting_month=reporting_month,
            subgroup_type=subgroup_type,
            financial_year=financial_year
        )
    except IneligibleIndicatorError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/intelligence/source-registry", response_model=SourceRegistrySummary)
def get_source_registry(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 15A: Returns registered HMIS data sources, file hashes, ingestion readiness,
    and official government data acquisition status for Tamil Nadu.
    """
    from sqlalchemy import func
    from backend.app.db.models.district_observation import DistrictObservation
    fy_counts = dict(
        db.query(DistrictObservation.financial_year, func.count(DistrictObservation.id))
        .group_by(DistrictObservation.financial_year)
        .all()
    )
    return SourceRegistryCatalog.get_summary(fy_counts)


@router.get("/intelligence/cross-year-comparability", response_model=CrossYearComparabilityReport)
def get_cross_year_comparability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 15C: Evaluates cross-year data quality, schema stability, missing months,
    district boundary bifurcations, and indicator semantic consistency.
    """
    return CrossYearComparabilityService.get_comparability_report(db)


@router.get("/intelligence/anomalies/reviews", response_model=List[DistrictAnomalyReviewSchema])
def list_anomaly_reviews(
    district: Optional[str] = Query(None, description="Filter by district"),
    indicator_id: Optional[str] = Query(None, description="Filter by indicator ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (OPEN, ACKNOWLEDGED, UNDER_REVIEW, RESOLVED, REOPENED)"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 15E: Lists administrative review records and audit history for anomaly signals.
    """
    reviews = DistrictAnomalyReviewService.list_reviews(
        db=db,
        district=district,
        indicator_id=indicator_id,
        status_filter=status_filter,
        limit=limit,
        offset=offset
    )
    res = []
    for r in reviews:
        actions_schema = [
            DistrictAnomalyReviewActionSchema(
                id=a.id,
                review_id=a.review_id,
                action=a.action,
                from_status=a.from_status,
                to_status=a.to_status,
                notes=a.notes,
                username=a.username,
                created_at=a.created_at.isoformat()
            )
            for a in r.actions
        ]
        res.append(
            DistrictAnomalyReviewSchema(
                id=r.id,
                signal_id=r.signal_id,
                district=r.district,
                indicator_id=r.indicator_id,
                reporting_month=r.reporting_month,
                signal_type=r.signal_type,
                severity=r.severity,
                current_status=r.current_status,
                trigger_reason=r.trigger_reason,
                metric_value=r.metric_value,
                expected_range=r.expected_range,
                last_reviewed_by_username=r.last_reviewed_by_username,
                last_reviewed_at=r.last_reviewed_at.isoformat() if r.last_reviewed_at else None,
                resolution_reason=r.resolution_reason,
                actions=actions_schema
            )
        )
    return res


@router.post("/intelligence/anomalies/reviews/{signal_id}/action", response_model=DistrictAnomalyReviewSchema)
def apply_anomaly_review_action(
    signal_id: str,
    payload: AnomalyReviewActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Phase 15E: Applies an administrative review transition (ACKNOWLEDGE, SET_UNDER_REVIEW,
    RESOLVE, REOPEN, ADD_NOTE) with user attribution and immutable audit logging.
    Requires ADMIN or ANALYST role.
    """
    review = DistrictAnomalyReviewService.apply_review_action(
        db=db,
        signal_id=signal_id,
        action=payload.action,
        notes=payload.notes,
        current_user=current_user,
        district=payload.district,
        indicator_id=payload.indicator_id,
        reporting_month=payload.reporting_month,
        signal_type=payload.signal_type,
        trigger_reason=payload.trigger_reason,
        metric_value=payload.metric_value,
        expected_range=payload.expected_range
    )
    actions_schema = [
        DistrictAnomalyReviewActionSchema(
            id=a.id,
            review_id=a.review_id,
            action=a.action,
            from_status=a.from_status,
            to_status=a.to_status,
            notes=a.notes,
            username=a.username,
            created_at=a.created_at.isoformat()
        )
        for a in review.actions
    ]
    return DistrictAnomalyReviewSchema(
        id=review.id,
        signal_id=review.signal_id,
        district=review.district,
        indicator_id=review.indicator_id,
        reporting_month=review.reporting_month,
        signal_type=review.signal_type,
        severity=review.severity,
        current_status=review.current_status,
        trigger_reason=review.trigger_reason,
        metric_value=review.metric_value,
        expected_range=review.expected_range,
        last_reviewed_by_username=review.last_reviewed_by_username,
        last_reviewed_at=review.last_reviewed_at.isoformat() if review.last_reviewed_at else None,
        resolution_reason=review.resolution_reason,
        actions=actions_schema
    )
