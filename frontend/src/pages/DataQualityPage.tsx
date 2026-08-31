import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { DataQualityAnalyticsResponse } from '../api/types';

import { DataQualityHeader } from '../components/data-quality/DataQualityHeader';
import { QualityScoreHero } from '../components/data-quality/QualityScoreHero';
import { QualityBreakdown } from '../components/data-quality/QualityBreakdown';
import { IssueDistribution } from '../components/data-quality/IssueDistribution';
import { ReportingCompleteness } from '../components/data-quality/ReportingCompleteness';
import { QualityIssueTable } from '../components/data-quality/QualityIssueTable';
import { IncompleteFacilities } from '../components/data-quality/IncompleteFacilities';
import { QualityTimeline } from '../components/data-quality/QualityTimeline';
import { QualityAttention } from '../components/data-quality/QualityAttention';
import { QualityMethodology } from '../components/data-quality/QualityMethodology';

import { PageTransition } from '../components/motion/PageTransition';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { RefreshCw, Database } from 'lucide-react';

export const DataQualityPage: React.FC = () => {
  const [data, setData] = useState<DataQualityAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');

  const fetchQualityData = () => {
    setLoading(true);
    setError(null);
    api.getDataQualityAnalytics()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Unable to retrieve data quality audit logs.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchQualityData();
  }, []);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fadeIn">
        <div className="h-24 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl animate-pulse" />
        <div className="h-64 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl animate-pulse" />
        <LoadingState type="card" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <ErrorState
          title="Data Quality Service Unavailable"
          message={error}
          onRetry={fetchQualityData}
        />
      </div>
    );
  }

  // Handle case when database has no records loaded
  const hasNoData = !data || (
    (data.observation_breakdown?.total_observations ?? 0) === 0 &&
    (data.completeness_summary?.expected_observations ?? 0) === 0 &&
    data.total_issues === 0
  );

  return (
    <PageTransition className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Editorial Header */}
      <DataQualityHeader data={data} />

      {hasNoData ? (
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-12 text-center my-8">
          <Database className="w-12 h-12 text-[var(--teal-600)] mx-auto mb-4" />
          <h2 className="text-xl font-bold text-[var(--text-primary)]">HMIS DATA AWAITING INGESTION</h2>
          <p className="text-sm text-[var(--text-muted)] mt-2 max-w-lg mx-auto">
            Data-quality analytics and 13-point pipeline audit scores will appear once verified HMIS returns are ingested.
          </p>
          <button
            onClick={fetchQualityData}
            className="mt-6 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--teal-600)] hover:bg-[var(--teal-700)] text-white font-bold text-xs shadow-sm transition-all cursor-pointer"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Check Pipeline Database</span>
          </button>
        </div>
      ) : (
        <>
          {/* 2. Quality Score Hero */}
          <QualityScoreHero data={data} />

          {/* 3. Observation Classification Breakdown */}
          <QualityBreakdown data={data} />

          {/* 4. Issue Severity & Category Distribution */}
          <IssueDistribution
            data={data}
            selectedSeverity={selectedSeverity}
            onSelectSeverity={setSelectedSeverity}
          />

          {/* 5. Reporting Completeness Yield */}
          <ReportingCompleteness data={data} />

          {/* 6. Operational Governance Attention Required */}
          <QualityAttention data={data} />

          {/* 7. Facilities with Incomplete Monthly Reporting */}
          <IncompleteFacilities facilities={data?.incomplete_facilities || []} />

          {/* 8. Monthly Reporting Continuity Timeline */}
          <QualityTimeline timeline={data?.monthly_timeline || []} />

          {/* 9. 13-Point Pipeline Audit Issue Registry */}
          <QualityIssueTable
            issues={data?.issues || []}
            selectedSeverity={selectedSeverity}
            onSelectSeverity={setSelectedSeverity}
          />

          {/* 10. 13-Point Quality Audit Methodology Accordion */}
          <QualityMethodology />
        </>
      )}
    </PageTransition>
  );
};

