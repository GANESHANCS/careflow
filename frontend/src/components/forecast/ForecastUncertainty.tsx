import React from 'react';
import { ShieldAlert } from 'lucide-react';
import type { ForecastResponse } from '../../api/types';

interface ForecastUncertaintyProps {
  data: ForecastResponse;
}

export const ForecastUncertainty: React.FC<ForecastUncertaintyProps> = ({ data }) => {
  if (data.status !== 'SUCCESS' || !data.prediction_intervals) return null;

  const intervals = data.prediction_intervals;
  const explainability = data.explainability;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs mb-8">
      <div className="flex items-center gap-2.5 border-b border-[var(--border-subtle)] pb-4 mb-4">
        <div className="p-2 rounded-xl bg-[var(--purple-100)] text-[var(--purple-700)]">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-extrabold text-[var(--text-primary)]">
            Uncertainty & 95% Prediction Intervals
          </h3>
          <p className="text-xs text-[var(--text-muted)]">
            Quantifying predictive confidence via residual variance modeling
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <div className="p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">
            Interval Estimation Method
          </span>
          <span className="font-extrabold text-[var(--text-primary)] text-sm block">
            {intervals.interval_type || 'Residual Standard Error'}
          </span>
          <p className="text-[11px] text-[var(--text-muted)] mt-1">
            {explainability?.prediction_interval_description || 'Residual-based prediction bounds.'}
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">
            Residual Standard Deviation
          </span>
          <span className="font-mono font-extrabold text-[var(--purple-700)] text-sm block">
            {intervals.residual_std_error ? intervals.residual_std_error.toFixed(2) : 'N/A'}
          </span>
          <p className="text-[11px] text-[var(--text-muted)] mt-1">
            Standard deviation of holdout validation errors (σ_val) used for confidence scaling.
          </p>
        </div>

        <div className="p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] block">
            Horizon Variance Expansion
          </span>
          <span className="font-extrabold text-[var(--teal-700)] text-sm block">
            Multi-step Step Scaling
          </span>
          <p className="text-[11px] text-[var(--text-muted)] mt-1">
            Intervals naturally widen for distant future months (t+12 vs t+1) to reflect compounding uncertainty.
          </p>
        </div>
      </div>
    </div>
  );
};
