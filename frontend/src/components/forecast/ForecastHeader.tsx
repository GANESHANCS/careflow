import React from 'react';
import { TrendingUp, Calendar, Building2, Activity, ShieldCheck } from 'lucide-react';
import type { Facility, Indicator } from '../../api/types';

interface ForecastHeaderProps {
  selectedFacility: Facility | null;
  selectedIndicator: Indicator | null;
  horizon: number;
  latestHistoricalMonth?: string | null;
  modelType?: string | null;
  isEligible?: boolean;
}

export const ForecastHeader: React.FC<ForecastHeaderProps> = ({
  selectedFacility,
  selectedIndicator,
  horizon,
  latestHistoricalMonth,
  modelType,
  isEligible = false,
}) => {
  return (
    <div className="mb-8 border-b border-[var(--border-subtle)] pb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[var(--purple-700)] mb-1">
            <TrendingUp className="w-4 h-4 text-[var(--purple-600)]" />
            <span>CAREFlow / Forecast Intelligence Workspace</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-primary)] tracking-tight">
            Demand Forecasting & Predictive Capacity
          </h1>
          <p className="text-sm sm:text-base text-[var(--text-muted)] mt-1 max-w-3xl leading-relaxed">
            Anticipate healthcare service demand before it arrives. CAREFlow uses historical HMIS monthly utilization patterns to evaluate candidate time-series models and forecast future attendance with ~95% prediction intervals.
          </p>
        </div>

        {/* Disclaimer / Synthetic Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[var(--purple-50)] border border-[var(--purple-200)] text-[var(--purple-800)] text-xs font-semibold self-start lg:self-auto">
          <ShieldCheck className="w-4 h-4 text-[var(--purple-600)] flex-shrink-0" />
          <span>Synthetic Development Framework</span>
        </div>
      </div>

      {/* Selected Scope Badges */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] font-medium text-[var(--text-primary)]">
          <Building2 className="w-3.5 h-3.5 text-[var(--teal-600)]" />
          <span className="text-[var(--text-muted)]">Facility:</span>
          <span className="font-bold">{selectedFacility ? selectedFacility.facility_name : 'No Facility Selected'}</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] font-medium text-[var(--text-primary)]">
          <Activity className="w-3.5 h-3.5 text-[var(--purple-600)]" />
          <span className="text-[var(--text-muted)]">Indicator:</span>
          <span className="font-bold">{selectedIndicator ? `${selectedIndicator.name} (${selectedIndicator.code})` : 'OPD Attendance'}</span>
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] font-medium text-[var(--text-primary)]">
          <Calendar className="w-3.5 h-3.5 text-[var(--blue-600)]" />
          <span className="text-[var(--text-muted)]">Horizon:</span>
          <span className="font-bold">{horizon} Months</span>
        </div>

        {latestHistoricalMonth && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] font-medium text-[var(--text-primary)]">
            <span className="text-[var(--text-muted)]">Latest History:</span>
            <span className="font-bold">{latestHistoricalMonth}</span>
          </div>
        )}

        {modelType && isEligible && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[var(--purple-100)] text-[var(--purple-900)] font-bold">
            <span>Model:</span>
            <span>{modelType}</span>
          </div>
        )}
      </div>
    </div>
  );
};
