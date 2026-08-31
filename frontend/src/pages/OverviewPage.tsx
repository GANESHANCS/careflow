import React, { useEffect, useState, useCallback } from 'react';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { PageTransition } from '../components/motion/PageTransition';
import { ErrorState } from '../components/feedback/ErrorState';
import { ContextualPopup } from '../components/overlays/ContextualPopup';
import { api } from '../api/client';
import type {
  AnalyticsSummary,
  AnalyticsTrendsResponse,
  RegionalAnalyticsResponse,
  DataQualityAnalyticsResponse,
} from '../api/types';

import { OverviewHeader } from '../components/overview/OverviewHeader';
import { OverviewFilters } from '../components/overview/OverviewFilters';
import { SystemPulse } from '../components/overview/SystemPulse';
import { TrendChart } from '../components/overview/TrendChart';
import { RegionalSignal } from '../components/overview/RegionalSignal';
import { DataReliability } from '../components/overview/DataReliability';
import { AttentionPanel } from '../components/overview/AttentionPanel';

export const OverviewPage: React.FC = () => {
  // State for API endpoints
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [trends, setTrends] = useState<AnalyticsTrendsResponse | null>(null);
  const [regional, setRegional] = useState<RegionalAnalyticsResponse | null>(null);
  const [quality, setQuality] = useState<DataQualityAnalyticsResponse | null>(null);

  // Filter state
  const [selectedIndicator, setSelectedIndicator] = useState<string>('');
  const [selectedState, setSelectedState] = useState<string>('');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [regionalLevel, setRegionalLevel] = useState<'state' | 'district'>('state');

  // Loading & Error states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isMethodologyOpen, setIsMethodologyOpen] = useState<boolean>(false);

  // Fetch all analytics APIs in parallel
  const fetchDashboardData = useCallback(() => {
    setLoading(true);
    setError(null);

    const summaryParams = {
      state: selectedState || undefined,
      district: selectedDistrict || undefined,
    };

    const trendParams = {
      indicator_code: selectedIndicator || undefined,
      state: selectedState || undefined,
      district: selectedDistrict || undefined,
    };

    const regionalParams = {
      level: regionalLevel,
      indicator_code: selectedIndicator || undefined,
      state: selectedState || undefined,
      district: selectedDistrict || undefined,
    };

    Promise.all([
      api.getAnalyticsSummary(summaryParams),
      api.getAnalyticsTrends(trendParams),
      api.getRegionalAnalytics(regionalParams),
      api.getDataQualityAnalytics(),
    ])
      .then(([summaryRes, trendsRes, regionalRes, qualityRes]) => {
        setSummary(summaryRes);
        setTrends(trendsRes);
        setRegional(regionalRes);
        setQuality(qualityRes);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Unable to load CAREFlow overview data.');
        setLoading(false);
      });
  }, [selectedIndicator, selectedState, selectedDistrict, regionalLevel]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleResetFilters = () => {
    setSelectedIndicator('');
    setSelectedState('');
    setSelectedDistrict('');
    setRegionalLevel('state');
  };

  return (
    <PageTransition className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Editorial Header */}
      <ScrollReveal>
        <OverviewHeader
          latestPeriod={summary?.latest_period ?? null}
          totalFacilities={summary?.total_facilities ?? 0}
          reportingCompletenessPct={summary?.reporting_completeness_pct ?? 0}
          onMethodologyClick={() => setIsMethodologyOpen(true)}
        />
      </ScrollReveal>

      {/* Filter Controls Bar */}
      <ScrollReveal delay={0.05}>
        <OverviewFilters
          selectedIndicator={selectedIndicator}
          selectedState={selectedState}
          selectedDistrict={selectedDistrict}
          onIndicatorChange={setSelectedIndicator}
          onStateChange={setSelectedState}
          onDistrictChange={setSelectedDistrict}
          onReset={handleResetFilters}
        />
      </ScrollReveal>

      {/* Main Content / Error Boundary View */}
      {error ? (
        <ErrorState message={error} onRetry={fetchDashboardData} />
      ) : (
        <>
          {/* Section 1: System Pulse (Dominant Primary Metric & Supporting Rows) */}
          <ScrollReveal delay={0.1}>
            <SystemPulse summary={summary} loading={loading} />
          </ScrollReveal>

          {/* Section 2: Time-Series Trend Chart */}
          <ScrollReveal delay={0.15}>
            <TrendChart
              data={trends}
              loading={loading}
              title={selectedIndicator ? `Monthly Attendance: ${selectedIndicator}` : 'Monthly Healthcare Attendance Movement'}
            />
          </ScrollReveal>

          {/* Section 3: Regional Intelligence Signal */}
          <ScrollReveal delay={0.2}>
            <RegionalSignal
              data={regional}
              loading={loading}
              activeLevel={regionalLevel}
              onLevelChange={setRegionalLevel}
            />
          </ScrollReveal>

          {/* Section 4 & 5: Data Reliability & Attention Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-6">
              <ScrollReveal delay={0.25}>
                <DataReliability data={quality} loading={loading} />
              </ScrollReveal>
            </div>
            <div className="lg:col-span-6">
              <ScrollReveal delay={0.3}>
                <AttentionPanel summary={summary} quality={quality} loading={loading} />
              </ScrollReveal>
            </div>
          </div>
        </>
      )}

      {/* Governance & Methodology Modal */}
      <ContextualPopup
        isOpen={isMethodologyOpen}
        onClose={() => setIsMethodologyOpen(false)}
        title="CAREFlow Operational & Methodological Governance"
      >
        <div className="space-y-3 text-xs text-[var(--text-secondary)]">
          <p>
            The CAREFlow operational platform processes raw monthly HMIS observations across outpatient attendance, inpatient admissions, deliveries, and preventive care.
          </p>
          <p>
            Data completeness rates and month-over-month growth calculations enforce zero-fabrication policies. If observations are unverified or awaiting raw return ingestion, features degrade gracefully into diagnostic audit states.
          </p>
          <p className="font-semibold text-[var(--text-primary)]">
            Baseline Primacy: Candidates must beat seasonal naive benchmarks before being selected for deployment.
          </p>
        </div>
      </ContextualPopup>
    </PageTransition>
  );
};

