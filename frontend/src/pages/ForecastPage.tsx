import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ScrollReveal } from '../components/motion/ScrollReveal';
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
      .then((inds: any) => {
        if (Array.isArray(inds)) setIndicators(inds);
        else if (inds && Array.isArray(inds.items)) setIndicators(inds.items);
        else setIndicators([]);
      })
      .catch(() => setIndicators([]));
  }, []);

  // Fetch forecast data when facility, indicator, or horizon changes
  const fetchForecast = useCallback((facId: string, indCode: string, h: number) => {
    if (!facId) {
      setForecastData(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    api.getForecast(facId, indCode, h)
      .then((res) => {
        setForecastData(res);
        setIsLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Unable to query CAREFlow backend forecasting engine.');
        setForecastData(null);
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    if (selectedFacilityId) {
      fetchForecast(selectedFacilityId, selectedIndicatorCode, horizon);
    }
  }, [selectedFacilityId, selectedIndicatorCode, horizon, fetchForecast]);

  const handleFacilityChange = (id: string) => {
    setSelectedFacilityId(id);
    if (id) {
      setSearchParams({ facility_id: id });
    } else {
      setSearchParams({});
    }
  };

  const handleIndicatorChange = (code: string) => {
    setSelectedIndicatorCode(code);
  };

  const handleHorizonChange = (h: number) => {
    setHorizon(h);
  };

  const selectedFacility = useMemo(
    () => facilities.find((f) => f.id === selectedFacilityId || f.facility_code === selectedFacilityId) || null,
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

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
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

      {/* 2. Control Toolbar */}
      <ScrollReveal delay={0.05}>
        <ForecastControls
          facilities={facilities}
          indicators={indicators}
          selectedFacilityId={selectedFacilityId}
          onFacilityChange={handleFacilityChange}
          selectedIndicatorCode={selectedIndicatorCode}
          onIndicatorChange={handleIndicatorChange}
          horizon={horizon}
          onHorizonChange={handleHorizonChange}
          isLoading={isLoading}
        />
      </ScrollReveal>

      {/* 3. Loading State */}
      {isLoading && (
        <ScrollReveal>
          <LoadingState type="chart" />
        </ScrollReveal>
      )}

      {/* 4. Network/API Error State */}
      {!isLoading && error && (
        <ScrollReveal>
          <ForecastEmptyState
            type="ERROR"
            errorMessage={error}
            onRetry={() => fetchForecast(selectedFacilityId, selectedIndicatorCode, horizon)}
          />
        </ScrollReveal>
      )}

      {/* 5. No Facility Selected State */}
      {!isLoading && !error && !selectedFacilityId && (
        <ScrollReveal>
          <ForecastEmptyState
            type="NO_SELECTION"
            facilities={facilities}
            onSelectFacility={handleFacilityChange}
          />
        </ScrollReveal>
      )}

      {/* 6. Forecast Content (Eligible or Ineligible) */}
      {!isLoading && !error && forecastData && (
        <>
          {/* Eligibility Audit Card */}
          <ScrollReveal delay={0.1}>
            <ForecastReadiness
              eligibility={forecastData.eligibility}
              dataQuality={forecastData.data_quality}
              totalHistoricalMonths={forecastData.historical_points?.length}
            />
          </ScrollReveal>

          {/* Success Mode: Full Forecasting Dashboard */}
          {forecastData.status === 'SUCCESS' && (
            <>
              <ScrollReveal delay={0.15}>
                <ForecastHero data={forecastData} />
              </ScrollReveal>

              <ScrollReveal delay={0.2}>
                <ForecastChart
                  historicalPoints={forecastData.historical_points}
                  forecastPoints={forecastData.forecast_points}
                  indicatorName={selectedIndicator?.name || selectedIndicatorCode}
                  unit={selectedIndicator?.unit || 'patients'}
                  isEligible={true}
                />
              </ScrollReveal>

              <ScrollReveal delay={0.25}>
                <ForecastHorizonSelector
                  currentHorizon={horizon}
                  onHorizonSelect={handleHorizonChange}
                  isLoading={isLoading}
                />
              </ScrollReveal>

              <ScrollReveal delay={0.3}>
                <ForecastSignals data={forecastData} />
              </ScrollReveal>

              <ScrollReveal delay={0.35}>
                <ModelSelectionPanel data={forecastData} />
              </ScrollReveal>

              <ScrollReveal delay={0.4}>
                <BaselineComparison data={forecastData} />
              </ScrollReveal>

              <ScrollReveal delay={0.45}>
                <ForecastUncertainty data={forecastData} />
              </ScrollReveal>

              <ScrollReveal delay={0.5}>
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
    </div>
  );
};
