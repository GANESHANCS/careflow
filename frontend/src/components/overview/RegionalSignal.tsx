import React from 'react';
import { MapPin, TrendingUp, TrendingDown, Building2, Layers, Compass } from 'lucide-react';
import type { RegionalAnalyticsResponse, RegionMetricPoint } from '../../api/types';
import { AnimatedNumber } from './AnimatedNumber';

interface RegionalSignalProps {
  data: RegionalAnalyticsResponse | null;
  loading: boolean;
  activeLevel: 'state' | 'district';
  onLevelChange: (level: 'state' | 'district') => void;
}

export const RegionalSignal: React.FC<RegionalSignalProps> = ({
  data,
  loading,
  activeLevel,
  onLevelChange,
}) => {
  const regions = data?.regions ?? [];
  const hasData = regions.length > 0;

  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse">
        <div className="h-4 w-40 bg-[var(--bg-surface-active)] rounded mb-4" />
        <div className="space-y-3">
          <div className="h-12 bg-[var(--bg-surface-active)] rounded-xl" />
          <div className="h-12 bg-[var(--bg-surface-active)] rounded-xl" />
          <div className="h-12 bg-[var(--bg-surface-active)] rounded-xl" />
        </div>
      </div>
    );
  }

  const maxUtilization = Math.max(...regions.map((r) => r.total_utilization), 1);

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Header and Level Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
            <Compass className="w-4 h-4 text-[var(--teal-600)]" />
            <span>Regional Signal & Spatial Intelligence</span>
          </div>
          <h3 className="font-display font-extrabold text-xl text-[var(--text-primary)] tracking-tight mt-0.5">
            Regional Utilization Rankings
          </h3>
          <p className="text-xs text-[var(--text-secondary)] font-normal">
            Comparative throughput and facility completeness across operational jurisdictions
          </p>
        </div>

        {/* Aggregation Level Toggle */}
        <div className="inline-flex items-center p-1 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-default)]">
          <button
            onClick={() => onLevelChange('state')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeLevel === 'state'
                ? 'bg-[var(--bg-surface)] text-[var(--teal-700)] shadow-2xs font-bold'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
            aria-label="View state-level aggregations"
          >
            STATE
          </button>
          <button
            onClick={() => onLevelChange('district')}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeLevel === 'district'
                ? 'bg-[var(--bg-surface)] text-[var(--teal-700)] shadow-2xs font-bold'
                : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
            aria-label="View district-level aggregations"
          >
            DISTRICT
          </button>
        </div>
      </div>

      {!hasData ? (
        <div className="p-8 text-center border border-dashed border-[var(--border-subtle)] rounded-xl">
          <MapPin className="w-8 h-8 text-[var(--text-subtle)] mx-auto mb-2" />
          <h4 className="text-sm font-bold text-[var(--text-primary)]">No Regional Observations Recorded</h4>
          <p className="text-xs text-[var(--text-muted)] mt-1 max-w-sm mx-auto">
            Regional utilization signals will render automatically when facility returns with valid state/district tags are ingested.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {regions.map((region: RegionMetricPoint, idx: number) => {
            const pct = Math.min((region.total_utilization / maxUtilization) * 100, 100);

            return (
              <div
                key={`${region.region_name}-${idx}`}
                className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-4 transition-transform duration-150 hover:-translate-y-0.5 hover:border-[var(--teal-500)] shadow-2xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-[var(--teal-100)] text-[var(--teal-700)] font-bold text-[10px] flex items-center justify-center">
                      {idx + 1}
                    </span>
                    <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
                      {region.region_name}
                    </h4>
                  </div>

                  <div className="flex items-center gap-4 text-xs font-semibold text-[var(--text-secondary)]">
                    <span className="flex items-center gap-1 text-[var(--text-muted)]">
                      <Building2 className="w-3.5 h-3.5 text-[var(--teal-600)]" />
                      <span>{region.reporting_facilities} / {region.total_facilities} Outlets</span>
                    </span>
                    <span className="flex items-center gap-1 text-[var(--text-muted)]">
                      <Layers className="w-3.5 h-3.5 text-[var(--blue-600)]" />
                      <span>{region.completeness_pct}% Complete</span>
                    </span>
                    {region.mom_change_pct !== null && (
                      <span
                        className={`inline-flex items-center gap-0.5 font-bold ${
                          region.mom_change_pct >= 0 ? 'text-[var(--green-700)]' : 'text-[var(--coral-700)]'
                        }`}
                      >
                        {region.mom_change_pct >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                        <span>{region.mom_change_pct >= 0 ? `+${region.mom_change_pct.toFixed(1)}%` : `${region.mom_change_pct.toFixed(1)}%`}</span>
                      </span>
                    )}
                  </div>
                </div>

                {/* Progress Bar Container */}
                <div className="w-full bg-[var(--border-subtle)] h-2 rounded-full overflow-hidden flex items-center">
                  <div
                    className="bg-gradient-to-r from-[var(--teal-600)] to-[var(--blue-600)] h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)] mt-2 font-medium">
                  <span>Total Utilization: <strong className="text-[var(--text-primary)]"><AnimatedNumber value={region.total_utilization} /></strong></span>
                  <span>Avg / Facility: <strong className="text-[var(--text-primary)]">{Math.round(region.average_per_reporting_facility).toLocaleString('en-IN')}</strong></span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
