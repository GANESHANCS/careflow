import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DataQualityPage } from './DataQualityPage';
import { api } from '../api/client';
import type { DataQualityAnalyticsResponse } from '../api/types';

vi.mock('../api/client', () => ({
  api: {
    getDataQualityAnalytics: vi.fn(),
  },
}));

describe('DataQualityPage Component', () => {
  const mockQualityResponse: DataQualityAnalyticsResponse = {
    overall_quality_score: 87.5,
    total_issues: 3,
    severity_counts: {
      CRITICAL: 0,
      ERROR: 1,
      WARNING: 1,
      INFO: 1,
    },
    category_counts: {
      'Missing Values': 1,
      'Reporting Completeness': 1,
      'Facility ID Consistency': 1,
    },
    incomplete_facilities_count: 1,
    incomplete_facilities: [
      {
        facility_id: 'fac_02',
        facility_name: 'CHC Beta',
        state: 'State A',
        district: 'District 2',
        reported_months: 30,
        expected_months: 36,
        completeness_pct: 83.3,
      },
    ],
    issues: [
      {
        id: 'log_01',
        audit_timestamp: '2024-12-01T10:00:00Z',
        category: 'Missing Values',
        severity: 'ERROR',
        affected_records: 12,
        description: 'Unreported monthly observations exceed 15% threshold in CHC Beta.',
      },
      {
        id: 'log_02',
        audit_timestamp: '2024-12-01T10:00:00Z',
        category: 'Reporting Completeness',
        severity: 'WARNING',
        affected_records: 6,
        description: 'Temporary reporting gap detected during monsoon quarter.',
      },
      {
        id: 'log_03',
        audit_timestamp: '2024-12-01T10:00:00Z',
        category: 'Facility ID Consistency',
        severity: 'INFO',
        affected_records: 1,
        description: 'Composite key assigned to unmapped facility code.',
      },
    ],
    latest_period: '2024-12',
    observation_breakdown: {
      valid_count: 2450,
      zero_count: 120,
      missing_count: 30,
      invalid_count: 0,
      imputed_count: 0,
      total_observations: 2600,
    },
    completeness_summary: {
      expected_observations: 2880,
      actual_reported_observations: 2570,
      completeness_pct: 89.2,
      total_facilities: 10,
      reporting_facilities: 9,
    },
    monthly_timeline: [
      {
        reporting_month: '2024-10',
        completeness_pct: 95.0,
        reporting_facilities: 10,
        total_facilities: 10,
        issue_count: 0,
        status: 'HEALTHY',
      },
      {
        reporting_month: '2024-11',
        completeness_pct: 90.0,
        reporting_facilities: 9,
        total_facilities: 10,
        issue_count: 1,
        status: 'WARNING',
      },
      {
        reporting_month: '2024-12',
        completeness_pct: 83.3,
        reporting_facilities: 8,
        total_facilities: 10,
        issue_count: 2,
        status: 'WARNING',
      },
    ],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (api.getDataQualityAnalytics as any).mockResolvedValue(mockQualityResponse);
  });

  const renderComponent = () => {
    return render(
      <MemoryRouter>
        <DataQualityPage />
      </MemoryRouter>
    );
  };

  it('renders header, overall quality score, and sub-scores', async () => {
    renderComponent();

    expect(await screen.findByText(/Know how reliable the data is before acting on it/i)).toBeInTheDocument();
    expect(screen.getByText(/Overall Data Quality Index/i)).toBeInTheDocument();
    expect(screen.getByText('87.5')).toBeInTheDocument();
    expect(screen.getByText(/GOOD QUALITY/i)).toBeInTheDocument();
  });

  it('renders observation classification breakdown (VALID, ZERO, MISSING, INVALID, IMPUTED)', async () => {
    renderComponent();

    expect(await screen.findByText(/Observation Classification Breakdown/i)).toBeInTheDocument();
    expect(screen.getByText(/Valid Non-Zero/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Reported Zero/i)[0]).toBeInTheDocument();
    expect(screen.getAllByText(/Unreported/i)[0]).toBeInTheDocument();
    expect(screen.getByText(/Strict Governance Rule/i)).toBeInTheDocument();
  });

  it('renders issue severity distribution and category chips', async () => {
    renderComponent();

    expect(await screen.findByText(/13-Point Pipeline Issue Severity & Category Distribution/i)).toBeInTheDocument();
    expect(screen.getByText(/Error Impact/i)).toBeInTheDocument();
    expect(screen.getByText(/Warning Flag/i)).toBeInTheDocument();
    expect(screen.getByText(/Informational/i)).toBeInTheDocument();
  });

  it('renders facility reporting completeness summary and incomplete facilities list', async () => {
    renderComponent();

    expect(await screen.findByText(/HMIS Facility Reporting Completeness & Expected Yield/i)).toBeInTheDocument();
    expect(screen.getByText(/89.2% Completeness/i)).toBeInTheDocument();
    expect(screen.getByText(/Facilities with Incomplete Monthly Reporting Returns/i)).toBeInTheDocument();
    expect(screen.getByText('CHC Beta')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Inspect facility profile for CHC Beta/i })).toHaveAttribute(
      'href',
      '/facilities/fac_02'
    );
  });

  it('renders historical monthly timeline and issue audit registry table with search', async () => {
    renderComponent();

    expect(await screen.findByText(/Historical Monthly Reporting Continuity Timeline/i)).toBeInTheDocument();
    expect(screen.getByText(/13-Point Pipeline Audit Issue Registry/i)).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText(/Search category or description.../i);
    fireEvent.change(searchInput, { target: { value: 'monsoon' } });

    expect(screen.getByText(/Temporary reporting gap detected during monsoon quarter/i)).toBeInTheDocument();
  });

  it('expands 13-point quality audit methodology accordion', async () => {
    renderComponent();

    const methodologyBtn = await screen.findByRole('button', {
      name: /Toggle 13-point data quality methodology details/i,
    });
    fireEvent.click(methodologyBtn);

    expect(await screen.findByText(/Weighted Quality Score Formula \(0 – 100\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Missing Values Audit/i)).toBeInTheDocument();
    expect(screen.getByText(/Source File Integrity/i)).toBeInTheDocument();
  });

  it('handles API error state and retry button', async () => {
    (api.getDataQualityAnalytics as any).mockRejectedValue(new Error('Backend database offline'));

    renderComponent();

    expect(await screen.findByText(/Data Quality Service Unavailable/i)).toBeInTheDocument();
    expect(screen.getByText(/Backend database offline/i)).toBeInTheDocument();
  });
});
