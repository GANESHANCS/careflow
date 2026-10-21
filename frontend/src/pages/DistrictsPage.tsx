import React, { useState, useEffect, useCallback } from 'react';
import { PageTransition } from '../components/motion/PageTransition';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { api } from '../api/client';
import type {
  DistrictCatalogResponse,
  DistrictIndicatorCatalogResponse,
  DistrictIndicatorItem,
  DistrictMonthlyTrendsResponse,
  DistrictComparisonResponse,
  DistrictDataQualitySummaryResponse,
} from '../api/types';

import { DistrictHeader } from '../components/districts/DistrictHeader';
import type { DistrictTab } from '../components/districts/DistrictHeader';
import { DistrictFilters } from '../components/districts/DistrictFilters';
import { DistrictMonthlyTrendChart } from '../components/districts/DistrictMonthlyTrendChart';
import { DistrictComparisonChart } from '../components/districts/DistrictComparisonChart';
import { DistrictDetailTable } from '../components/districts/DistrictDetailTable';
import { DistrictQualityTab } from '../components/districts/DistrictQualityTab';

export const DistrictsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<DistrictTab>('trends');

  // Lookups and Catalog state
  const [catalog, setCatalog] = useState<DistrictCatalogResponse | null>(null);
  const [indicators, setIndicators] = useState<DistrictIndicatorItem[]>([]);
  const [catalogLoading, setCatalogLoading] = useState<boolean>(true);
  const [catalogError, setCatalogError] = useState<string | null>(null);

  // Active Filter state
  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [selectedSNo, setSelectedSNo] = useState<string>('');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('');
  const [selectedSubgroup, setSelectedSubgroup] = useState<string>('');
  const [selectedFinancialYear, setSelectedFinancialYear] = useState<string>('');

  // Analytics Result state
  const [trendsData, setTrendsData] = useState<DistrictMonthlyTrendsResponse | null>(null);
  const [trendsLoading, setTrendsLoading] = useState<boolean>(false);
  const [trendsError, setTrendsError] = useState<string | null>(null);

  const [comparisonData, setComparisonData] = useState<DistrictComparisonResponse | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState<boolean>(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  const [qualityData, setQualityData] = useState<DistrictDataQualitySummaryResponse | null>(null);
  const [qualityLoading, setQualityLoading] = useState<boolean>(false);

  // Export progress states
  const [exportingTrends, setExportingTrends] = useState<boolean>(false);
  const [exportingComparison, setExportingComparison] = useState<boolean>(false);

  // 1. Initial Catalog & Indicators Fetch
  const fetchCatalogAndIndicators = useCallback(() => {
    setCatalogLoading(true);
    setCatalogError(null);

    Promise.all([api.getDistrictCatalog(), api.getDistrictIndicators()])
      .then(([catRes, indRes]: [DistrictCatalogResponse, DistrictIndicatorCatalogResponse]) => {
        setCatalog(catRes);
        const inds = indRes.indicators || [];
        setIndicators(inds);

        // Populate initial filter defaults if not already selected
        if (!selectedDistrict && catRes.districts && catRes.districts.length > 0) {
          setSelectedDistrict(catRes.districts[0]);
        }
        if (!selectedSNo && inds.length > 0) {
          setSelectedSNo(inds[0].s_no);
        }
        if (!selectedPeriod && catRes.reporting_periods && catRes.reporting_periods.length > 0) {
          setSelectedPeriod(catRes.reporting_periods[0]);
        }
        if (!selectedFinancialYear && catRes.financial_years && catRes.financial_years.length > 0) {
          setSelectedFinancialYear(catRes.financial_years[0]);
        }
        setCatalogLoading(false);
      })
      .catch((err) => {
        setCatalogError(err instanceof Error ? err.message : 'Unable to connect to District Analytics Catalog.');
        setCatalogLoading(false);
      });
  }, [selectedDistrict, selectedSNo, selectedPeriod, selectedFinancialYear]);

  useEffect(() => {
    fetchCatalogAndIndicators();
  }, [fetchCatalogAndIndicators]);

  // 2. Fetch Monthly Trends when District, S.No, Subgroup, or FY changes
  const fetchMonthlyTrends = useCallback(() => {
    if (!selectedDistrict || !selectedSNo) return;

    setTrendsLoading(true);
    setTrendsError(null);

    api.getDistrictMonthlyTrends({
      district: selectedDistrict,
      s_no: selectedSNo,
      subgroup_type: selectedSubgroup || undefined,
      financial_year: selectedFinancialYear || undefined,
    })
      .then((data) => {
        setTrendsData(data);
        setTrendsLoading(false);
      })
      .catch((err) => {
        setTrendsError(err instanceof Error ? err.message : 'Error fetching monthly trend observations.');
        setTrendsLoading(false);
      });
  }, [selectedDistrict, selectedSNo, selectedSubgroup, selectedFinancialYear]);

  useEffect(() => {
    fetchMonthlyTrends();
  }, [fetchMonthlyTrends]);

  // 3. Fetch Cross-District Comparison when S.No, Period, Subgroup, or FY changes
  const fetchDistrictComparison = useCallback(() => {
    if (!selectedSNo || !selectedPeriod) return;

    setComparisonLoading(true);
    setComparisonError(null);

    api.getDistrictComparison({
      s_no: selectedSNo,
      reporting_month: selectedPeriod,
      subgroup_type: selectedSubgroup || undefined,
      financial_year: selectedFinancialYear || undefined,
    })
      .then((data) => {
        setComparisonData(data);
        setComparisonLoading(false);
      })
      .catch((err) => {
        setComparisonError(err instanceof Error ? err.message : 'Error fetching district comparison data.');
        setComparisonLoading(false);
      });
  }, [selectedSNo, selectedPeriod, selectedSubgroup, selectedFinancialYear]);

  useEffect(() => {
    fetchDistrictComparison();
  }, [fetchDistrictComparison]);

  // 4. Fetch Quality Summary
  const fetchQualitySummary = useCallback(() => {
    setQualityLoading(true);
    api.getDistrictQuality()
      .then((data) => {
        setQualityData(data);
        setQualityLoading(false);
      })
      .catch(() => {
        setQualityLoading(false);
      });
  }, []);

  useEffect(() => {
    fetchQualitySummary();
  }, [fetchQualitySummary]);

  // Export handlers
  const handleExportTrends = useCallback(async () => {
    if (!selectedDistrict || !selectedSNo) return;
    setExportingTrends(true);
    try {
      await api.downloadDistrictTrendsCsv({
        district: selectedDistrict,
        s_no: selectedSNo,
        subgroup_type: selectedSubgroup || undefined,
        financial_year: selectedFinancialYear || undefined,
      });
    } catch (err) {
      alert(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setExportingTrends(false);
    }
  }, [selectedDistrict, selectedSNo, selectedSubgroup, selectedFinancialYear]);

  const handleExportComparison = useCallback(async () => {
    if (!selectedSNo || !selectedPeriod) return;
    setExportingComparison(true);
    try {
      await api.downloadDistrictComparisonCsv({
        s_no: selectedSNo,
        reporting_month: selectedPeriod,
        subgroup_type: selectedSubgroup || undefined,
        financial_year: selectedFinancialYear || undefined,
      });
    } catch (err) {
      alert(`Export failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setExportingComparison(false);
    }
  }, [selectedSNo, selectedPeriod, selectedSubgroup, selectedFinancialYear]);

  // Reset filter state to initial defaults
  const handleResetFilters = () => {
    if (catalog?.districts?.length) setSelectedDistrict(catalog.districts[0]);
    if (indicators.length) setSelectedSNo(indicators[0].s_no);
    if (catalog?.reporting_periods?.length) setSelectedPeriod(catalog.reporting_periods[0]);
    if (catalog?.financial_years?.length) setSelectedFinancialYear(catalog.financial_years[0]);
    setSelectedSubgroup('');
  };

  if (catalogLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
        <div className="h-32 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl animate-pulse" />
        <div className="h-20 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl animate-pulse" />
        <LoadingState type="card" />
      </div>
    );
  }

  if (catalogError) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <ErrorState
          title="District Analytics Catalog Offline"
          message={catalogError}
          onRetry={fetchCatalogAndIndicators}
        />
      </div>
    );
  }

  const currentParamDesc =
    trendsData?.parameter_name ||
    indicators.find((ind) => ind.s_no === selectedSNo)?.parameter_name ||
    'Selected Health Indicator';

  return (
    <PageTransition className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-16">
      {/* Editorial Header with Source Separation Badge and Workspace Tabs */}
      <ScrollReveal>
        <DistrictHeader
          activeTab={activeTab}
          onTabChange={setActiveTab}
          selectedDistrict={selectedDistrict}
          totalDistricts={catalog?.districts?.length ?? 31}
          totalIndicators={indicators.length}
        />
      </ScrollReveal>

      {/* Primary District Filter Bar (rendered for trends, comparison, and raw observation table) */}
      {activeTab !== 'quality' && (
        <ScrollReveal delay={0.05}>
          <DistrictFilters
            districts={catalog?.districts ?? []}
            indicators={indicators}
            reportingPeriods={catalog?.reporting_periods ?? []}
            subgroups={catalog?.subgroup_types ?? []}
            financialYears={catalog?.financial_years ?? []}
            selectedDistrict={selectedDistrict}
            onDistrictChange={setSelectedDistrict}
            selectedSNo={selectedSNo}
            onSNoChange={setSelectedSNo}
            selectedPeriod={selectedPeriod}
            onPeriodChange={setSelectedPeriod}
            selectedSubgroup={selectedSubgroup}
            onSubgroupChange={setSelectedSubgroup}
            selectedFinancialYear={selectedFinancialYear}
            onFinancialYearChange={setSelectedFinancialYear}
            onReset={handleResetFilters}
          />
        </ScrollReveal>
      )}

      {/* Tab 1: Monthly Time-Series Trend */}
      {activeTab === 'trends' && (
        <ScrollReveal delay={0.1}>
          {trendsError ? (
            <ErrorState
              title="Time-Series Observation Query Failed"
              message={trendsError}
              onRetry={fetchMonthlyTrends}
            />
          ) : (
            <DistrictMonthlyTrendChart
              trendData={trendsData}
              loading={trendsLoading}
              onExportCsv={handleExportTrends}
              isExporting={exportingTrends}
            />
          )}
        </ScrollReveal>
      )}

      {/* Tab 2: Cross-District Comparison */}
      {activeTab === 'compare' && (
        <ScrollReveal delay={0.1}>
          {comparisonError ? (
            <ErrorState
              title="District Comparison Query Failed"
              message={comparisonError}
              onRetry={fetchDistrictComparison}
            />
          ) : (
            <DistrictComparisonChart
              comparisonData={comparisonData}
              loading={comparisonLoading}
              selectedDistrict={selectedDistrict}
              onSelectDistrict={(dist) => {
                setSelectedDistrict(dist);
                setActiveTab('trends');
              }}
              onExportCsv={handleExportComparison}
              isExporting={exportingComparison}
            />
          )}
        </ScrollReveal>
      )}

      {/* Tab 3: Raw Observations Log */}
      {activeTab === 'table' && (
        <ScrollReveal delay={0.1}>
          <DistrictDetailTable
            observations={trendsData?.observations ?? []}
            district={selectedDistrict}
            sNo={selectedSNo}
            parameterName={currentParamDesc}
            onExportCsv={handleExportTrends}
            isExporting={exportingTrends}
          />
        </ScrollReveal>
      )}

      {/* Tab 4: Phase 11F & 12B Data Quality, Ingestion Traceability & Verified Registry */}
      {activeTab === 'quality' && (
        <ScrollReveal delay={0.1}>
          <DistrictQualityTab
            qualityData={qualityData}
            loading={qualityLoading}
          />
        </ScrollReveal>
      )}
    </PageTransition>
  );
};
