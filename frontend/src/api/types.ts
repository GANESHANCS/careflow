// API Type Definitions for CAREFlow Backend Service

export interface User {
  id: number;
  username: string;
  email: string | null;
  role: 'ADMIN' | 'ANALYST' | 'VIEWER';
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  environment: string;
  python_version: string;
  database_status: string;
  timestamp: string;
  database: {
    status: string;
    engine: string;
    error: string | null;
  };
}

export interface Facility {
  id: string;
  facility_code: string | null;
  facility_name: string;
  facility_type: string;
  state: string;
  district: string;
  sub_district: string | null;
  raw_facility_name?: string;
  raw_district_name?: string;
}

export interface FacilityListResponse {
  items: Facility[];
  total: number;
  skip: number;
  limit: number;
}

export interface Indicator {
  id: string;
  code: string;
  name: string;
  category: string;
  unit: string;
  description?: string;
  active: boolean;
}

export interface AnalyticsSummary {
  latest_period: string | null;
  previous_period: string | null;
  total_facilities: number;
  reporting_facilities: number;
  reporting_completeness_pct: number;
  totals_by_indicator: Record<string, number>;
  indicator_names: Record<string, string>;
  mom_changes: Record<string, number | null>;
}

export interface MonthlyTrendPoint {
  reporting_month: string;
  observation_date: string;
  total_value: number;
  average_per_facility: number;
  reporting_facilities: number;
  total_facilities: number;
  completeness_pct: number;
  observation_count: number;
}

export interface MonthlyTrendsFilter {
  indicator_code?: string | null;
  state?: string | null;
  district?: string | null;
  facility_id?: string | null;
  start_month?: string | null;
  end_month?: string | null;
}

export interface AnalyticsTrendsResponse {
  filters: MonthlyTrendsFilter;
  total_facilities: number;
  series: MonthlyTrendPoint[];
}

export interface RegionMetricPoint {
  region_name: string;
  level: string;
  reporting_month: string;
  total_facilities: number;
  reporting_facilities: number;
  completeness_pct: number;
  total_utilization: number;
  average_per_reporting_facility: number;
  median_per_reporting_facility: number;
  mom_change_pct: number | null;
}

export interface RegionalAnalyticsResponse {
  level: string;
  reporting_month: string | null;
  indicator_code: string | null;
  regions: RegionMetricPoint[];
}

export interface FacilityLatestMetric {
  indicator_code: string;
  indicator_name: string;
  latest_reporting_month: string;
  latest_value: number | null;
  value_type: string;
  previous_value: number | null;
  mom_change_pct: number | null;
}

export interface FacilityObservationPoint {
  reporting_month: string;
  observation_date: string;
  indicator_code: string;
  indicator_name: string;
  value: number | null;
  value_type: string;
}

export interface FacilityAnalyticsResponse {
  facility_id: string;
  facility_code: string | null;
  facility_name: string;
  facility_type: string;
  state: string;
  district: string;
  sub_district: string | null;
  total_expected_months: number;
  reported_months_count: number;
  completeness_pct: number;
  reporting_completeness_pct?: number;
  missing_months: string[];
  latest_metrics: FacilityLatestMetric[];
  history: FacilityObservationPoint[];
}

export interface DataQualityIssueItem {
  id: string;
  audit_timestamp: string;
  category: string;
  severity: string;
  affected_records: number;
  description: string;
}

export interface IncompleteFacilityItem {
  facility_id: string;
  facility_name: string;
  state: string;
  district: string;
  reported_months: number;
  expected_months: number;
  completeness_pct: number;
}

export interface ObservationBreakdown {
  valid_count: number;
  zero_count: number;
  missing_count: number;
  invalid_count: number;
  imputed_count: number;
  total_observations: number;
}

export interface CompletenessSummary {
  expected_observations: number;
  actual_reported_observations: number;
  completeness_pct: number;
  total_facilities: number;
  reporting_facilities: number;
}

export interface MonthlyQualityPoint {
  reporting_month: string;
  completeness_pct: number;
  reporting_facilities: number;
  total_facilities: number;
  issue_count: number;
  status: string;
}

export interface DataQualityAnalyticsResponse {
  overall_quality_score: number;
  total_issues: number;
  severity_counts: Record<string, number>;
  category_counts: Record<string, number>;
  incomplete_facilities_count: number;
  incomplete_facilities: IncompleteFacilityItem[];
  issues: DataQualityIssueItem[];
  latest_period?: string | null;
  observation_breakdown?: ObservationBreakdown;
  completeness_summary?: CompletenessSummary;
  monthly_timeline?: MonthlyQualityPoint[];
}

