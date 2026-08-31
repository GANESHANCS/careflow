import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ForecastPage } from './ForecastPage';
import { api } from '../api/client';
import type { ForecastResponse } from '../api/types';

vi.mock('../api/client', () => ({
  api: {
    getFacilities: vi.fn(),
    getIndicators: vi.fn(),
    getForecast: vi.fn(),
  },
}));

describe('ForecastPage Component', () => {
  const mockFacilities = [
    {
      id: 'fac_01',
      facility_code: 'FAC_1001',
      facility_name: 'District Hospital Alpha',
      facility_type: 'DH',
      state: 'State A',
      district: 'District 1',
      sub_district: null,
    },
    {
      id: 'fac_02',
      facility_code: 'FAC_1002',
      facility_name: 'Community Health Centre Beta',
      facility_type: 'CHC',
      state: 'State A',
      district: 'District 2',
      sub_district: null,
    },
  ];

  const mockIndicators = [
    {
      id: 'IND_01',
      code: 'opd_attendance',
      name: 'Outpatient Attendance',
      category: 'Outpatient',
      unit: 'patients',
      active: true,
    },
  ];

  const mockEligibleForecast: ForecastResponse = {
    status: 'SUCCESS',
    facility: {
      id: 'fac_01',
      name: 'District Hospital Alpha',
      district: 'District 1',
      facility_type: 'DH',
    },
    indicator: {
      id: 'IND_01',
      code: 'opd_attendance',
      name: 'Outpatient Attendance',
      unit: 'patients',
    },
    forecast_horizon: 12,
    model: {
      model_version: '1.0.0',
      model_type: 'SARIMAX',
      is_baseline: false,
    },
    training_period: {
      start_month: '2022-01',
      end_month: '2024-12',
      total_observations: 36,
    },
    historical_points: [
      { observation_month: '2024-10', observation_date: '2024-10-01', observed_value: 1200, is_missing: false, is_imputed: false, status: 'VALID' },
      { observation_month: '2024-11', observation_date: '2024-11-01', observed_value: 1350, is_missing: false, is_imputed: false, status: 'VALID' },
      { observation_month: '2024-12', observation_date: '2024-12-01', observed_value: 1400, is_missing: false, is_imputed: false, status: 'VALID' },
    ],
    forecast_points: [
      { forecast_month: '2025-01', forecast_date: '2025-01-01', predicted_value: 1450, lower_bound: 1300, upper_bound: 1600 },
      { forecast_month: '2025-02', forecast_date: '2025-02-01', predicted_value: 1500, lower_bound: 1320, upper_bound: 1680 },
    ],
    prediction_intervals: {
      interval_type: 'Residual Standard Error',
      residual_std_error: 45.2,
    },
    validation_metrics: {
      mae: 35.5,
      rmse: 42.1,
      smape: 0.04,
      wape: 0.035,
      mape: 4.1,
    },
    baseline_metrics: {
      strongest_baseline_name: 'Seasonal Naive',
      strongest_baseline_mae: 55.0,
    },
    candidate_evaluations: [
      { model_name: 'SARIMAX', is_baseline: false, mae: 35.5, rmse: 42.1, smape: 0.04, wape: 0.035 },
      { model_name: 'Seasonal Naive', is_baseline: true, mae: 55.0, rmse: 65.2, smape: 0.06, wape: 0.055 },
      { model_name: 'Naive', is_baseline: true, mae: 70.0, rmse: 82.0, smape: 0.08, wape: 0.075 },
    ],
    improvement_over_baseline_pct: 35.45,
    eligibility: {
      is_eligible: true,
      status: 'ELIGIBLE',
      reason_code: null,
      reason_message: 'Series satisfies minimum 24 months requirement and <30% missingness threshold.',
    },
    explainability: {
      model_title: 'Forecast generated using SARIMAX',
      historical_months_count: 36,
      reporting_completeness_pct: '100.0%',
      validation_mae: 35.5,
      prediction_interval_description: '95% residual prediction interval',
      baseline_benchmark_model: 'Seasonal Naive',
      improvement_over_baseline: '35.5%',
      selection_rationale: "Candidate ML model 'SARIMAX' selected as it outperformed strongest baseline 'Seasonal Naive'.",
    },
    disclaimer: 'SYNTHETIC / NON-REPRESENTATIVE — Validation performed on synthetic fixtures.',
  };

  const mockIneligibleForecast: ForecastResponse = {
    status: 'NOT_ELIGIBLE',
    facility: {
      id: 'fac_02',
      name: 'Community Health Centre Beta',
      district: 'District 2',
    },
    indicator: {
      code: 'opd_attendance',
      name: 'Outpatient Attendance',
    },
    forecast_horizon: 12,
    forecast_points: [],
    historical_points: [
      { observation_month: '2024-10', observation_date: '2024-10-01', observed_value: 500, is_missing: false, is_imputed: false, status: 'VALID' },
      { observation_month: '2024-11', observation_date: '2024-11-01', observed_value: null, is_missing: true, is_imputed: false, status: 'MISSING' },
    ],
    eligibility: {
      is_eligible: false,
      status: 'NOT_ELIGIBLE',
      reason_code: 'INSUFFICIENT_HISTORY',
      reason_message: 'Only 8 valid monthly observations are available. At least 24 are required.',
    },
    data_quality: {
      reporting_completeness_pct: 50.0,
      quality_score: 50.0,
      total_observations: 8,
      missing_count: 4,
    },
    disclaimer: 'SYNTHETIC / NON-REPRESENTATIVE',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (api.getFacilities as any).mockResolvedValue(mockFacilities);
    (api.getIndicators as any).mockResolvedValue(mockIndicators);
    (api.getForecast as any).mockResolvedValue(mockEligibleForecast);
  });

  const renderComponent = (initialPath = '/forecast') => {
    return render(
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/forecast" element={<ForecastPage />} />
        </Routes>
      </MemoryRouter>
    );
  };

  it('renders header, parameters toolbar, and loads forecast for initial facility', async () => {
    renderComponent();

    expect(screen.getByText(/Demand Forecasting & Predictive Capacity/i)).toBeInTheDocument();
    expect(screen.getByText(/CAREFlow \/ Forecast Intelligence Workspace/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(api.getForecast).toHaveBeenCalledWith('fac_01', 'opd_attendance', 12);
    });

    expect(await screen.findByText(/Winning Model: SARIMAX/i)).toBeInTheDocument();
    expect(screen.getByText(/Demand Trajectory & ~95% Prediction Interval/i)).toBeInTheDocument();
  });

  it('handles query parameter facility_id pre-selection', async () => {
    renderComponent('/forecast?facility_id=fac_02');

    await waitFor(() => {
      expect(api.getForecast).toHaveBeenCalledWith('fac_02', 'opd_attendance', 12);
    });
  });

  it('displays ineligible diagnostic state when series fails eligibility criteria', async () => {
    (api.getForecast as any).mockResolvedValue(mockIneligibleForecast);

    renderComponent('/forecast?facility_id=fac_02');

    expect(await screen.findByText(/NOT ELIGIBLE FOR FORECASTING/i)).toBeInTheDocument();
    expect(screen.getByText(/Insufficient Historical Observations/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Only 8 valid monthly observations are available/i)[0]).toBeInTheDocument();
  });

  it('handles forecast horizon selection changes (3M, 6M, 12M)', async () => {
    renderComponent();

    await waitFor(() => {
      expect(api.getForecast).toHaveBeenCalledWith('fac_01', 'opd_attendance', 12);
    });

    const button3M = screen.getByRole('button', { name: /Select 3 months forecast horizon/i });
    fireEvent.click(button3M);

    await waitFor(() => {
      expect(api.getForecast).toHaveBeenCalledWith('fac_01', 'opd_attendance', 3);
    });
  });

  it('renders candidate model tournament benchmark table and selection rationale', async () => {
    renderComponent();

    expect(await screen.findByText(/Candidate Model Tournament Benchmark/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Seasonal Naive/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Selection Rationale/i)).toBeInTheDocument();
  });

  it('handles API error state and provides retry button', async () => {
    (api.getForecast as any).mockRejectedValue(new Error('Network API connection failed'));

    renderComponent();

    expect(await screen.findByText(/Unable to Load Forecast Model/i)).toBeInTheDocument();
    expect(screen.getByText(/Network API connection failed/i)).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /Retry Model Query/i });
    expect(retryBtn).toBeInTheDocument();
  });

  it('expands methodology panel when clicked', async () => {
    renderComponent();

    const methodologyBtn = await screen.findByRole('button', { name: /Phase 5 Forecasting Architecture & ML Methodology/i });
    fireEvent.click(methodologyBtn);

    expect(await screen.findByText(/1. Data Integrity & Missingness Handling/i)).toBeInTheDocument();
    expect(screen.getByText(/2. Eligibility Guardrails/i)).toBeInTheDocument();
  });
});
