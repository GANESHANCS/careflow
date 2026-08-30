import React from 'react';
import { Activity, TrendingUp, TrendingDown, Minus, Info } from 'lucide-react';
import { AnimatedNumber } from '../overview/AnimatedNumber';
import type { FacilityAnalyticsResponse } from '../../api/types';

interface FacilityUtilizationProps {
  analytics: FacilityAnalyticsResponse | null;
  loading: boolean;
}

export const FacilityUtilization: React.FC<FacilityUtilizationProps> = ({ analytics, loading }) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-4 w-40 bg-[var(--bg-surface-active)] rounded" />
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-6 h-36 bg-[var(--bg-surface-active)] rounded-xl" />
          <div className="md:col-span-6 h-36 bg-[var(--bg-surface-active)] rounded-xl" />
        </div>
      </div>
    );
  }

  const latestMetrics = analytics?.latest_metrics ?? [];

  if (!analytics || latestMetrics.length === 0) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs text-center">
        <div className="w-10 h-10 rounded-full bg-[var(--amber-50)] text-[var(--amber-600)] flex items-center justify-center mx-auto mb-3 border border-[var(--amber-100)]">
          <Info className="w-5 h-5" />
        </div>
        <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
          No Recent Utilization Observations
        </h3>
        <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto mt-1 leading-relaxed">
          This facility is registered in the database, but recent monthly observations for OPD, IPD, or delivery indicators are awaiting raw return ingestion.
        </p>
      </div>
    );
  }

  // Identify dominant primary metric (e.g. opd_attendance or first metric)
  const primaryMetric = latestMetrics.find(
    (m) => m.indicator_code.toLowerCase().includes('opd') || m.indicator_code.toLowerCase().includes('attendance')
  ) || latestMetrics[0];

  const supportingMetrics = latestMetrics.filter(
    (m) => m.indicator_code !== primaryMetric.indicator_code
  );

  const formatValue = (val: number | null) => {
    if (val === null) return 'N/A';
    return val.toLocaleString('en-IN');
  };

  const getMoMBadge = (pct: number | null) => {
    if (pct === null) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--bg-surface-subtle)] text-[var(--text-muted)] border border-[var(--border-subtle)]">
          <Minus className="w-3 h-3" />
          <span>Baseline</span>
        </span>
      );
    }

    const isPositive = pct > 0;
    const isNegative = pct < 0;

    return (
      <span
        className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold ${
          isPositive
            ? 'bg-[var(--green-50)] text-[var(--green-700)] border border-[var(--green-100)]'
            : isNegative
            ? 'bg-[var(--coral-50)] text-[var(--coral-700)] border border-[var(--coral-100)]'
            : 'bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)] border border-[var(--border-subtle)]'
        }`}
      >
        {isPositive ? (
          <TrendingUp className="w-3.5 h-3.5 text-[var(--green-600)]" />
        ) : isNegative ? (
          <TrendingDown className="w-3.5 h-3.5 text-[var(--coral-600)]" />
        ) : (
          <Minus className="w-3.5 h-3.5" />
        )}
        <span>{pct > 0 ? `+${pct.toFixed(1)}%` : `${pct.toFixed(1)}%`} MoM</span>
      </span>
    );
  };

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <Activity className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Facility Utilization Signal</span>
        </div>
        <div className="text-xs text-[var(--text-muted)] font-mono">
          Latest Period: {primaryMetric.latest_reporting_month}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Dominant Primary Metric Card */}
        <div className="lg:col-span-6 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-2">
              <span>{primaryMetric.indicator_name}</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-[var(--teal-50)] text-[var(--teal-700)] font-semibold border border-[var(--teal-100)]">
                Primary Signal
              </span>
            </div>
            <div className="text-4xl sm:text-5xl font-extrabold font-display text-[var(--text-primary)] tracking-tight my-2">
              {typeof primaryMetric.latest_value === 'number' ? (
                <AnimatedNumber value={primaryMetric.latest_value} />
              ) : (
                'N/A'
              )}
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-4 mt-4 text-xs text-[var(--text-secondary)]">
            <span>Month-over-Month Shift</span>
            {getMoMBadge(primaryMetric.mom_change_pct)}
          </div>
        </div>

        {/* Supporting Secondary Indicator Cards */}
        <div className="lg:col-span-6 space-y-3 flex flex-col justify-center">
          {supportingMetrics.map((sec) => (
            <div
              key={sec.indicator_code}
              className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 flex items-center justify-between shadow-2xs hover:border-[var(--border-default)] transition-colors"
            >
              <div>
                <div className="text-xs font-semibold text-[var(--text-muted)]">
                  {sec.indicator_name}
                </div>
                <div className="text-2xl font-extrabold font-display text-[var(--text-primary)] mt-0.5">
                  {formatValue(sec.latest_value)}
                </div>
              </div>

              <div>{getMoMBadge(sec.mom_change_pct)}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
