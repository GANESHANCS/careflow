import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { OverviewPage } from './OverviewPage';
import { api } from '../api/client';

// Mock the API client
vi.mock('../api/client', () => ({
  api: {
    getAnalyticsSummary: vi.fn(),
    getAnalyticsTrends: vi.fn(),
    getRegionalAnalytics: vi.fn(),
    getDataQualityAnalytics: vi.fn(),
    getIndicators: vi.fn(),
  },
}));

describe('OverviewPage Component', () => {
  const mockSummaryEmpty = {
    latest_period: null,
    previous_period: null,
    total_facilities: 0,
    reporting_facilities: 0,
    reporting_completeness_pct: 0,
    totals_by_indicator: {},
    indicator_names: {},
    mom_changes: {},
  };

  const mockSummaryData = {
    latest_period: '2025-12',
    previous_period: '2025-11',
    total_facilities: 120,
    reporting_facilities: 100,
    reporting_completeness_pct: 83.3,
    totals_by_indicator: {
      opd_attendance: 1284392,
      ipd_admissions: 45210,
    },
    indicator_names: {
      opd_attendance: 'Outpatient Attendance',
      ipd_admissions: 'Inpatient Admissions',
    },
    mom_changes: {
      opd_attendance: 7.2,
      ipd_admissions: -2.1,
    },
  };

  const mockTrendsData = {
    filters: { indicator_code: 'opd_attendance' },
    total_facilities: 120,
    series: [
      {
        reporting_month: '2025-11',
        observation_date: '2025-11-01',
        total_value: 1198000,
        average_per_facility: 9983.3,
        reporting_facilities: 98,
        total_facilities: 120,
        completeness_pct: 81.6,
        observation_count: 98,
      },
      {
        reporting_month: '2025-12',
        observation_date: '2025-12-01',
        total_value: 1284392,
        average_per_facility: 10703.2,
        reporting_facilities: 100,
        total_facilities: 120,
        completeness_pct: 83.3,
        observation_count: 100,
      },
    ],
  };

  const mockRegionalData = {
    level: 'state',
    reporting_month: '2025-12',
    indicator_code: 'opd_attendance',
    regions: [
      {
        region_name: 'Karnataka',
        level: 'state',
        reporting_month: '2025-12',
        total_facilities: 80,
        reporting_facilities: 75,
        completeness_pct: 93.75,
        total_utilization: 850000,
        average_per_reporting_facility: 11333.3,
        median_per_reporting_facility: 10500,
        mom_change_pct: 4.5,
      },
    ],
  };

  const mockQualityData = {
    overall_quality_score: 91.5,
    total_issues: 2,
    severity_counts: { CRITICAL: 0, WARNING: 2, INFO: 0 },
    category_counts: { MISSING: 2 },
    incomplete_facilities_count: 1,
    incomplete_facilities: [
      {
        facility_id: 'fac-101',
        facility_name: 'District Hospital Mysuru',
        state: 'Karnataka',
        district: 'Mysuru',
        reported_months: 10,
        expected_months: 12,
        completeness_pct: 83.3,
      },
    ],
    issues: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getIndicators).mockResolvedValue([
      { id: '1', code: 'opd_attendance', name: 'Outpatient Attendance', category: 'OPD', unit: 'Count', active: true },
    ]);
  });

  it('renders empty state when backend returns 0 observations', async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockSummaryEmpty);
    vi.mocked(api.getAnalyticsTrends).mockResolvedValue({ filters: {}, total_facilities: 0, series: [] });
    vi.mocked(api.getRegionalAnalytics).mockResolvedValue({ level: 'state', reporting_month: null, indicator_code: null, regions: [] });
    vi.mocked(api.getDataQualityAnalytics).mockResolvedValue({
      overall_quality_score: 100,
      total_issues: 0,
      severity_counts: {},
      category_counts: {},
      incomplete_facilities_count: 0,
      incomplete_facilities: [],
      issues: [],
    });

    render(
      <BrowserRouter>
        <OverviewPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/HMIS Data Awaiting Ingestion/i)).toBeInTheDocument();
      expect(screen.getByText(/AWAITING HMIS INGESTION/i)).toBeInTheDocument();
    });
  });

  it('renders operational dashboard successfully when HMIS data exists', async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockSummaryData);
    vi.mocked(api.getAnalyticsTrends).mockResolvedValue(mockTrendsData);
    vi.mocked(api.getRegionalAnalytics).mockResolvedValue(mockRegionalData);
    vi.mocked(api.getDataQualityAnalytics).mockResolvedValue(mockQualityData);

    render(
      <BrowserRouter>
        <OverviewPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/SYSTEM ONLINE/i)).toBeInTheDocument();
      expect(screen.getByText(/Karnataka/i)).toBeInTheDocument();
      expect(screen.getByText(/Overall Quality Score/i)).toBeInTheDocument();
    });
  });

  it('renders error state and handles retry button', async () => {
    vi.mocked(api.getAnalyticsSummary).mockRejectedValue(new Error('Backend Connection Failed'));
    vi.mocked(api.getAnalyticsTrends).mockRejectedValue(new Error('Backend Connection Failed'));
    vi.mocked(api.getRegionalAnalytics).mockRejectedValue(new Error('Backend Connection Failed'));
    vi.mocked(api.getDataQualityAnalytics).mockRejectedValue(new Error('Backend Connection Failed'));

    render(
      <BrowserRouter>
        <OverviewPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Backend Connection Failed/i)).toBeInTheDocument();
    });

    const retryBtn = screen.getByRole('button', { name: /try again/i });
    expect(retryBtn).toBeInTheDocument();

    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockSummaryData);
    vi.mocked(api.getAnalyticsTrends).mockResolvedValue(mockTrendsData);
    vi.mocked(api.getRegionalAnalytics).mockResolvedValue(mockRegionalData);
    vi.mocked(api.getDataQualityAnalytics).mockResolvedValue(mockQualityData);

    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(screen.getByText(/SYSTEM ONLINE/i)).toBeInTheDocument();
    });
  });

  it('handles state vs district regional toggle', async () => {
    vi.mocked(api.getAnalyticsSummary).mockResolvedValue(mockSummaryData);
    vi.mocked(api.getAnalyticsTrends).mockResolvedValue(mockTrendsData);
    vi.mocked(api.getRegionalAnalytics).mockResolvedValue(mockRegionalData);
    vi.mocked(api.getDataQualityAnalytics).mockResolvedValue(mockQualityData);

    render(
      <BrowserRouter>
        <OverviewPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /view district-level aggregations/i })).toBeInTheDocument();
    });

    const districtBtn = screen.getByRole('button', { name: /view district-level aggregations/i });
    fireEvent.click(districtBtn);

    expect(api.getRegionalAnalytics).toHaveBeenCalledWith(expect.objectContaining({ level: 'district' }));
  });
});
