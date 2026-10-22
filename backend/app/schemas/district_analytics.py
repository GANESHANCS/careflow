from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DistrictCatalogResponse(BaseModel):
    districts: List[str] = Field(..., description="List of all 32 official districts present in the dataset")
    reporting_periods: List[str] = Field(..., description="Available reporting periods in chronological ISO YYYY-MM")
    financial_years: List[str] = Field(..., description="Observed financial years (e.g. 2015-16)")
    subgroup_types: List[str] = Field(..., description="Distinct subgroup disaggregation types available")
    total_observed_records: int = Field(..., description="Total recorded district observations in the database")
    source_name: str = Field(default="MoHFW / NHM District Item Performance Report", description="Source public dataset")
    geographic_level: str = Field(default="District (State of Tamil Nadu)", description="Administrative level")
    limitations: List[str] = Field(default_factory=list, description="Explicit boundaries and usage caveats")


class DistrictIndicatorItem(BaseModel):
    s_no: str = Field(..., description="Original MoHFW item serial code (e.g. 14.12.1)")
    parameter_name: str = Field(..., description="Official parameter description")
    available_subgroups: List[str] = Field(default_factory=list, description="Available subgroup slices")
    is_stock_metric: bool = Field(..., description="Whether this metric is a non-additive capacity/stock count")
    is_mapped: bool = Field(..., description="Whether a verified crosswalk to a canonical CAREFlow indicator exists")
    canonical_indicator_id: Optional[str] = Field(None, description="Mapped CAREFlow indicator ID if verified")
    canonical_indicator_name: Optional[str] = Field(None, description="Mapped CAREFlow indicator name if verified")
    mapping_status: Optional[str] = Field(None, description="Detailed crosswalk status: VERIFIED, AMBIGUOUS, UNMAPPED")


class DistrictIndicatorCatalogResponse(BaseModel):
    total_indicators: int
    mapped_count: int
    unmapped_count: int
    indicators: List[DistrictIndicatorItem]
    limitations_note: str = Field(
        default="Unmapped indicators expose verbatim MoHFW S.No. codes and labels without fabricated clinical definitions.",
        description="Catalog governance note"
    )


class DistrictTrendObservation(BaseModel):
    id: str
    reporting_month: str
    observation_date: str
    value: Optional[float] = None
    value_type: str = Field(..., description="Classification: VALID, ZERO, MISSING, INVALID")
    subgroup_type: str
    is_subgroup_total: bool
    reported_annual_total: Optional[float] = None
    source_file: str
    source_row: Optional[int] = None
    transformation_version: str
    last_import_job_id: Optional[int] = None


class DistrictMonthlyTrendsResponse(BaseModel):
    district: str
    s_no: str
    parameter_name: str
    subgroup_type: str
    is_subgroup_total: bool
    is_stock_metric: bool
    canonical_indicator_id: Optional[str] = None
    canonical_indicator_name: Optional[str] = None
    annual_total_reported: Optional[float] = None
    calculated_sum: Optional[float] = None
    valid_months_count: int
    zero_months_count: int
    missing_months_count: int
    total_months_count: int
    observations: List[DistrictTrendObservation]
    limitations: str = Field(
        default="District observations represent macro administrative health reporting and must not be combined with facility data.",
        description="Usage constraints"
    )


class DistrictComparisonItem(BaseModel):
    district: str
    value: Optional[float] = None
    value_type: str
    reported_annual_total: Optional[float] = None
    rank: Optional[int] = None


class DistrictComparisonResponse(BaseModel):
    s_no: str
    parameter_name: str
    reporting_month: str
    subgroup_type: str
    is_subgroup_total: bool
    is_stock_metric: bool
    total_districts: int
    reporting_districts: int
    state_mean: Optional[float] = None
    state_median: Optional[float] = None
    state_total: Optional[float] = None
    items: List[DistrictComparisonItem]
    data_note: str = Field(
        default="Comparisons strictly evaluate equal subgroup categories across identical reporting periods. Missing values are preserved.",
        description="Comparison methodology note"
    )


class DistrictCoverageItem(BaseModel):
    district: str
    total_records: int
    valid_records: int
    zero_records: int
    missing_records: int
    completeness_pct: float


class DistrictDataQualitySummaryResponse(BaseModel):
    total_records: int
    value_counts: Dict[str, int]
    subgroup_totals_count: int
    subgroup_slices_count: int
    non_additive_stock_rows: int
    districts_count: int
    parameters_count: int
    import_job: Optional[Dict[str, Any]] = None
    district_coverage: List[DistrictCoverageItem] = []
    audit_timestamp: str


# Phase 12B Verified Indicator Registry Schemas
class IndicatorMappingItem(BaseModel):
    s_no: str
    parameter_name: str
    canonical_id: Optional[str] = None
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    status: str
    rationale: str
    clinical_definition: Optional[str] = None
    provenance: str
    is_stock_metric: bool
    reviewed_at: str


class IndicatorRegistryResponse(BaseModel):
    total_items: int
    verified_count: int
    unmapped_count: int
    items: List[IndicatorMappingItem]


