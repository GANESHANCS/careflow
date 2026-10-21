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
