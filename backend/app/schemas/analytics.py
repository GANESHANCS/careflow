from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class ExecutiveSummaryResponse(BaseModel):
    latest_period: Optional[str] = None
    previous_period: Optional[str] = None
    total_facilities: int
    reporting_facilities: int
    reporting_completeness_pct: float
    totals_by_indicator: Dict[str, float]
    indicator_names: Dict[str, str] = {}
    mom_changes: Dict[str, Optional[float]] = {}


class MonthlyTrendPoint(BaseModel):
    reporting_month: str
    observation_date: str
    total_value: float
    average_per_facility: float
    reporting_facilities: int
    total_facilities: int
    completeness_pct: float
    observation_count: int


class MonthlyTrendsFilter(BaseModel):
    indicator_code: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    facility_id: Optional[str] = None
    start_month: Optional[str] = None
    end_month: Optional[str] = None


class MonthlyTrendsResponse(BaseModel):
    filters: MonthlyTrendsFilter
    total_facilities: int
    series: List[MonthlyTrendPoint]


class RegionMetricPoint(BaseModel):
    region_name: str
    level: str
    reporting_month: str
    total_facilities: int
    reporting_facilities: int
    completeness_pct: float
    total_utilization: float
    average_per_reporting_facility: float
    median_per_reporting_facility: float
    mom_change_pct: Optional[float] = None


class RegionalAnalyticsResponse(BaseModel):
    level: str
    reporting_month: Optional[str] = None
    indicator_code: Optional[str] = None
    regions: List[RegionMetricPoint]


class FacilityLatestMetric(BaseModel):
    indicator_code: str
    indicator_name: str
    latest_reporting_month: str
    latest_value: Optional[float] = None
    value_type: str
    previous_value: Optional[float] = None
    mom_change_pct: Optional[float] = None


class FacilityObservationPoint(BaseModel):
    reporting_month: str
    observation_date: str
    indicator_code: str
    indicator_name: str
    value: Optional[float] = None
    value_type: str


class FacilityAnalyticsResponse(BaseModel):
    facility_id: str
    facility_code: Optional[str] = None
    facility_name: str
    facility_type: str
    state: str
    district: str
    sub_district: Optional[str] = None
    total_expected_months: int
    reported_months_count: int
    completeness_pct: float
    missing_months: List[str]
    latest_metrics: List[FacilityLatestMetric]
    history: List[FacilityObservationPoint]


class ComparisonFacilitySummary(BaseModel):
    facility_id: str
    facility_name: str
    facility_type: str
    district: str
    average_value: Optional[float] = None
    median_value: Optional[float] = None
    latest_value: Optional[float] = None
    trend_direction: str
    completeness_pct: float


class FacilityComparisonResponse(BaseModel):
    indicator_code: str
    indicator_name: Optional[str] = None
    interpretation_note: str
    facilities: List[ComparisonFacilitySummary]
    timeseries: List[Dict[str, Any]]


class DataQualityIssueItem(BaseModel):
    id: str
    audit_timestamp: str
    category: str
    severity: str
    affected_records: int
    description: str


class IncompleteFacilityItem(BaseModel):
    facility_id: str
    facility_name: str
    state: str
    district: str
    reported_months: int
    expected_months: int
    completeness_pct: float


class ObservationBreakdownSchema(BaseModel):
    valid_count: int = 0
    zero_count: int = 0
    missing_count: int = 0
    invalid_count: int = 0
    imputed_count: int = 0
    total_observations: int = 0


class CompletenessSummarySchema(BaseModel):
    expected_observations: int = 0
    actual_reported_observations: int = 0
    completeness_pct: float = 0.0
    total_facilities: int = 0
    reporting_facilities: int = 0


class MonthlyQualityPointSchema(BaseModel):
    reporting_month: str
    completeness_pct: float
    reporting_facilities: int
    total_facilities: int
    issue_count: int
    status: str = "HEALTHY"


class DataQualityAnalyticsResponse(BaseModel):
    overall_quality_score: float
    total_issues: int
    severity_counts: Dict[str, int]
    category_counts: Dict[str, int]
    incomplete_facilities_count: int
    incomplete_facilities: List[IncompleteFacilityItem]
    issues: List[DataQualityIssueItem]
    latest_period: Optional[str] = None
    observation_breakdown: Optional[ObservationBreakdownSchema] = None
    completeness_summary: Optional[CompletenessSummarySchema] = None
    monthly_timeline: List[MonthlyQualityPointSchema] = []