class IndicatorAuditReportResponse(BaseModel):
    total_parameters_observed: int
    verified_mappings_count: int
    ambiguous_mappings_count: int = 0
    provisional_mappings_count: int = 0
    unmapped_parameters_count: int
    verified_percentage: float
    unmapped_percentage: float
    stock_metrics_count: int
    verified_mappings: List[IndicatorMappingItem]
    ambiguous_mappings: List[IndicatorMappingItem] = []
    unmapped_indicators_sample: List[str]
    governance_note: str
    audit_timestamp: str


# ===========================================================================
# Phase 14: Healthcare Intelligence, Forecasting Readiness & Early-Warning Schemas
# ===========================================================================

class VerifiedIndicatorTimeSeriesPoint(BaseModel):
    month: str
    date: str
    value: Optional[float] = None
    value_type: str
    is_zero: bool = False
    is_missing: bool = False


class VerifiedIndicatorOverviewResponse(BaseModel):
    s_no: str
    parameter_name: str
    canonical_id: str
    canonical_name: str
    category: str
    unit: str
    mapping_status: str
    provenance: str
    rationale: str
    is_stock_metric: bool
    temporal_aggregation_permitted: bool
    district: str
    subgroup_type: str
    financial_year: str
    total_expected_months: int
    reported_months_count: int
    valid_months_count: int
    zero_months_count: int
    missing_months_count: int
    completeness_ratio: float
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    std_dev: Optional[float] = None
    points: List[VerifiedIndicatorTimeSeriesPoint]
    stock_warning: Optional[str] = None
    governance_notice: str = Field(
        default="Canonical healthcare metrics strictly derived from VERIFIED MoHFW crosswalks without concept conflation.",
        description="Governance notice"
    )


class ForecastingReadinessResponse(BaseModel):
    district: str
    s_no: str
    parameter_name: str
    canonical_id: Optional[str] = None
    canonical_name: Optional[str] = None
    subgroup_type: str
    financial_year: str
    requested_horizon: int
    is_ready: bool
    readiness_status: str
    readiness_reason: str
    dataset_limitation: str
    clinical_validation_disclaimer: str
    historical_months_available: int
    historical_months_required: int
    training_period: Optional[Dict[str, Any]] = None
    evaluation_period: Optional[Dict[str, Any]] = None
    baseline_models_evaluated: List[Dict[str, Any]] = []
    selected_baseline_model: Optional[str] = None
    held_out_metrics: Optional[Dict[str, float]] = None
    baseline_forecast: List[Dict[str, Any]] = []


class AnomalySignalItem(BaseModel):
    signal_id: str
    signal_type: str  # "HISTORICAL_OUTLIER_MAD", "MONTH_OVER_MONTH_SHIFT", "MISSING_REPORTING_PERIOD", "SPATIAL_DEVIATION"
    severity: str     # "INFO", "WARNING", "ELEVATED"
    district: str
    s_no: str
    parameter_name: str
    reporting_month: str
    observed_value: Optional[float] = None
    expected_baseline: Optional[float] = None
    deviation_score: float
    metric_unit: Optional[str] = None
    statistical_method: str
    rationale: str
    data_points_used: int
    review_status: str = "OPEN"
    last_reviewed_by_username: Optional[str] = None
    last_reviewed_at: Optional[str] = None
    disclaimer: str = (
        "STATISTICAL_SIGNAL — Indicates statistical variation requiring HMIS officer review. "
        "Not a clinical diagnosis, disease outbreak alert, or evidence of reporting fraud."
    )


class DistrictAnomalyReportResponse(BaseModel):
    s_no: Optional[str] = None
    district: Optional[str] = None
    reporting_month: Optional[str] = None
    financial_year: Optional[str] = None
    total_signals_detected: int
    signals: List[AnomalySignalItem]
    evaluation_summary: Dict[str, Any]
    governance_disclaimer: str = (
        "Statistical anomaly detection utilizes robust non-parametric estimation (Median Absolute Deviation). "
        "All alerts require human clinical and operational validation before administrative action."
    )


# ===========================================================================
# Phase 15: Anomaly Review Workflow & Governance Schemas
# ===========================================================================

class DistrictAnomalyReviewActionSchema(BaseModel):
    id: int
    review_id: str
    action: str
    from_status: str
    to_status: str
    notes: Optional[str] = None
    username: str
    created_at: str


class DistrictAnomalyReviewSchema(BaseModel):
    id: str
    signal_id: str
    district: str
    indicator_id: str
    reporting_month: str
    signal_type: str
    severity: str
    current_status: str
    trigger_reason: str
    metric_value: Optional[float] = None
    expected_range: Optional[str] = None
    last_reviewed_by_username: Optional[str] = None
    last_reviewed_at: Optional[str] = None
    resolution_reason: Optional[str] = None
    actions: List[DistrictAnomalyReviewActionSchema] = []


class AnomalyReviewActionRequest(BaseModel):
    action: str = Field(..., description="ACKNOWLEDGE, SET_UNDER_REVIEW, RESOLVE, REOPEN, or ADD_NOTE")
    notes: Optional[str] = Field(None, description="Clinical or administrative explanation / audit note")
    district: Optional[str] = None
    indicator_id: Optional[str] = None
    reporting_month: Optional[str] = None
    signal_type: Optional[str] = None
    trigger_reason: Optional[str] = None
    metric_value: Optional[float] = None
    expected_range: Optional[str] = None
