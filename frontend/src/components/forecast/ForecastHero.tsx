import React from 'react';
import { Award, ShieldCheck, Zap } from 'lucide-react';
import type { ForecastResponse } from '../../api/types';

interface ForecastHeroProps {
  data: ForecastResponse;
}

export const ForecastHero: React.FC<ForecastHeroProps> = ({ data }) => {
  if (data.status !== 'SUCCESS') return null;

  const modelName = data.model?.model_type || 'Winning Forecaster';
  const isBaseline = data.model?.is_baseline ?? false;
  const validationMae = data.validation_metrics?.mae ?? 0;
  const impPct = data.improvement_over_baseline_pct ?? 0;
  const strongestBaseline = data.baseline_metrics?.strongest_baseline_name || 'Baseline';
  const horizon = data.forecast_horizon;
  const points = data.forecast_points || [];

  const totalForecastDemand = points.reduce((sum, p) => sum + p.predicted_value, 0);
  const avgMonthlyDemand = points.length > 0 ? totalForecastDemand / points.length : 0;

  return (
    <div className="bg-[var(--purple-950)] text-white rounded-3xl p-6 sm:p-8 shadow-xl mb-8 relative overflow-hidden">
      {/* Background Decorative Gradient Blobs */}
      <div className="absolute -top-24 -right-24 w-96 h-96 bg-[var(--purple-600)]/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-[var(--teal-500)]/15 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column: Model Winner Narrative */}
        <div className="lg:col-span-7 space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--purple-900)] border border-[var(--purple-700)] text-[var(--purple-200)] text-xs font-bold uppercase tracking-wider">
            <Award className="w-4 h-4 text-[var(--purple-400)]" />
            <span>Winning Model: {modelName}</span>
            {isBaseline && <span className="bg-[var(--amber-500)] text-gray-900 text-[10px] px-1.5 py-0.5 rounded font-black">BASELINE</span>}
          </div>

          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white leading-tight">
            {isBaseline
              ? `Mandatory Baseline '${modelName}' Outperformed Complex Candidates`
              : `Candidate '${modelName}' Achieved Superior Validation Accuracy`}
          </h2>

          <p className="text-sm text-[var(--purple-200)] leading-relaxed max-w-2xl">
            {data.explainability?.selection_rationale ||
              `Evaluated against 4 mandatory baselines and 4 machine learning models using time-aware chronological validation splits.`}
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <div className="flex items-center gap-1.5 text-xs text-[var(--purple-200)] bg-[var(--purple-900)]/60 px-3 py-1.5 rounded-xl border border-[var(--purple-800)]">
              <ShieldCheck className="w-4 h-4 text-[var(--teal-400)]" />
              <span>95% Residual Prediction Band</span>
            </div>

            <div className="flex items-center gap-1.5 text-xs text-[var(--purple-200)] bg-[var(--purple-900)]/60 px-3 py-1.5 rounded-xl border border-[var(--purple-800)]">
              <Zap className="w-4 h-4 text-[var(--amber-400)]" />
              <span>Zero Data Leakage Split</span>
            </div>
          </div>
        </div>

        {/* Right Column: Hero Metrics Grid */}
        <div className="lg:col-span-5 grid grid-cols-2 gap-3">
          {/* Metric 1: Total Horizon Demand */}
          <div className="bg-[var(--purple-900)]/50 backdrop-blur-xs border border-[var(--purple-800)] rounded-2xl p-4 text-center">
            <span className="block text-[10px] font-extrabold uppercase tracking-wider text-[var(--purple-300)]">
              {horizon}-Month Total Forecast
            </span>
            <span className="text-2xl sm:text-3xl font-black text-white mt-1 block">
              {Math.round(totalForecastDemand).toLocaleString()}
            </span>
            <span className="text-[10px] text-[var(--purple-300)] font-medium">
              ~{Math.round(avgMonthlyDemand).toLocaleString()} / month
            </span>
          </div>

          {/* Metric 2: Validation MAE */}
          <div className="bg-[var(--purple-900)]/50 backdrop-blur-xs border border-[var(--purple-800)] rounded-2xl p-4 text-center">
            <span className="block text-[10px] font-extrabold uppercase tracking-wider text-[var(--purple-300)]">
              Validation MAE
            </span>
            <span className="text-2xl sm:text-3xl font-black text-[var(--teal-300)] mt-1 block">
              {validationMae.toFixed(1)}
            </span>
            <span className="text-[10px] text-[var(--purple-300)] font-medium">
              Mean Absolute Error
            </span>
          </div>

          {/* Metric 3: Improvement Over Baseline */}
          <div className="bg-[var(--purple-900)]/50 backdrop-blur-xs border border-[var(--purple-800)] rounded-2xl p-4 text-center col-span-2">
            <div className="flex items-center justify-between text-xs font-bold text-[var(--purple-200)]">
              <span>Benchmark vs {strongestBaseline}:</span>
              <span className={`font-black ${impPct >= 0 ? 'text-[var(--teal-300)]' : 'text-[var(--amber-300)]'}`}>
                {impPct >= 0 ? `+${impPct.toFixed(1)}% Improvement` : `${impPct.toFixed(1)}%`}
              </span>
            </div>

            <div className="w-full bg-[var(--purple-950)] rounded-full h-2 mt-2 overflow-hidden border border-[var(--purple-800)]">
              <div
                className="bg-gradient-to-r from-[var(--teal-400)] to-[var(--blue-400)] h-full rounded-full transition-all duration-700"
                style={{ width: `${Math.min(Math.max(impPct, 10), 100)}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
