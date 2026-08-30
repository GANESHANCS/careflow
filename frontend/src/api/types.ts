// API Type Definitions for CAREFlow Backend Service

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
  total_facilities: number;
  active_facilities: number;
  total_indicators: number;
  latest_month: string | null;
  total_observations: number;
  overall_reporting_completeness_pct: number;
}

export interface MonthlyTrendPoint {
  reporting_month: string;
  observation_date: string;
  total_value: number;
  average_value: number;
  reporting_facilities: number;
  completeness_pct: number;
}

export interface AnalyticsTrendsResponse {
  indicator_code: string;
  total_months: number;
  trends: MonthlyTrendPoint[];
}

export interface RegionalMetric {
  region_name: string;
  state: string;
  district: string | null;
  total_utilization: number;
  average_per_facility: number;
  median_per_facility: number;
  reporting_facilities_count: number;
  mom_growth_pct: number | null;
}

export interface RegionalAnalyticsResponse {
  aggregation_level: 'state' | 'district';
  indicator_code: string;
  reporting_month: string | null;
  regions: RegionalMetric[];
}

export interface FacilityAnalyticsResponse {
  facility: Facility;
  reporting_completeness_pct: number;
  missing_months_count: number;
  indicators_tracked: number;
  recent_trends: Record<string, MonthlyTrendPoint[]>;
}

export interface DataQualityAnalyticsResponse {
  total_observations: number;
  valid_count: number;
  missing_count: number;
  zero_count: number;
  invalid_count: number;
  imputed_count: number;
  overall_quality_score: number;
  completeness_rate_pct: number;
  critical_issues_count: number;
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
  improvement_over_baseline_pct?: number;
  eligibility: {
    is_eligible: boolean;
    status: string;
    reason_code: string | null;
    reason_message: string;
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
