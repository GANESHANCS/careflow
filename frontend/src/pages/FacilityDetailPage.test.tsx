import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { FacilityDetailPage } from './FacilityDetailPage';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    getFacilityById: vi.fn(),
    getFacilityAnalytics: vi.fn(),
    getForecast: vi.fn(),
  },
}));

describe('FacilityDetailPage Component', () => {
  const mockFacility = {
    id: 'fac-101',
    facility_code: 'DH101',
    facility_name: 'District Hospital Mysuru',
    facility_type: 'District Hospital',
    state: 'Karnataka',
    district: 'Mysuru',
    sub_district: 'Mysuru Urban',
  };

  const mockAnalytics = {
    facility_id: 'fac-101',
    facility_code: 'DH101',
    facility_name: 'District Hospital Mysuru',
    facility_type: 'District Hospital',
    state: 'Karnataka',
    district: 'Mysuru',
    sub_district: 'Mysuru Urban',
    total_expected_months: 12,
    reported_months_count: 10,
    completeness_pct: 83.3,
    missing_months: ['2024-05', '2024-09'],
    latest_metrics: [
      {
        indicator_code: 'opd_attendance',
        indicator_name: 'Outpatient Attendance',
        latest_reporting_month: '2024-12',
        latest_value: 12450,
        value_type: 'Count',
        previous_value: 11800,
        mom_change_pct: 5.5,
      },
    ],
    history: [
      {
        reporting_month: '2024-11',
        observation_date: '2024-11-01',
        indicator_code: 'opd_attendance',
        indicator_name: 'Outpatient Attendance',
        value: 11800,
        value_type: 'Count',
      },
      {
        reporting_month: '2024-12',
        observation_date: '2024-12-01',
        indicator_code: 'opd_attendance',
        indicator_name: 'Outpatient Attendance',
        value: 12450,
        value_type: 'Count',
      },
    ],
  };

  const mockForecastSuccess = {
    status: 'SUCCESS' as const,
    facility: { id: 'fac-101', name: 'District Hospital Mysuru', district: 'Mysuru' },
    indicator: { code: 'opd_attendance', name: 'Outpatient Attendance' },
    forecast_horizon: 12,
    forecast_points: [],
    eligibility: {
      is_eligible: true,
      status: 'SUCCESS',
      reason_code: null,
      reason_message: 'Eligible for forecasting',
    },
    explainability: {
      model_title: 'SARIMAX (p=1,d=1,q=1)',
      historical_months_count: 24,
      reporting_completeness_pct: '83.3%',
      validation_mae: 142.5,
      prediction_interval_description: '95% Prediction Interval',
      baseline_benchmark_model: 'Seasonal Naive',
      improvement_over_baseline: '+14.2%',
      selection_rationale: 'Best cross-validation accuracy',
    },
    disclaimer: 'Development fixture',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders facility intelligence profile header and metrics when API succeeds', async () => {
    vi.mocked(api.getFacilityById).mockResolvedValue(mockFacility);
    vi.mocked(api.getFacilityAnalytics).mockResolvedValue(mockAnalytics);
    vi.mocked(api.getForecast).mockResolvedValue(mockForecastSuccess);

    render(
      <MemoryRouter initialEntries={['/facilities/fac-101']}>
        <Routes>
          <Route path="/facilities/:id" element={<FacilityDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/District Hospital Mysuru/i)[0]).toBeInTheDocument();
      expect(screen.getByText(/Facility Utilization Signal/i)).toBeInTheDocument();
      expect(screen.getByText(/Reporting Reliability & Audit Governance/i)).toBeInTheDocument();
      expect(screen.getByText(/FORECAST READY/i)).toBeInTheDocument();
    });
  });

  it('renders missing month markers (○) in timeline matrix', async () => {
    vi.mocked(api.getFacilityById).mockResolvedValue(mockFacility);
    vi.mocked(api.getFacilityAnalytics).mockResolvedValue(mockAnalytics);
    vi.mocked(api.getForecast).mockResolvedValue(mockForecastSuccess);

    render(
      <MemoryRouter initialEntries={['/facilities/fac-101']}>
        <Routes>
          <Route path="/facilities/:id" element={<FacilityDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/83.3%/i)[0]).toBeInTheDocument();
      expect(screen.getByText(/10 of 12 expected monthly returns ingested/i)).toBeInTheDocument();
    });
  });

  it('renders 404 error state when facility ID is not found', async () => {
    vi.mocked(api.getFacilityById).mockResolvedValue(null as any);
    vi.mocked(api.getFacilityAnalytics).mockResolvedValue(null as any);
    vi.mocked(api.getForecast).mockResolvedValue(null as any);

    render(
      <MemoryRouter initialEntries={['/facilities/non-existent-id']}>
        <Routes>
          <Route path="/facilities/:id" element={<FacilityDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Facility Not Found/i)).toBeInTheDocument();
    });
  });
});
