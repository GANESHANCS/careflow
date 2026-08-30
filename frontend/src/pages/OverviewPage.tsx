import React, { useEffect, useState } from 'react';
import { InteractiveHeading } from '../components/typography/InteractiveHeading';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { EmptyState } from '../components/feedback/EmptyState';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { ChartContainer } from '../components/charts/ChartContainer';
import { ContextualPopup } from '../components/overlays/ContextualPopup';
import { api } from '../api/client';
import type { AnalyticsSummary } from '../api/types';
import { Activity, Building2, ShieldAlert, TrendingUp } from 'lucide-react';

export const OverviewPage: React.FC = () => {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  const fetchSummary = () => {
    setLoading(true);
    setError(null);
    api.getAnalyticsSummary()
      .then((data) => {
        setSummary(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Unable to connect to analytics engine.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <ScrollReveal>
        <InteractiveHeading
          title="Executive Healthcare Overview"
          subtitle="Real-time Operational Intelligence & System Health across Healthcare Facilities in India"
          badge="Executive Summary"
          badgeColor="teal"
          actionText="View System Methodology"
          onActionClick={() => setIsPopupOpen(true)}
        />
      </ScrollReveal>

      {/* Editorial Key Stat Metrics Bar */}
      <ScrollReveal delay={0.1}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs transition-transform duration-200 hover:-translate-y-0.5">
            <div className="flex items-center justify-between text-[var(--text-muted)] text-xs font-medium mb-1">
              <span>Active Facilities</span>
              <Building2 className="w-4 h-4 text-[var(--teal-600)]" />
            </div>
            <div className="text-3xl font-extrabold font-display text-[var(--text-primary)]">
              {loading ? '...' : summary?.active_facilities ?? 0}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--green-500)]" />
              <span>Registered HMIS Outlets</span>
            </div>
          </div>

          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs transition-transform duration-200 hover:-translate-y-0.5">
            <div className="flex items-center justify-between text-[var(--text-muted)] text-xs font-medium mb-1">
              <span>Tracked Indicators</span>
              <Activity className="w-4 h-4 text-[var(--blue-600)]" />
            </div>
            <div className="text-3xl font-extrabold font-display text-[var(--text-primary)]">
              {loading ? '...' : summary?.total_indicators ?? 0}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1">
              OPD, IPD, Deliveries & Care
            </div>
          </div>

          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs transition-transform duration-200 hover:-translate-y-0.5">
            <div className="flex items-center justify-between text-[var(--text-muted)] text-xs font-medium mb-1">
              <span>Total Observations</span>
              <TrendingUp className="w-4 h-4 text-[var(--purple-600)]" />
            </div>
            <div className="text-3xl font-extrabold font-display text-[var(--text-primary)]">
              {loading ? '...' : summary?.total_observations ?? 0}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1">
              Monthly Time-Series Records
            </div>
          </div>

          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs transition-transform duration-200 hover:-translate-y-0.5">
            <div className="flex items-center justify-between text-[var(--text-muted)] text-xs font-medium mb-1">
              <span>Reporting Completeness</span>
              <ShieldAlert className="w-4 h-4 text-[var(--amber-600)]" />
            </div>
            <div className="text-3xl font-extrabold font-display text-[var(--text-primary)]">
              {loading ? '...' : `${summary?.overall_reporting_completeness_pct ?? 0}%`}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1">
              Expected Reporting Rate
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Main Section Content Area */}
      <ScrollReveal delay={0.2}>
        {loading ? (
          <LoadingState type="chart" />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchSummary} />
        ) : summary && summary.total_observations > 0 ? (
          <ChartContainer title="National Monthly Healthcare Attendance Trend" status="success">
            <div className="h-64 flex items-center justify-center text-[var(--text-secondary)] text-sm font-medium">
              Observation Data Present (Chart Visualizer Ready)
            </div>
          </ChartContainer>
        ) : (
          <EmptyState
            title="NO HMIS OBSERVATIONS LOADED"
            description="The CAREFlow analytics engine is connected to the backend database. To view real monthly attendance trends, place HMIS source files under data/raw/ and run the ingestion pipeline."
            actionText="Refresh Analytics"
            onAction={fetchSummary}
          />
        )}
      </ScrollReveal>

      {/* Contextual Popup Trigger Modal */}
      <ContextualPopup
        isOpen={isPopupOpen}
        onClose={() => setIsPopupOpen(false)}
        title="CAREFlow Operational Governance"
      >
        <p className="mb-3">
          The CAREFlow platform applies strict time-series data contracts and diagnostic eligibility checks to operational healthcare data.
        </p>
        <p>
          Models evaluate historical OPD, IPD, and delivery trends using expanding window validation to prevent any data leakage.
        </p>
      </ContextualPopup>
    </div>
  );
};
