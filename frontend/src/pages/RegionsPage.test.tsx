import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { RegionsPage } from './RegionsPage';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    getRegionalAnalytics: vi.fn(),
    getAnalyticsTrends: vi.fn(),
    getIndicators: vi.fn(),
    getFacilities: vi.fn(),
  },
}));

describe('RegionsPage Component', () => {
  const mockRegionalData = {
    level: 'state',
    reporting_month: '2024-12',
    indicator_code: 'opd_attendance',
    regions: [
      {
        region_name: 'Karnataka',
        level: 'state',
        reporting_month: '2024-12',
        total_facilities: 50,
        reporting_facilities: 45,
        completeness_pct: 90.0,
        total_utilization: 125000,
        average_per_reporting_facility: 2777.78,
        median_per_reporting_facility: 2500.0,
        mom_change_pct: 4.5,
      },
      {
        region_name: 'Maharashtra',
        level: 'state',
        reporting_month: '2024-12',
        total_facilities: 80,
        reporting_facilities: 60,
        completeness_pct: 75.0,
        total_utilization: 180000,
        average_per_reporting_facility: 3000.0,
        median_per_reporting_facility: 2800.0,
        mom_change_pct: -2.1,
      },
    ],
  };

  const mockTrendsData = {
    filters: {
      indicator_code: 'opd_attendance',
      state: undefined,
      district: undefined,
      facility_id: undefined,
      start_month: undefined,
      end_month: undefined,
    },
    total_facilities: 130,
    series: [
      {
        reporting_month: '2024-11',
        observation_date: '2024-11-01',
        indicator_code: 'opd_attendance',
        total_value: 290000,
        average_per_facility: 2800,
        reporting_facilities: 100,
        total_facilities: 130,
        completeness_pct: 76.9,
        observation_count: 100,
      },
      {
        reporting_month: '2024-12',
        observation_date: '2024-12-01',
        indicator_code: 'opd_attendance',
        total_value: 305000,
        average_per_facility: 2900,
        reporting_facilities: 105,
        total_facilities: 130,
        completeness_pct: 80.8,
        observation_count: 105,
      },
    ],
  };

  const mockIndicators = [
    { id: 'ind-1', code: 'opd_attendance', name: 'Outpatient Attendance', category: 'utilization', unit: 'Count', active: true },
    { id: 'ind-2', code: 'ipd_admissions', name: 'Inpatient Admissions', category: 'utilization', unit: 'Count', active: true },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getIndicators).mockResolvedValue(mockIndicators);
    vi.mocked(api.getFacilities).mockResolvedValue({ items: [], total: 0, skip: 0, limit: 100 });
  });

  it('renders regional workspace header, hero signal, and spatial ranking list', async () => {
    vi.mocked(api.getRegionalAnalytics).mockResolvedValue(mockRegionalData);
    vi.mocked(api.getAnalyticsTrends).mockResolvedValue(mockTrendsData);

    render(
      <BrowserRouter>
        <RegionsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Geographic Intelligence & Spatial Comparison/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Karnataka/i)[0]).toBeInTheDocument();
      expect(screen.getAllByText(/Maharashtra/i)[0]).toBeInTheDocument();
      expect(screen.getAllByText(/90.0%/i)[0]).toBeInTheDocument();
    });
  });

  it('toggles level navigation between State Level and District Level', async () => {
    vi.mocked(api.getRegionalAnalytics).mockResolvedValue(mockRegionalData);
    vi.mocked(api.getAnalyticsTrends).mockResolvedValue(mockTrendsData);

    render(
      <BrowserRouter>
        <RegionsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/Karnataka/i)[0]).toBeInTheDocument();
    });

    const districtBtn = screen.getByRole('button', { name: /District Level/i });
    fireEvent.click(districtBtn);

    await waitFor(() => {
      expect(api.getRegionalAnalytics).toHaveBeenCalledWith(
        expect.objectContaining({ level: 'district' })
      );
    });
  });

  it('sorts spatial ranking list by completeness % when sort button clicked', async () => {
    vi.mocked(api.getRegionalAnalytics).mockResolvedValue(mockRegionalData);
    vi.mocked(api.getAnalyticsTrends).mockResolvedValue(mockTrendsData);

    render(
      <BrowserRouter>
        <RegionsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText(/Karnataka/i)[0]).toBeInTheDocument();
    });

    const completenessSortBtn = screen.getByRole('button', { name: /Completeness/i });
    fireEvent.click(completenessSortBtn);

    // Karnataka has 90% completeness, Maharashtra has 75%, so Karnataka should be listed first
    const headings = screen.getAllByRole('heading', { level: 3 });
    expect(headings[0]).toHaveTextContent('Karnataka');
  });

  it('renders empty state when API returns zero regions', async () => {
    vi.mocked(api.getRegionalAnalytics).mockResolvedValue({
      level: 'state',
      reporting_month: '2024-12',
      indicator_code: 'opd_attendance',
      regions: [],
    });
    vi.mocked(api.getAnalyticsTrends).mockResolvedValue(mockTrendsData);

    render(
      <BrowserRouter>
        <RegionsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/NO VERIFIED REGIONAL OBSERVATIONS/i)).toBeInTheDocument();
    });
  });

  it('renders error state when API fails', async () => {
    vi.mocked(api.getRegionalAnalytics).mockRejectedValue(new Error('Regional Analytics Timeout'));
    vi.mocked(api.getAnalyticsTrends).mockRejectedValue(new Error('Trend Error'));

    render(
      <BrowserRouter>
        <RegionsPage />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Regional Analytics Timeout/i)).toBeInTheDocument();
    });
  });
});
