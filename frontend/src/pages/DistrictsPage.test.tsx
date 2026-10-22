import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { DistrictsPage } from './DistrictsPage';
import { api } from '../api/client';
import type {
  DistrictCatalogResponse,
  DistrictIndicatorCatalogResponse,
  DistrictMonthlyTrendsResponse,
  DistrictComparisonResponse,
  DistrictDataQualitySummaryResponse,
  IndicatorAuditReportResponse,
} from '../api/types';

vi.mock('../api/client', () => ({
  api: {
    getDistrictCatalog: vi.fn(),
    getDistrictIndicators: vi.fn(),
    getDistrictMonthlyTrends: vi.fn(),
    getDistrictComparison: vi.fn(),
    getDistrictQuality: vi.fn(),
    getIndicatorAudit: vi.fn(),
    getIndicatorRegistry: vi.fn(),
    downloadDistrictTrendsCsv: vi.fn(),
    downloadDistrictComparisonCsv: vi.fn(),
    getDistrictIntelligenceOverview: vi.fn(),
    getDistrictForecastingReadiness: vi.fn(),
    getDistrictAnomalies: vi.fn(),
  },
}));

describe('DistrictsPage Component (Phases 11E–12E)', () => {
  const mockCatalog: DistrictCatalogResponse = {
    districts: ['Ariyalur', 'Chennai', 'Coimbatore'],
    reporting_periods: [
      '2015-04',
      '2015-05',
      '2015-06',
      '2015-07',
      '2015-08',
      '2015-09',
      '2015-10',
      '2015-11',
      '2015-12',
      '2016-01',
      '2016-02',
      '2016-03',
    ],
    financial_years: ['2015-16'],
    subgroup_types: ['Rural', 'Urban', 'Total'],
    total_observed_records: 175872,
    source_name: 'Tamil Nadu State HMIS FY 2015-16',
    geographic_level: 'District',
    limitations: ['Official administrative returns', 'Separated from facility observations'],
  };

  const mockIndicators: DistrictIndicatorCatalogResponse = {
    total_indicators: 2,
    mapped_count: 1,
    unmapped_count: 1,
    limitations_note: 'Official indicators',
    indicators: [
      {
        s_no: '1.1',
        parameter_name: 'Total number of pregnant women registered for ANC',
        available_subgroups: ['Total'],
        is_stock_metric: false,
        is_mapped: true,
        canonical_indicator_id: 'anc_registration_total',
        canonical_indicator_name: 'ANC Registration Total',
      },
      {
        s_no: '2.1',
        parameter_name: 'Number of Institutional Deliveries conducted',
        available_subgroups: ['Rural', 'Urban'],
        is_stock_metric: false,
        is_mapped: false,
        canonical_indicator_id: null,
        canonical_indicator_name: null,
      },
    ],
  };

  const mockTrends: DistrictMonthlyTrendsResponse = {
    district: 'Ariyalur',
    s_no: '1.1',
    parameter_name: 'Total number of pregnant women registered for ANC',
    subgroup_type: 'Total',
    is_subgroup_total: true,
    is_stock_metric: false,
    canonical_indicator_id: 'anc_registration_total',
    canonical_indicator_name: 'ANC Registration Total',
    annual_total_reported: 12000,
    calculated_sum: 12000,
    valid_months_count: 1,
    zero_months_count: 1,
    missing_months_count: 1,
    total_months_count: 3,
    limitations: 'Monthly values represent discrete reporting periods.',
    observations: [
      {
        id: 'obs-1',
        reporting_month: '2015-04',
        observation_date: '2015-04-01',
        value: 1000,
        value_type: 'VALID',
        subgroup_type: 'Total',
        is_subgroup_total: true,
        reported_annual_total: 12000,
        source_file: 'hmis-item-rpt-tn-for-2015-16.csv',
        source_row: 42,
        transformation_version: 'v1.0',
        last_import_job_id: 3,
      },
      {
        id: 'obs-2',
        reporting_month: '2015-05',
        observation_date: '2015-05-01',
        value: 0,
        value_type: 'ZERO',
        subgroup_type: 'Total',
        is_subgroup_total: true,
        reported_annual_total: 12000,
        source_file: 'hmis-item-rpt-tn-for-2015-16.csv',
        source_row: 42,
        transformation_version: 'v1.0',
        last_import_job_id: 3,
      },
      {
        id: 'obs-3',
        reporting_month: '2015-06',
        observation_date: '2015-06-01',
        value: null,
        value_type: 'MISSING',
        subgroup_type: 'Total',
        is_subgroup_total: true,
        reported_annual_total: 12000,
        source_file: 'hmis-item-rpt-tn-for-2015-16.csv',
        source_row: 42,
        transformation_version: 'v1.0',
        last_import_job_id: 3,
      },
    ],
  };

  const mockComparison: DistrictComparisonResponse = {
    s_no: '1.1',
    parameter_name: 'Total number of pregnant women registered for ANC',
    reporting_month: '2015-04',
    subgroup_type: 'Total',
    is_subgroup_total: true,
    is_stock_metric: false,
    total_districts: 3,
    reporting_districts: 2,
    state_mean: 1500,
    state_median: 1200,
    state_total: 3500,
    data_note: 'Comparisons represent discrete reporting activity.',
    items: [
      { district: 'Ariyalur', value: 1000, value_type: 'VALID', reported_annual_total: 12000, rank: 2 },
      { district: 'Chennai', value: 2500, value_type: 'VALID', reported_annual_total: 30000, rank: 1 },
      { district: 'Coimbatore', value: null, value_type: 'MISSING', reported_annual_total: null, rank: null },
    ],
  };

  const mockQuality: DistrictDataQualitySummaryResponse = {
    total_records: 175872,
    value_counts: {
      VALID: 140000,
      ZERO: 25000,
      MISSING: 10872,
    },
    subgroup_totals_count: 50000,
    subgroup_slices_count: 125872,
    non_additive_stock_rows: 1200,
    districts_count: 31,
    parameters_count: 150,
    import_job: {
      id: 3,
      job_code: 'JOB_20261021_124025_eb4fc9',
      original_filename: 'data/raw/hmis_public_source/hmis-item-rpt-tn-for-2015-16.csv',
      status: 'COMPLETED',
      total_records: 14656,
      records_imported: 14656,
      records_rejected: 0,
      completed_at: '2026-10-21T12:40:48Z',
      schema_profile: 'district_monthly_tabular_v1',
    },
    district_coverage: [
      {
        district: 'Ariyalur',
        total_records: 5673,
        valid_records: 5000,
        zero_records: 500,
        missing_records: 173,
        completeness_pct: 96.95,
      },
    ],
    audit_timestamp: '2026-10-21T12:41:00Z',
  };

  const mockAuditReport: IndicatorAuditReportResponse = {
    total_parameters_observed: 261,
    verified_mappings_count: 8,
    provisional_mappings_count: 0,
    unmapped_parameters_count: 253,
    verified_percentage: 3.07,
    unmapped_percentage: 96.93,
    stock_metrics_count: 8,
    verified_mappings: [
      {
        s_no: '1.1',
        parameter_name: 'Total number of pregnant women registered for ANC',
        canonical_id: 'IND_antenatal_visits',
        canonical_name: 'Antenatal Care (ANC) Registered Visits',
        category: 'Maternal Health',
        unit: 'visits',
        status: 'VERIFIED',
        rationale: 'Direct clinical equivalent to MoHFW HMIS Item 1.1',
        clinical_definition: 'Count of pregnant women registered for ANC',
        provenance: 'MoHFW HMIS Operational Guidelines',
        is_stock_metric: false,
        reviewed_at: '2026-10-21T00:00:00Z',
      },
    ],
    unmapped_indicators_sample: ['1.2', '1.3'],
    governance_note: 'Strict non-fabrication rule enforced.',
    audit_timestamp: '2026-10-21T12:41:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getDistrictCatalog).mockResolvedValue(mockCatalog);
    vi.mocked(api.getDistrictIndicators).mockResolvedValue(mockIndicators);
    vi.mocked(api.getDistrictMonthlyTrends).mockResolvedValue(mockTrends);
    vi.mocked(api.getDistrictComparison).mockResolvedValue(mockComparison);
    vi.mocked(api.getDistrictQuality).mockResolvedValue(mockQuality);
    vi.mocked(api.getIndicatorAudit).mockResolvedValue(mockAuditReport);
    vi.mocked(api.downloadDistrictTrendsCsv).mockResolvedValue(undefined);
    vi.mocked(api.downloadDistrictComparisonCsv).mockResolvedValue(undefined);
  });

  it('renders district workspace header with official data separation callout', async () => {
    render(
      <BrowserRouter>
        <DistrictsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/District Healthcare Analytics & Provenance/i)).toBeInTheDocument();
      expect(screen.getByText(/Official State HMIS Returns/i)).toBeInTheDocument();
      expect(screen.getByText(/Data Architecture Separation/i)).toBeInTheDocument();
      expect(screen.getByText(/Ariyalur District/i)).toBeInTheDocument();
    });
  });

  it('populates filter dropdowns with catalog districts, indicators, FY, and periods', async () => {
    render(
      <BrowserRouter>
        <DistrictsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByLabelText(/Select district/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Select financial year/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Select HMIS Indicator/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Select comparison reporting period/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/Select subgroup slice/i)).toBeInTheDocument();
    });
  });

  it('renders monthly trend chart with zero vs missing indicators and CSV export button', async () => {
    render(
      <BrowserRouter>
        <DistrictsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/12-Month Time-Series Movement/i)).toBeInTheDocument();
      expect(screen.getByText(/Valid: 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Zero: 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Missing: 1/i)).toBeInTheDocument();
    });

    const exportBtn = screen.getByRole('button', { name: /Export CSV/i });
    expect(exportBtn).toBeInTheDocument();
    fireEvent.click(exportBtn);

    expect(api.downloadDistrictTrendsCsv).toHaveBeenCalledWith({
      district: 'Ariyalur',
      s_no: '1.1',
      subgroup_type: undefined,
      financial_year: '2015-16',
    });
  });

  it('switches to District Comparison tab, renders comparison, and triggers CSV export', async () => {
    render(
      <BrowserRouter>
        <DistrictsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Monthly Trends/i)).toBeInTheDocument();
    });

    const compareTab = screen.getByRole('button', { name: /District Comparison/i });
    fireEvent.click(compareTab);

    await waitFor(() => {
      expect(screen.getByText(/Cross-District Comparison — 2015-04/i)).toBeInTheDocument();
      expect(screen.getByText(/Districts Reporting/i)).toBeInTheDocument();
      expect(screen.getByText(/District Mean/i)).toBeInTheDocument();
      expect(screen.getAllByText('Chennai').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Coimbatore').length).toBeGreaterThan(0);
    });

    const exportBtn = screen.getByRole('button', { name: /Export CSV/i });
    fireEvent.click(exportBtn);

    expect(api.downloadDistrictComparisonCsv).toHaveBeenCalledWith({
      s_no: '1.1',
      reporting_month: '2015-04',
      subgroup_type: undefined,
      financial_year: '2015-16',
    });
  });

  it('switches to Observation Records tab and renders raw observation records with export action', async () => {
    render(
      <BrowserRouter>
        <DistrictsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Observation Records/i)).toBeInTheDocument();
    });

    const tableTab = screen.getByRole('button', { name: /Observation Records/i });
    fireEvent.click(tableTab);

    await waitFor(() => {
      expect(screen.getByText(/Raw Observation Record Log/i)).toBeInTheDocument();
      expect(screen.getAllByText('2015-04').length).toBeGreaterThan(0);
      expect(screen.getAllByText('2015-05').length).toBeGreaterThan(0);
      expect(screen.getByText(/Zero Activity \(0\)/i)).toBeInTheDocument();
      expect(screen.getByText(/Missing \/ Absent/i)).toBeInTheDocument();
    });

    const exportBtn = screen.getByRole('button', { name: /Export CSV/i });
    expect(exportBtn).toBeInTheDocument();
    fireEvent.click(exportBtn);

    expect(api.downloadDistrictTrendsCsv).toHaveBeenCalled();
  });

  it('switches to Quality & Provenance tab and displays Phase 11F & 12B verified registry audit', async () => {
    render(
      <BrowserRouter>
        <DistrictsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Quality & Provenance/i)).toBeInTheDocument();
    });

    const qualityTab = screen.getByRole('button', { name: /Quality & Provenance/i });
    fireEvent.click(qualityTab);

    await waitFor(() => {
      expect(screen.getByText(/Total Ingested Records/i)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getAllByText(/Confirmed Zero Events/i).length).toBeGreaterThan(0);
    });
    await waitFor(() => {
      expect(screen.getByText(/Phase 12B Verified Indicator Registry & Governance Audit/i)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/Strict Non-Fabrication Rule:/i)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(screen.getByText(/Formula Injection Protection/i)).toBeInTheDocument();
    });
  });

  it('renders error state if the catalog API call fails', async () => {
    vi.mocked(api.getDistrictCatalog).mockRejectedValue(new Error('Connection Refused to District Service'));

    render(
      <BrowserRouter>
        <DistrictsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/District Analytics Catalog Offline/i)).toBeInTheDocument();
      expect(screen.getByText(/Connection Refused to District Service/i)).toBeInTheDocument();
    });
  });

  it('switches to Intelligence & Early Warning tab and renders readiness and anomalies', async () => {
    vi.mocked(api.getDistrictIntelligenceOverview).mockResolvedValue({
      s_no: '1.1',
      parameter_name: 'Total number of pregnant women registered for ANC',
      canonical_id: 'IND_antenatal_visits',
      canonical_name: 'Antenatal Care (ANC) Registered Visits',
      category: 'Maternal Health',
      unit: 'visits',
      mapping_status: 'VERIFIED',
      provenance: 'MoHFW HMIS Operational Guidelines',
      rationale: 'Direct clinical equivalent',
      is_stock_metric: false,
      temporal_aggregation_permitted: true,
      district: 'Ariyalur',
      subgroup_type: 'Total',
      financial_year: '2015-16',
      total_expected_months: 12,
      reported_months_count: 12,
      valid_months_count: 12,
      zero_months_count: 0,
      missing_months_count: 0,
      completeness_ratio: 1.0,
      mean_value: 1000.0,
      median_value: 1000.0,
      min_value: 950.0,
      max_value: 1050.0,
      std_dev: 30.0,
      points: [
        { month: '2015-04', date: '2015-04-01', value: 1000.0, value_type: 'VALID', is_zero: false, is_missing: false }
      ],
      stock_warning: null,
      governance_notice: 'Canonical healthcare metrics'
    });

    vi.mocked(api.getDistrictForecastingReadiness).mockResolvedValue({
      district: 'Ariyalur',
      s_no: '1.1',
      parameter_name: 'ANC registrations',
      canonical_id: 'IND_antenatal_visits',
      canonical_name: 'Antenatal Care (ANC) Registered Visits',
      subgroup_type: 'Total',
      financial_year: '2015-16',
      requested_horizon: 3,
      is_ready: true,
      readiness_status: 'ELIGIBLE_FOR_BASELINE_EVALUATION',
      readiness_reason: 'Evaluated on chronological hold-out',
      dataset_limitation: 'Single-year HMIS dataset (12 months)',
      clinical_validation_disclaimer: 'Statistical baseline models are not clinically validated',
      historical_months_available: 12,
      historical_months_required: 9,
      training_period: { start_month: '2015-04', end_month: '2015-12', months_count: 9 },
      evaluation_period: { start_month: '2016-01', end_month: '2016-03', months_count: 3 },
      baseline_models_evaluated: [
        {
          model_name: 'Naive Forecaster',
          evaluation_metrics: { mae: 15.0, rmse: 18.0, smape: 1.5, wape: 1.5, mape: 1.5 },
          predictions: [1000.0, 1000.0, 1000.0],
          ground_truth: [1010.0, 990.0, 1020.0]
        }
      ],
      selected_baseline_model: 'Naive Forecaster',
      held_out_metrics: { mae: 15.0, rmse: 18.0, smape: 1.5, wape: 1.5, mape: 1.5 },
      baseline_forecast: [
        { month: '2016-04', predicted_value: 1000.0, lower_bound: 964.7, upper_bound: 1035.3, model_used: 'Naive Forecaster' }
      ]
    });

    vi.mocked(api.getDistrictAnomalies).mockResolvedValue({
      total_signals_detected: 1,
      signals: [
        {
          signal_id: 'SIG_MAD_1',
          signal_type: 'HISTORICAL_OUTLIER_MAD',
          severity: 'WARNING',
          district: 'Ariyalur',
          s_no: '1.1',
          parameter_name: 'ANC Registration',
          reporting_month: '2016-03',
          observed_value: 4500.0,
          expected_baseline: 1000.0,
          deviation_score: 4.2,
          metric_unit: 'visits',
          statistical_method: 'Median Absolute Deviation',
          rationale: 'Observed value is 4.2x MAD above median',
          data_points_used: 12,
          disclaimer: 'STATISTICAL_SIGNAL — Requires HMIS review'
        }
      ],
      evaluation_summary: {
        districts_evaluated: 1,
        indicators_evaluated: 1,
        methods_applied: ['MAD']
      },
      governance_disclaimer: 'Statistical anomaly detection disclaimer'
    });

    render(
      <BrowserRouter>
        <DistrictsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Intelligence & Early Warning/i)).toBeInTheDocument();
    });

    const intelTab = screen.getByRole('button', { name: /Intelligence & Early Warning/i });
    fireEvent.click(intelTab);

    await waitFor(() => {
      expect(screen.getByText(/Eligible for Baseline Evaluation/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Single-Year Dataset Limitation/i)).toBeInTheDocument();
    expect(screen.getByText(/Statistical Anomaly & Operational Change Signals/i)).toBeInTheDocument();
    expect(screen.getByText(/HISTORICAL OUTLIER MAD/i)).toBeInTheDocument();
  });
});
