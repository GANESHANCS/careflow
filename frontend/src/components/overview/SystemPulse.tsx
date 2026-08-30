import React from 'react';
import { Activity, TrendingUp, TrendingDown, Building2, Layers, AlertCircle, Sparkles } from 'lucide-react';
import type { AnalyticsSummary } from '../../api/types';
import { AnimatedNumber } from './AnimatedNumber';

interface SystemPulseProps {
  summary: AnalyticsSummary | null;
  loading: boolean;
}

export const SystemPulse: React.FC<SystemPulseProps> = ({ summary, loading }) => {
  // Check if real observation data is present in summary
  const hasData =
    summary !== null &&
    summary.total_facilities > 0 &&
    summary.totals_by_indicator &&
    Object.keys(summary.totals_by_indicator).length > 0;

  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 shadow-xs animate-pulse">
        <div className="h-4 w-32 bg-[var(--bg-surface-active)] rounded mb-4" />
        <div className="h-12 w-48 bg-[var(--bg-surface-active)] rounded mb-6" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="h-16 bg-[var(--bg-surface-active)] rounded" />
          <div className="h-16 bg-[var(--bg-surface-active)] rounded" />
          <div className="h-16 bg-[var(--bg-surface-active)] rounded" />
        </div>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 shadow-xs text-center relative overflow-hidden">
        <div className="absolute top-0 right-0 p-8 opacity-5">
          <Activity className="w-48 h-48 text-[var(--teal-700)]" />
        </div>
        
        <div className="max-w-xl mx-auto flex flex-col items-center">
          <div className="w-12 h-12 rounded-2xl bg-[var(--amber-50)] border border-[var(--amber-100)] flex items-center justify-center text-[var(--amber-600)] mb-4 shadow-2xs">
            <AlertCircle className="w-6 h-6" />
          </div>

          <span className="text-xs font-bold uppercase tracking-widest text-[var(--amber-700)] mb-1">
            Operational Dynamics
          </span>

          <h2 className="font-display font-extrabold text-2xl sm:text-3xl text-[var(--text-primary)] tracking-tight">
            HMIS Data Awaiting Ingestion
          </h2>

          <p className="mt-2 text-sm text-[var(--text-secondary)] font-normal leading-relaxed">
            Connect verified HMIS reporting data to activate operational intelligence across District Hospitals, CHCs, and PHCs.
          </p>

          {summary && (
            <div className="mt-6 flex flex-wrap items-center justify-center gap-4 text-xs text-[var(--text-muted)] border-t border-[var(--border-subtle)] pt-4 w-full">
              <div className="flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-[var(--teal-600)]" />
                <span>HMIS Facilities Registered: <strong>{summary.total_facilities}</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-[var(--blue-600)]" />
                <span>Completeness Baseline: <strong>{summary.reporting_completeness_pct}%</strong></span>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Identify dominant indicator (e.g. opd_attendance or first available key)
  const indicatorKeys = Object.keys(summary.totals_by_indicator);
  const primaryCode = indicatorKeys.includes('opd_attendance') ? 'opd_attendance' : indicatorKeys[0];
  const primaryValue = summary.totals_by_indicator[primaryCode] ?? 0;
  const primaryName = summary.indicator_names[primaryCode] || primaryCode.replace(/_/g, ' ').toUpperCase();
  const primaryMoM = summary.mom_changes[primaryCode] ?? null;

  // Secondary indicators
  const secondaryCodes = indicatorKeys.filter((c) => c !== primaryCode);

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs relative overflow-hidden">
      {/* Editorial Section Label */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <Activity className="w-4 h-4 text-[var(--teal-600)]" />
          <span>System Pulse — Primary Utilization Signal</span>
        </div>
        <div className="text-xs text-[var(--text-muted)] flex items-center gap-1.5 font-medium">
          <span className="w-2 h-2 rounded-full bg-[var(--green-500)]" />
          <span>Verified HMIS Telemetry</span>
        </div>
      </div>

      {/* Dominant Metric Hero Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        {/* Dominant Left Column */}
        <div className="lg:col-span-7 flex flex-col justify-between bg-gradient-to-br from-[var(--bg-surface-subtle)] to-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 sm:p-8 shadow-2xs">
          <div>
            <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)] mb-2">
              <span>{primaryName}</span>
              <Sparkles className="w-4 h-4 text-[var(--teal-600)]" />
            </div>

            {/* Large Animated Dominant Counter */}
            <div className="text-4xl sm:text-6xl font-extrabold font-display text-[var(--text-primary)] tracking-tight leading-none my-2">
              <AnimatedNumber value={primaryValue} />
            </div>

            <div className="flex items-center gap-3 mt-3">
              {primaryMoM !== null && (
                <div
                  className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold ${
                    primaryMoM >= 0
                      ? 'bg-[var(--green-50)] text-[var(--green-700)] border border-[var(--green-100)]'
                      : 'bg-[var(--coral-50)] text-[var(--coral-700)] border border-[var(--coral-100)]'
                  }`}
                >
                  {primaryMoM >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                  <span>{primaryMoM >= 0 ? `+${primaryMoM.toFixed(1)}%` : `${primaryMoM.toFixed(1)}%`} MoM</span>
                </div>
              )}
              <span className="text-xs text-[var(--text-muted)] font-normal">
                Monthly system attendance across active facilities
              </span>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs text-[var(--text-secondary)] font-medium">
            <span>Reporting Completeness</span>
            <span className="font-bold text-[var(--text-primary)]">{summary.reporting_completeness_pct}%</span>
          </div>
        </div>

        {/* Supporting Secondary Metrics Column */}
        <div className="lg:col-span-5 flex flex-col justify-between gap-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1">
            Supporting Health Indicators
          </h3>

          {secondaryCodes.length > 0 ? (
            secondaryCodes.map((code) => {
              const val = summary.totals_by_indicator[code] ?? 0;
              const name = summary.indicator_names[code] || code.replace(/_/g, ' ');
              const mom = summary.mom_changes[code] ?? null;

              return (
                <div
                  key={code}
                  className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 flex items-center justify-between hover:border-[var(--teal-500)] transition-colors shadow-2xs"
                >
                  <div>
                    <div className="text-xs font-medium text-[var(--text-muted)] capitalize">{name}</div>
                    <div className="text-xl font-bold font-display text-[var(--text-primary)] mt-0.5">
                      <AnimatedNumber value={val} />
                    </div>
                  </div>
                  {mom !== null && (
                    <div
                      className={`text-xs font-semibold px-2 py-0.5 rounded ${
                        mom >= 0 ? 'text-[var(--green-700)] bg-[var(--green-50)]' : 'text-[var(--coral-700)] bg-[var(--coral-50)]'
                      }`}
                    >
                      {mom >= 0 ? `+${mom.toFixed(1)}%` : `${mom.toFixed(1)}%`}
                    </div>
                  )}
                </div>
              );
            })
          ) : (
            <div className="text-xs text-[var(--text-muted)] p-4 border border-dashed border-[var(--border-subtle)] rounded-xl">
              No additional secondary indicator breakdowns available.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
