import React from 'react';
import { Activity, TrendingUp, ShieldCheck, CheckCircle2 } from 'lucide-react';
import type { ForecastResponse } from '../../api/types';

interface ForecastSignalsProps {
  data: ForecastResponse;
}

export const ForecastSignals: React.FC<ForecastSignalsProps> = ({ data }) => {
  if (data.status !== 'SUCCESS') return null;

  const points = data.forecast_points || [];
  const historical = data.historical_points || [];
  const model = data.model;
  const validationMae = data.validation_metrics?.mae ?? 0;

  // Calculate demand trend direction over forecast horizon
  let trendSignal = 'STABLE DEMAND';
  let trendDesc = 'Projected monthly attendance remains consistent with historical baselines.';
  let trendColor = 'text-[var(--teal-700)] bg-[var(--teal-50)] border-[var(--teal-200)]';

  if (points.length >= 2) {
    const firstP = points[0].predicted_value;
    const lastP = points[points.length - 1].predicted_value;
    const pctChange = firstP > 0 ? ((lastP - firstP) / firstP) * 100 : 0;

    if (pctChange >= 8) {
      trendSignal = `RISING DEMAND SHIFT (+${pctChange.toFixed(1)}%)`;
      trendDesc = `Expected attendance increases by ${pctChange.toFixed(1)}% over the ${data.forecast_horizon}-month horizon. Consider capacity scaling.`;
      trendColor = 'text-[var(--purple-800)] bg-[var(--purple-50)] border-[var(--purple-200)]';
    } else if (pctChange <= -8) {
      trendSignal = `DECLINING DEMAND SHIFT (${pctChange.toFixed(1)}%)`;
      trendDesc = `Expected attendance decreases by ${Math.abs(pctChange).toFixed(1)}% over the horizon. Verify regional referral patterns.`;
      trendColor = 'text-[var(--blue-800)] bg-[var(--blue-50)] border-[var(--blue-200)]';
    }
  }

  // Completeness signal
  const validHistCount = historical.filter((h) => !h.is_missing).length;
  const histCompletenessPct = historical.length > 0 ? (validHistCount / historical.length) * 100 : 100;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs mb-8">
      <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-4 mb-4">
        <Activity className="w-5 h-5 text-[var(--purple-600)]" />
        <div>
          <h3 className="text-base font-extrabold text-[var(--text-primary)]">
            Operational Diagnostic & Forecast Signals
          </h3>
          <p className="text-xs text-[var(--text-muted)]">
            Actionable insights derived from backend time-series model evaluation
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        {/* Signal 1: Demand Trend */}
        <div className={`p-4 rounded-xl border ${trendColor} space-y-1.5`}>
          <div className="flex items-center justify-between">
            <span className="font-extrabold text-[10px] uppercase tracking-wider">Demand Trajectory</span>
            <TrendingUp className="w-4 h-4 opacity-80" />
          </div>
          <h4 className="font-bold text-sm">{trendSignal}</h4>
          <p className="text-[11px] leading-relaxed opacity-90">{trendDesc}</p>
        </div>

        {/* Signal 2: Model Confidence */}
        <div className="p-4 rounded-xl border text-[var(--purple-900)] bg-[var(--purple-50)] border-[var(--purple-200)] space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-extrabold text-[10px] uppercase tracking-wider text-[var(--purple-800)]">
              Model Reliability
            </span>
            <ShieldCheck className="w-4 h-4 text-[var(--purple-600)]" />
          </div>
          <h4 className="font-bold text-sm">{model?.model_type || 'Model Selected'}</h4>
          <p className="text-[11px] leading-relaxed text-[var(--purple-950)]">
            Validation MAE of {validationMae.toFixed(1)}. Evaluated with zero-leakage chronological split.
          </p>
        </div>

        {/* Signal 3: Reporting Quality */}
        <div className="p-4 rounded-xl border text-[var(--teal-900)] bg-[var(--teal-50)] border-[var(--teal-200)] space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="font-extrabold text-[10px] uppercase tracking-wider text-[var(--teal-800)]">
              Historical Integrity
            </span>
            <CheckCircle2 className="w-4 h-4 text-[var(--teal-600)]" />
          </div>
          <h4 className="font-bold text-sm">{histCompletenessPct.toFixed(1)}% Reporting Completeness</h4>
          <p className="text-[11px] leading-relaxed text-[var(--teal-950)]">
            Based on {validHistCount} valid monthly observations across historical reporting records.
          </p>
        </div>
      </div>
    </div>
  );
};