export interface HistoricalPoint {
  observation_month: string;
  observation_date: string;
  observed_value: number | null;
  is_missing: boolean;
  is_imputed: boolean;
  status: string | null;
}

export interface CandidateEvaluation {
  model_name: string;
  is_baseline: boolean;
  mae: number;
  rmse: number;
  smape: number;
  wape: number;
}

export interface ForecastPoint {
  forecast_month: string;
  forecast_date: string;
  predicted_value: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResponse {
  status: 'SUCCESS' | 'NOT_ELIGIBLE' | 'ERROR';
  facility: {
    id: string;
    name: string;
    district: string;
    facility_type?: string;
  };
  indicator: {
    id?: string;
    code: string;
    name: string;
    unit?: string;
  };
  forecast_horizon: number;
  model?: {
    model_version: string;
    model_type: string;
    is_baseline: boolean;
  };
  training_period?: {
    start_month: string;
    end_month: string;
    total_observations: number;
  };
  historical_points?: HistoricalPoint[];
  forecast_points: ForecastPoint[];
  prediction_intervals?: {
    interval_type: string;
    residual_std_error: number;
  };
  validation_metrics?: {
    mae: number;
    rmse: number;
    smape: number;
    wape: number;
    mape: number;
  };
  baseline_metrics?: {
    strongest_baseline_name: string;
    strongest_baseline_mae: number;
  };
  candidate_evaluations?: CandidateEvaluation[];
  improvement_over_baseline_pct?: number;
  eligibility: {
    is_eligible: boolean;
    status: string;
    reason_code: string | null;
    reason_message: string;
  };
  data_quality?: {
    reporting_completeness_pct?: number;
    quality_score?: number;
    total_observations?: number;
    missing_count?: number;
  };
  explainability?: {
    model_title: string;
    historical_months_count: number;
    reporting_completeness_pct: string;
    validation_mae: number;
    prediction_interval_description: string;
    baseline_benchmark_model: string;
    improvement_over_baseline: string;
    selection_rationale: string;
  };
  disclaimer: string;
  message?: string;
}

export interface ModelMetrics {
  model_version: string;
  model_type: string;
  target_indicator: string;
  training_start: string;
  training_end: string;
  mae: number | null;
  rmse: number | null;
  mape: number | null;
  baseline_mae: number | null;
  improvement_over_baseline_pct: number | null;
  created_at: string | null;
}

// -------------------------------------------------------------------
// HMIS Data Ingestion & Import Workspace Types (Phase 7G)
// -------------------------------------------------------------------

export type ImportJobStatus =
  | 'QUEUED'
  | 'PROCESSING'
  | 'VALIDATED'
  | 'COMPLETED'
  | 'COMPLETED_WITH_WARNINGS'
  | 'FAILED'
  | 'ROLLED_BACK'
  | 'CANCELLED';

export interface ImportJob {
  id: number;
  job_code: string;
  original_filename: string;
  file_size_bytes: number | null;
  mime_type: string | null;
  file_hash: string | null;
  status: ImportJobStatus | string;
  total_records: number;
  processed_records?: number;
  records_imported: number;
  records_rejected: number;
  quality_score: number | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  claimed_at?: string | null;
  claimed_by?: string | null;
  heartbeat_at?: string | null;
  retry_count?: number;
  max_retries?: number;
  error_summary?: string | null;
  schema_profile?: string | null;
  rolled_back_at?: string | null;
  rolled_back_by?: string | null;
  rollback_reason?: string | null;
  progress_percent?: number | null;
  batch_id?: number | null;
}

export type ImportBatchStatus =
  | 'QUEUED'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'PARTIALLY_FAILED'
  | 'FAILED'
  | 'CANCELLED';

export interface ImportBatch {
  id: number;
  batch_code: string;
  source: string;
  status: ImportBatchStatus | string;
  total_files: number;
  processed_files: number;
  successful_files: number;
  failed_files: number;
  total_records: number;
  imported_records: number;
  rejected_records: number;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  initiated_by?: string | null;
  error_summary?: string | null;
  progress_percent?: number;
}

export interface ImportBatchDetail extends ImportBatch {
  import_jobs: ImportJob[];
}

export interface ImportBatchListResponse {
  total: number;
  items: ImportBatch[];
  page: number;
  page_size: number;
}

export interface DirectoryScanTriggerResponse {
  files_discovered: number;
  jobs_created: number;
  batch_code?: string | null;
  message: string;
}

export interface ImportBatchRetryResponse {
  batch_code: string;
  status: string;
  retried_jobs: number;
  message: string;
}

export interface ImportJobProgressResponse {
  job_code: string;
  status: ImportJobStatus | string;
  total_records: number;
  processed_records: number;
  records_imported: number;
  records_rejected: number;
  progress_percent: number;
  heartbeat_at?: string | null;
  error_summary?: string | null;
  schema_profile?: string | null;
}

export interface ImportJobRetryResponse {
  job_code: string;
  status: string;
  retry_count: number;
  message: string;
}

export interface ImportRollbackResponse {
  job_code: string;
  status: string;
  records_deleted: number;
  records_restored: number;
  records_unchanged: number;
  rolled_back_at: string;
  rolled_back_by?: string | null;
  message: string;
}

export interface ImportJobListResponse {
  total: number;
  items: ImportJob[];
  page: number;
  page_size: number;
}

export interface ImportQualityFinding {
  code: string;
  severity: string;
  message: string;
  row: number | null;
  sheet: string | null;
}

export interface ImportJobQualityResponse {
  job_code: string;
  overall_quality_score: number;
  total_issues: number;
  severity_counts: Record<string, number>;
  category_scores: Record<string, number>;
  findings: ImportQualityFinding[];
}

export interface ImportErrorLog {
  id: number;
  import_job_id: number;
  source_row: number | null;
  source_sheet: string | null;
  error_code: string;
  severity: 'CRITICAL' | 'ERROR' | 'WARNING' | 'INFO' | string;
  message: string;
  created_at: string;
}

export interface ImportErrorLogListResponse {
  total: number;
  items: ImportErrorLog[];
  page: number;
  page_size: number;
}

// District HMIS Analytics Type Definitions (Phases 11D-11G)

export interface DistrictCatalogResponse {
  districts: string[];
  reporting_periods: string[];
  financial_years: string[];
  subgroup_types: string[];
  total_observed_records: number;
  source_name: string;
  geographic_level: string;
  limitations: string[];
}

export interface DistrictIndicatorItem {
  s_no: string;
  parameter_name: string;
  available_subgroups: string[];
  is_stock_metric: boolean;
  is_mapped: boolean;
  canonical_indicator_id: string | null;
  canonical_indicator_name: string | null;
}

export interface DistrictIndicatorCatalogResponse {
  total_indicators: number;
  mapped_count: number;
  unmapped_count: number;
  indicators: DistrictIndicatorItem[];
  limitations_note: string;
}

export interface DistrictTrendObservation {
  id: string;
  reporting_month: string;
  observation_date: string;
  value: number | null;
  value_type: 'VALID' | 'ZERO' | 'MISSING' | 'INVALID' | string;
  subgroup_type: string;
  is_subgroup_total: boolean;
  reported_annual_total: number | null;
  source_file: string;
  source_row: number | null;
  transformation_version: string;
  last_import_job_id: number | null;
}

export interface DistrictMonthlyTrendsResponse {
  district: string;
  s_no: string;
  parameter_name: string;
  subgroup_type: string;
  is_subgroup_total: boolean;
  is_stock_metric: boolean;
  canonical_indicator_id: string | null;
  canonical_indicator_name: string | null;
  annual_total_reported: number | null;
  calculated_sum: number | null;
  valid_months_count: number;
  zero_months_count: number;
  missing_months_count: number;
  total_months_count: number;
  observations: DistrictTrendObservation[];
  limitations: string;
}

export interface DistrictComparisonItem {
  district: string;
  value: number | null;
  value_type: string;
  reported_annual_total: number | null;
  rank: number | null;
}

export interface DistrictComparisonResponse {
  s_no: string;
  parameter_name: string;
  reporting_month: string;
  subgroup_type: string;
  is_subgroup_total: boolean;
  is_stock_metric: boolean;
  total_districts: number;
  reporting_districts: number;
  state_mean: number | null;
  state_median: number | null;
  state_total: number | null;
  items: DistrictComparisonItem[];
  data_note: string;
}

export interface DistrictCoverageItem {
  district: string;
  total_records: number;
  valid_records: number;
  zero_records: number;
  missing_records: number;
  completeness_pct: number;
}

export interface DistrictDataQualitySummaryResponse {
  total_records: number;
  value_counts: Record<string, number>;
  subgroup_totals_count: number;
  subgroup_slices_count: number;
  non_additive_stock_rows: number;
  districts_count: number;
  parameters_count: number;
  import_job: {
    id: number;
    job_code: string;
    original_filename: string;
    status: string;
    total_records: number;
    records_imported: number;
    records_rejected: number;
    completed_at: string | null;
    schema_profile: string;
  } | null;
  district_coverage: DistrictCoverageItem[];
  audit_timestamp: string;
}

// Phase 12A & 12C CSV Export & Multi-Year Parameter Types
export interface DistrictTrendsExportParams {
  district: string;
  s_no: string;
  subgroup_type?: string;
  start_month?: string;
  end_month?: string;
  financial_year?: string;
}

export interface DistrictComparisonExportParams {
  s_no: string;
  reporting_month: string;
  subgroup_type?: string;
  districts?: string[];
  financial_year?: string;
}

// Phase 12B Verified Indicator Registry Types
export interface IndicatorMappingItem {
  s_no: string;
  parameter_name: string;
  canonical_id: string | null;
  canonical_name: string | null;
  category: string | null;
  unit: string | null;
  status: 'VERIFIED' | 'PROVISIONAL' | 'UNMAPPED' | string;
  rationale: string;
  clinical_definition: string | null;
  provenance: string;
  is_stock_metric: boolean;
  reviewed_at: string;
}

export interface IndicatorRegistryResponse {
  total_items: number;
  verified_count: number;
  unmapped_count: number;
  items: IndicatorMappingItem[];
}

export interface IndicatorAuditReportResponse {
  total_parameters_observed: number;
  verified_mappings_count: number;
  ambiguous_mappings_count?: number;
  provisional_mappings_count: number;
  unmapped_parameters_count: number;
  verified_percentage: number;
  unmapped_percentage: number;
  stock_metrics_count: number;
  verified_mappings: IndicatorMappingItem[];
  ambiguous_mappings?: IndicatorMappingItem[];
  unmapped_indicators_sample: string[];
  governance_note: string;
  audit_timestamp: string;
}

// Phase 14: Healthcare Intelligence, Forecasting Readiness & Early-Warning Types
export interface VerifiedIndicatorTimeSeriesPoint {
  month: string;
  date: string;
  value: number | null;
  value_type: string;
  is_zero: boolean;
  is_missing: boolean;
}

export interface VerifiedIndicatorOverviewResponse {
  s_no: string;
  parameter_name: string;
  canonical_id: string;
  canonical_name: string;
  category: string;
  unit: string;
  mapping_status: string;
  provenance: string;
  rationale: string;
  is_stock_metric: boolean;
  temporal_aggregation_permitted: boolean;
  district: string;
  subgroup_type: string;
  financial_year: string;
  total_expected_months: number;
  reported_months_count: number;
  valid_months_count: number;
  zero_months_count: number;
  missing_months_count: number;
  completeness_ratio: number;
  mean_value: number | null;
  median_value: number | null;
  min_value: number | null;
  max_value: number | null;
  std_dev: number | null;
  points: VerifiedIndicatorTimeSeriesPoint[];
  stock_warning: string | null;
  governance_notice: string;
}

export interface BaselineModelEvaluation {
  model_name: string;
  evaluation_metrics: {
    mae: number;
    rmse: number;
    smape: number;
    wape: number;
    mape: number;
  };
  predictions: number[];
  ground_truth: number[];
}

export interface BaselineForecastPoint {
  month: string;
  predicted_value: number;
  lower_bound: number;
  upper_bound: number;
  model_used: string;
}

export interface ForecastingReadinessResponse {
  district: string;
  s_no: string;
  parameter_name: string;
  canonical_id?: string | null;
  canonical_name?: string | null;
  subgroup_type: string;
  financial_year: string;
  requested_horizon: number;
  is_ready: boolean;
  readiness_status: string;
  readiness_reason: string;
  dataset_limitation: string;
  clinical_validation_disclaimer: string;
  historical_months_available: number;
  historical_months_required: number;
  training_period?: {
    start_month: string;
    end_month: string;
    months_count: number;
  } | null;
  evaluation_period?: {
    start_month: string;
    end_month: string;
    months_count: number;
  } | null;
  baseline_models_evaluated: BaselineModelEvaluation[];
  selected_baseline_model?: string | null;
  held_out_metrics?: {
    mae: number;
    rmse: number;
    smape: number;
    wape: number;
    mape: number;
  } | null;
  baseline_forecast: BaselineForecastPoint[];
}

export interface AnomalySignalItem {
  signal_id: string;
  signal_type: 'HISTORICAL_OUTLIER_MAD' | 'MONTH_OVER_MONTH_SHIFT' | 'MISSING_REPORTING_PERIOD' | 'SPATIAL_DEVIATION' | string;
  severity: 'INFO' | 'WARNING' | 'ELEVATED' | string;
  district: string;
  s_no: string;
  parameter_name: string;
  reporting_month: string;
  observed_value: number | null;
  expected_baseline: number | null;
  deviation_score: number;
  metric_unit?: string | null;
  statistical_method: string;
  rationale: string;
  data_points_used: number;
  review_status?: 'OPEN' | 'ACKNOWLEDGED' | 'UNDER_REVIEW' | 'RESOLVED' | 'REOPENED' | string;
  last_reviewed_by_username?: string | null;
  last_reviewed_at?: string | null;
  disclaimer: string;
}

export interface DistrictAnomalyReportResponse {
  s_no?: string | null;
  district?: string | null;
  reporting_month?: string | null;
  financial_year?: string | null;
  total_signals_detected: number;
  signals: AnomalySignalItem[];
  evaluation_summary: {
    districts_evaluated: number;
    indicators_evaluated: number;
    methods_applied: string[];
  };
  governance_disclaimer: string;
}

// -------------------------------------------------------------------
// Phase 15: Source Registry, Comparability, and Anomaly Review Types
// -------------------------------------------------------------------

export interface HMISSourceItem {
  financial_year: string;
  state: string;
  status: 'INGESTED' | 'AVAILABLE_UNINGESTED' | 'BLOCKED_MISSING_OFFICIAL_FILE' | string;
  source_filename: string;
  source_portal: string;
  source_url: string;
  file_format: string;
  total_observations_ingested: number;
  file_sha256?: string | null;
  acquisition_blocker?: string | null;
  ingestion_readiness: string;
}

export interface SourceRegistrySummary {
  state: string;
  total_registered_years: number;
  ingested_years: string[];
  pending_years: string[];
  sources: HMISSourceItem[];
  acquisition_guidelines: string;
}

export interface DistrictBoundaryShift {
  bifurcated_district: string;
  parent_district: string;
  effective_year: string;
  notes: string;
}

export interface IndicatorStabilityCheck {
  s_no: string;
  canonical_id?: string | null;
  audit_status: string;
  parameter_names_by_fy: Record<string, string>;
  subgroups_by_fy: Record<string, string[]>;
  is_stable: boolean;
  drift_notes?: string | null;
}

export interface FinancialYearCoverageDetail {
  financial_year: string;
  total_observations: number;
  distinct_districts_count: number;
  districts: string[];
  distinct_months_count: number;
  reporting_months: string[];
  missing_months: string[];
  coverage_percentage: number;
  confirmed_zero_count: number;
  missing_value_count: number;
  valid_value_count: number;
}

export interface CrossYearComparabilityReport {
  state: string;
  available_financial_years: string[];
  coverage_by_year: FinancialYearCoverageDetail[];
  boundary_shifts_catalog: DistrictBoundaryShift[];
  indicator_stability: IndicatorStabilityCheck[];
  comparability_warnings: string[];
  multi_year_aggregation_permitted: boolean;
  governance_notice: string;
}

export interface DistrictAnomalyReviewActionItem {
  id: number;
  review_id: string;
  action: string;
  from_status: string;
  to_status: string;
  notes?: string | null;
  username: string;
  created_at: string;
}

export interface DistrictAnomalyReviewItem {
  id: string;
  signal_id: string;
  district: string;
  indicator_id: string;
  reporting_month: string;
  signal_type: string;
  severity: string;
  current_status: 'OPEN' | 'ACKNOWLEDGED' | 'UNDER_REVIEW' | 'RESOLVED' | 'REOPENED' | string;
  trigger_reason: string;
  metric_value?: number | null;
  expected_range?: string | null;
  last_reviewed_by_username?: string | null;
  last_reviewed_at?: string | null;
  resolution_reason?: string | null;
  actions: DistrictAnomalyReviewActionItem[];
}

export interface AnomalyReviewActionRequest {
  action: 'ACKNOWLEDGE' | 'SET_UNDER_REVIEW' | 'RESOLVE' | 'REOPEN' | 'ADD_NOTE' | string;
  notes?: string | null;
  district?: string;
  indicator_id?: string;
  reporting_month?: string;
  signal_type?: string;
  trigger_reason?: string;
  metric_value?: number | null;
  expected_range?: string | null;
}
