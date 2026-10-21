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
