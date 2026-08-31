import React from 'react';
import { Activity, Building2, ShieldCheck, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { AnimatedNumber } from '../overview/AnimatedNumber';
import type { RegionalAnalyticsResponse } from '../../api/types';

interface RegionalOverviewProps {
  data: RegionalAnalyticsResponse | null;
  loading: boolean;
}

export const RegionalOverview: React.FC<RegionalOverviewProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-4 w-44 bg-[var(--bg-surface-active)] rounded" />
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-6 h-36 bg-[var(--bg-surface-active)] rounded-xl" />
          <div className="md:col-span-6 h-36 bg-[var(--bg-surface-active)] rounded-xl" />
        </div>
      </div>
    );
  }

  const regions = data?.regions ?? [];
  const totalUtilization = regions.reduce((sum, r) => sum + (r.total_utilization || 0), 0);
  const totalFacilities = regions.reduce((sum, r) => sum + (r.total_facilities || 0), 0);
  const totalReporting = regions.reduce((sum, r) => sum + (r.reporting_facilities || 0), 0);

  const avgCompleteness = totalFacilities > 0 ? (totalReporting / totalFacilities) * 100 : 0;
  const avgPerFacility = totalReporting > 0 ? Math.round(totalUtilization / totalReporting) : 0;

  // Average MoM change across regions
  const validMoM = regions.map((r) => r.mom_change_pct).filter((v): v is number => typeof v === 'number');
  const avgMoM = validMoM.length > 0 ? validMoM.reduce((a, b) => a + b, 0) / validMoM.length : null;

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
          <span>System Regional Utilization Signal</span>
        </div>
        <div className="text-xs text-[var(--text-muted)] font-mono">
          Level: {data?.level === 'state' ? 'State Aggregation' : 'District Aggregation'}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Dominant Utilization Hero Card */}
        <div className="lg:col-span-6 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-2">
              Total Regional Attendance
            </div>
            <div className="text-4xl sm:text-5xl font-extrabold font-display text-[var(--text-primary)] tracking-tight my-2">
              <AnimatedNumber value={totalUtilization} />
            </div>
            <div className="text-xs text-[var(--text-secondary)] mt-1 font-medium">
              Sum of monthly attendance across all reporting health facilities.
            </div>
          </div>

          <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-4 mt-4 text-xs text-[var(--text-secondary)]">
            <span>Average Regional Movement</span>
            {getMoMBadge(avgMoM)}
          </div>
        </div>

        {/* Secondary Supporting Metric Cards */}
        <div className="lg:col-span-6 space-y-3 flex flex-col justify-center">
          {/* Average per Facility */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 flex items-center justify-between shadow-2xs">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--blue-50)] text-[var(--blue-700)] border border-[var(--blue-100)] flex items-center justify-center shrink-0">
                <Building2 className="w-4.5 h-4.5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[var(--text-muted)]">
                  Average Utilization per Reporting Facility
                </div>
                <div className="text-2xl font-extrabold font-display text-[var(--text-primary)] mt-0.5">
                  {avgPerFacility.toLocaleString('en-IN')}
                </div>
              </div>
            </div>
          </div>

          {/* Reporting Completeness */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 flex items-center justify-between shadow-2xs">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-[var(--green-50)] text-[var(--green-700)] border border-[var(--green-100)] flex items-center justify-center shrink-0">
                <ShieldCheck className="w-4.5 h-4.5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-[var(--text-muted)]">
                  Overall System Reporting Completeness
                </div>
                <div className="text-2xl font-extrabold font-display text-[var(--text-primary)] mt-0.5">
                  {avgCompleteness.toFixed(1)}%
                </div>
              </div>
            </div>
            <div className="text-xs text-[var(--text-muted)] font-mono font-medium">
              {totalReporting} / {totalFacilities} Facilities
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
