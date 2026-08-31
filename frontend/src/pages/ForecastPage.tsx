import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { PageTransition } from '../components/motion/PageTransition';
import { LoadingState } from '../components/feedback/LoadingState';
import { api } from '../api/client';
import type { Facility, Indicator, ForecastResponse, FacilityListResponse } from '../api/types';

import { ForecastHeader } from '../components/forecast/ForecastHeader';
import { ForecastControls } from '../components/forecast/ForecastControls';
import { ForecastReadiness } from '../components/forecast/ForecastReadiness';
import { ForecastHero } from '../components/forecast/ForecastHero';
import { ForecastChart } from '../components/forecast/ForecastChart';
import { ForecastHorizonSelector } from '../components/forecast/ForecastHorizonSelector';
import { ModelSelectionPanel } from '../components/forecast/ModelSelectionPanel';
import { BaselineComparison } from '../components/forecast/BaselineComparison';
import { ForecastUncertainty } from '../components/forecast/ForecastUncertainty';
import { ForecastMethodology } from '../components/forecast/ForecastMethodology';
import { ForecastSignals } from '../components/forecast/ForecastSignals';
import { ForecastEmptyState } from '../components/forecast/ForecastEmptyState';

export const ForecastPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryFacilityId = searchParams.get('facility_id') || '';

  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState<string>(queryFacilityId);
  const [selectedIndicatorCode, setSelectedIndicatorCode] = useState<string>('opd_attendance');
  const [horizon, setHorizon] = useState<number>(12);

  const [forecastData, setForecastData] = useState<ForecastResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Sync URL query param to state if present
  useEffect(() => {
    if (queryFacilityId && queryFacilityId !== selectedFacilityId) {
      setSelectedFacilityId(queryFacilityId);
    }
  }, [queryFacilityId]);

  // Load facilities and indicators list once
  useEffect(() => {
    document.title = 'Forecast Intelligence Workspace | CAREFlow India';

    api.getFacilities({ limit: 100 })
      .then((res: FacilityListResponse | Facility[]) => {
        let facs: Facility[] = [];
        if (Array.isArray(res)) facs = res;
        else if (res && Array.isArray(res.items)) facs = res.items;

        setFacilities(facs);

        // If no facility is selected yet, pre-select the first facility automatically
        if (!queryFacilityId && facs.length > 0) {
          setSelectedFacilityId(facs[0].id);
        }
      })
      .catch(() => setFacilities([]));

    api.getIndicators()
      .then((res: any) => {
        let inds: Indicator[] = [];
        if (Array.isArray(res)) inds = res;
        else if (res && Array.isArray(res.items)) inds = res.items;
        setIndicators(inds);
      })
      .catch(() => setIndicators([]));
  }, []);

  // Primary API fetch function
  const fetchForecast = useCallback(() => {
    if (!selectedFacilityId || !selectedIndicatorCode) return;

    setIsLoading(true);
    setError(null);

    api.getForecast(selectedFacilityId, selectedIndicatorCode, horizon)
      .then((res) => {
        setForecastData(res);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Unable to generate forecast for the selected facility.');
        setIsLoading(false);
      });
  }, [selectedFacilityId, selectedIndicatorCode, horizon]);

  // Fetch forecast whenever selected scope or horizon changes
  useEffect(() => {
    fetchForecast();
  }, [fetchForecast]);

  const handleFacilityChange = (id: string) => {
    setSelectedFacilityId(id);
    setSearchParams({ facility_id: id });
  };

  const handleIndicatorChange = (code: string) => {
    setSelectedIndicatorCode(code);
  };

  const handleHorizonChange = (h: number) => {
    setHorizon(h);
  };

  const selectedFacility = useMemo(
    () => facilities.find((f) => f.id === selectedFacilityId) || null,
    [facilities, selectedFacilityId]
  );

  const selectedIndicator = useMemo(
    () => indicators.find((ind) => ind.code === selectedIndicatorCode) || null,
    [indicators, selectedIndicatorCode]
  );

  const latestHistoricalMonth = useMemo(() => {
    if (!forecastData || !forecastData.historical_points || forecastData.historical_points.length === 0) {
      return null;
    }
    return forecastData.historical_points[forecastData.historical_points.length - 1].observation_month;
  }, [forecastData]);

  const isEligible = forecastData?.eligibility?.is_eligible;

  return (
    <PageTransition className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      {/* 1. Header */}
      <ScrollReveal>
        <ForecastHeader
          selectedFacility={selectedFacility}
          selectedIndicator={selectedIndicator}
          horizon={horizon}
          latestHistoricalMonth={latestHistoricalMonth}
          modelType={forecastData?.model?.model_type}
          isEligible={forecastData?.eligibility?.is_eligible}
        />
      </ScrollReveal>

      {/* 2. Controls Toolbar */}
      <ScrollReveal delay={0.05}>
        <ForecastControls
          facilities={facilities}
          indicators={indicators}
          selectedFacilityId={selectedFacilityId}
          selectedIndicatorCode={selectedIndicatorCode}
          horizon={horizon}
          onFacilityChange={handleFacilityChange}
          onIndicatorChange={handleIndicatorChange}
          onHorizonChange={handleHorizonChange}
        />
      </ScrollReveal>

      {/* 3. Main Content Body */}
      {isLoading ? (
        <LoadingState type="chart" />
      ) : error ? (
        <ForecastEmptyState
          type="ERROR"
          errorMessage={error}
          onRetry={fetchForecast}
        />
      ) : !forecastData ? (
        <ForecastEmptyState
          type="NO_SELECTION"
          facilities={facilities}
          onSelectFacility={handleFacilityChange}
        />
      ) : (
        <>
          {/* Eligibility Banner & Diagnostic Diagnostics */}
          <ScrollReveal delay={0.1}>
            <ForecastReadiness eligibility={forecastData.eligibility} />
          </ScrollReveal>

          {/* Eligible Forecast View */}
          {forecastData.status === 'SUCCESS' && isEligible && (
            <>
              {/* Hero Metric & Model Badge */}
              <ScrollReveal delay={0.12}>
                <ForecastHero data={forecastData} />
              </ScrollReveal>

              {/* Forecast Horizon Selector */}
              <ScrollReveal delay={0.14}>
                <ForecastHorizonSelector
                  currentHorizon={horizon}
                  onHorizonSelect={handleHorizonChange}
                />
              </ScrollReveal>

              {/* Forecast Line Chart with 95% Confidence Band */}
              <ScrollReveal delay={0.16}>
                <ForecastChart
                  historicalPoints={forecastData.historical_points}
                  forecastPoints={forecastData.forecast_points}
                  indicatorName={selectedIndicator?.name || selectedIndicatorCode}
                  unit={selectedIndicator?.unit || 'patients'}
                  isEligible={true}
                />
              </ScrollReveal>

              {/* Model Selection & Performance Evaluation */}
              <ScrollReveal delay={0.18}>
                <ModelSelectionPanel data={forecastData} />
              </ScrollReveal>

              {/* Baseline Comparison (Naive vs Candidate Models) */}
              <ScrollReveal delay={0.2}>
                <BaselineComparison data={forecastData} />
              </ScrollReveal>

              {/* Prediction Interval & Uncertainty Analysis */}
              <ScrollReveal delay={0.22}>
                <ForecastUncertainty data={forecastData} />
              </ScrollReveal>

              {/* Action Signals & Operational Alerts */}
              <ScrollReveal delay={0.24}>
                <ForecastSignals data={forecastData} />
              </ScrollReveal>

              {/* Methodology & Model Governance Accordion */}
              <ScrollReveal delay={0.26}>
                <ForecastMethodology />
              </ScrollReveal>
            </>
          )}

          {/* Ineligible Mode: Show Diagnostic Empty State with Historical Series Chart */}
          {forecastData.status === 'NOT_ELIGIBLE' && (
            <>
              {forecastData.historical_points && forecastData.historical_points.length > 0 && (
                <ScrollReveal delay={0.15}>
                  <ForecastChart
                    historicalPoints={forecastData.historical_points}
                    forecastPoints={[]}
                    indicatorName={selectedIndicator?.name || selectedIndicatorCode}
                    unit={selectedIndicator?.unit || 'patients'}
                    isEligible={false}
                  />
                </ScrollReveal>
              )}

              <ScrollReveal delay={0.2}>
                <ForecastEmptyState
                  type="NOT_ELIGIBLE"
                  facilities={facilities}
                  onSelectFacility={handleFacilityChange}
                  reasonMessage={forecastData.eligibility?.reason_message}
                />
              </ScrollReveal>
            </>
          )}
        </>
      )}
    </PageTransition>
  );
};
