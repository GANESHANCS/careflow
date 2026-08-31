import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { EmptyState } from '../components/feedback/EmptyState';
import { api } from '../api/client';
import type {
  RegionalAnalyticsResponse,
  AnalyticsTrendsResponse,
  Indicator,
  FacilityListResponse,
  Facility,
} from '../api/types';

import { RegionalHeader } from '../components/regions/RegionalHeader';
import { RegionalFilters } from '../components/regions/RegionalFilters';
import { RegionalOverview } from '../components/regions/RegionalOverview';
import { RegionalRanking } from '../components/regions/RegionalRanking';
import { RegionalTrend } from '../components/regions/RegionalTrend';
import { RegionalReliability } from '../components/regions/RegionalReliability';
import { RegionalAttention } from '../components/regions/RegionalAttention';

export const RegionsPage: React.FC = () => {
  const [level, setLevel] = useState<'state' | 'district'>('state');
  const [selectedIndicator, setSelectedIndicator] = useState<string>('');
  const [selectedState, setSelectedState] = useState<string>('');
  const [selectedRegionName, setSelectedRegionName] = useState<string | null>(null);

  const [regionalData, setRegionalData] = useState<RegionalAnalyticsResponse | null>(null);
  const [trendData, setTrendData] = useState<AnalyticsTrendsResponse | null>(null);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [facilities, setFacilities] = useState<Facility[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch static lookups once
  useEffect(() => {
    api.getIndicators()
      .then((inds: any) => {
        if (Array.isArray(inds)) setIndicators(inds);
        else if (inds && Array.isArray(inds.items)) setIndicators(inds.items);
        else setIndicators([]);
      })
      .catch(() => setIndicators([]));

    api.getFacilities({ limit: 100 })
      .then((res: FacilityListResponse | Facility[]) => {
        if (Array.isArray(res)) setFacilities(res);
        else if (res && Array.isArray(res.items)) setFacilities(res.items);
      })
      .catch(() => setFacilities([]));
  }, []);

  // Derive available states dynamically from data
  const statesList = useMemo(() => {
    const list = Array.from(new Set(facilities.map((f) => f.state).filter(Boolean))).sort();
    if (list.length > 0) return list;
    return ['Karnataka', 'Maharashtra', 'Tamil Nadu', 'Kerala'];
  }, [facilities]);

  const fetchRegionalAnalytics = useCallback(() => {
    setLoading(true);
    setError(null);

    const regionalParams = {
      level,
      indicator_code: selectedIndicator || undefined,
      state: selectedState || undefined,
    };

    const trendParams = {
      indicator_code: selectedIndicator || 'opd_attendance',
      state: selectedState || undefined,
    };

    Promise.all([
      api.getRegionalAnalytics(regionalParams),
      api.getAnalyticsTrends(trendParams).catch(() => null),
    ])
      .then(([regRes, trendRes]) => {
        setRegionalData(regRes);
        setTrendData(trendRes);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Unable to retrieve regional intelligence data.');
        setLoading(false);
      });
  }, [level, selectedIndicator, selectedState]);

  useEffect(() => {
    fetchRegionalAnalytics();
  }, [fetchRegionalAnalytics]);

  const handleReset = () => {
    setSelectedIndicator('');
    setSelectedState('');
    setSelectedRegionName(null);
  };

  const regionsList = regionalData?.regions ?? [];

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Editorial Header */}
      <ScrollReveal>
        <RegionalHeader
          reportingMonth={regionalData?.reporting_month}
          level={level}
          totalRegions={regionsList.length}
        />
      </ScrollReveal>

      {/* Filter Navigation Bar */}
      <ScrollReveal delay={0.05}>
        <RegionalFilters
          level={level}
          onLevelChange={setLevel}
          selectedIndicator={selectedIndicator}
          onIndicatorChange={setSelectedIndicator}
          selectedState={selectedState}
          onStateChange={setSelectedState}
          indicators={indicators}
          statesList={statesList}
          onReset={handleReset}
        />
      </ScrollReveal>

      {/* Content Section */}
      {loading ? (
        <LoadingState type="table" />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchRegionalAnalytics} />
      ) : !regionalData || regionsList.length === 0 ? (
        <EmptyState
          title="NO VERIFIED REGIONAL OBSERVATIONS"
          description="Regional intelligence will activate when verified HMIS reporting data is available for the selected jurisdiction level and indicator filters."
          actionText="Reset Filters"
          onAction={handleReset}
          icon="database"
        />
      ) : (
        <div className="space-y-8">
          {/* Section 1: Hero Regional Utilization Signal */}
          <ScrollReveal delay={0.1}>
            <RegionalOverview data={regionalData} loading={loading} />
          </ScrollReveal>

          {/* Section 2: Spatial Ranked Comparison */}
          <ScrollReveal delay={0.15}>
            <RegionalRanking
              regions={regionsList}
              level={level}
              onSelectRegion={(name) => setSelectedRegionName(name)}
            />
          </ScrollReveal>

          {/* Section 3: Monthly Time-Series Trend */}
          <ScrollReveal delay={0.2}>
            <RegionalTrend
              trends={trendData}
              loading={loading}
              regionName={selectedRegionName || selectedState || 'All Regions'}
            />
          </ScrollReveal>

          {/* Section 4 & 5: Governance & Diagnostic Signals */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            <div className="lg:col-span-6">
              <ScrollReveal delay={0.25}>
                <RegionalReliability regions={regionsList} loading={loading} level={level} />
              </ScrollReveal>
            </div>
            <div className="lg:col-span-6">
              <ScrollReveal delay={0.3}>
                <RegionalAttention regions={regionsList} loading={loading} />
              </ScrollReveal>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
