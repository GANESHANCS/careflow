import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { api } from '../api/client';
import type { Facility, FacilityAnalyticsResponse, ForecastResponse } from '../api/types';

import { FacilityHeader } from '../components/facilities/FacilityHeader';
import { FacilityUtilization } from '../components/facilities/FacilityUtilization';
import { FacilityTrendChart } from '../components/facilities/FacilityTrendChart';
import { FacilityReliability } from '../components/facilities/FacilityReliability';
import { FacilitySignals } from '../components/facilities/FacilitySignals';
import { ForecastReadiness } from '../components/facilities/ForecastReadiness';

export const FacilityDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [facility, setFacility] = useState<Facility | null>(null);
  const [analytics, setAnalytics] = useState<FacilityAnalyticsResponse | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchFacilityData = useCallback(() => {
    if (!id) return;

    setLoading(true);
    setError(null);

    Promise.all([
      api.getFacilityById(id).catch(() => null),
      api.getFacilityAnalytics(id).catch(() => null),
      api.getForecast(id, 'opd_attendance', 12).catch(() => null),
    ])
      .then(([facData, analyticsData, forecastData]) => {
        if (!facData && !analyticsData) {
          setError(`Facility with ID '${id}' was not found in the database.`);
        } else {
          if (facData) setFacility(facData);
          if (analyticsData) setAnalytics(analyticsData);
          if (forecastData) setForecast(forecastData);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Unable to load facility intelligence profile.');
        setLoading(false);
      });
  }, [id]);

  useEffect(() => {
    fetchFacilityData();
  }, [fetchFacilityData]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto pb-12">
        <LoadingState type="detail" />
      </div>
    );
  }

  if (error || !facility) {
    return (
      <div className="max-w-7xl mx-auto pb-12">
        <ErrorState
          title="Facility Not Found"
          message={error || `Facility '${id}' does not exist in the database.`}
          onRetry={fetchFacilityData}
        />
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Editorial Header */}
      <ScrollReveal>
        <FacilityHeader
          facility={facility}
          reportingCompletenessPct={analytics?.completeness_pct ?? analytics?.reporting_completeness_pct ?? null}
        />
      </ScrollReveal>

      {/* Section 1: Dominant Facility Utilization Signal */}
      <ScrollReveal delay={0.05}>
        <FacilityUtilization analytics={analytics} loading={loading} />
      </ScrollReveal>

      {/* Section 2: Historical Attendance Movement SVG Line Chart */}
      <ScrollReveal delay={0.1}>
        <FacilityTrendChart analytics={analytics} loading={loading} />
      </ScrollReveal>

      {/* Section 3 & 4: Reporting Reliability & Diagnostic Signals */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        <div className="lg:col-span-6">
          <ScrollReveal delay={0.15}>
            <FacilityReliability analytics={analytics} loading={loading} />
          </ScrollReveal>
        </div>
        <div className="lg:col-span-6">
          <ScrollReveal delay={0.2}>
            <FacilitySignals analytics={analytics} loading={loading} />
          </ScrollReveal>
        </div>
      </div>

      {/* Section 5: Forecast Readiness & Phase 5 ML Diagnostic */}
      <ScrollReveal delay={0.25}>
        <ForecastReadiness facilityId={facility.id} forecastData={forecast} loading={loading} />
      </ScrollReveal>
    </div>
  );
};
