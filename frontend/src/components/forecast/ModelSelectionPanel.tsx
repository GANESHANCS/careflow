import React from 'react';
import { Cpu, CheckCircle, Sparkles } from 'lucide-react';
import type { ForecastResponse } from '../../api/types';

interface ModelSelectionPanelProps {
  data: ForecastResponse;
}

export const ModelSelectionPanel: React.FC<ModelSelectionPanelProps> = ({ data }) => {
  if (data.status !== 'SUCCESS' || !data.model) return null;

  const model = data.model;
  const explainability = data.explainability;
  const isBaseline = model.is_baseline;
  const validationMetrics = data.validation_metrics;
  const baselineMetrics = data.baseline_metrics;
  const impPct = data.improvement_over_baseline_pct ?? 0;
  const trainingPeriod = data.training_period;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs mb-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4 mb-5">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-[var(--purple-100)] text-[var(--purple-700)]">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)]">
              Model Selection & Baseline Primacy Governance
            </h3>
            <p className="text-xs text-[var(--text-muted)]">
              Phase 5 Time-Aware Validation & Automated Model Selection Architecture
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-xl bg-[var(--purple-50)] border border-[var(--purple-200)] text-[var(--purple-900)] text-xs font-bold self-start md:self-auto">
          <Sparkles className="w-4 h-4 text-[var(--purple-600)]" />
          <span>Model Version v{model.model_version}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Selection Rationale Narrative */}
        <div className="lg:col-span-7 space-y-4">
          <div className="p-4 rounded-xl bg-[var(--purple-50)] border border-[var(--purple-200)]">
            <div className="flex items-center gap-2 text-xs font-extrabold uppercase text-[var(--purple-900)] mb-1">
              <CheckCircle className="w-4 h-4 text-[var(--purple-600)]" />
              <span>Selection Rationale</span>
            </div>
            <p className="text-xs text-[var(--purple-950)] leading-relaxed font-medium">
              {explainability?.selection_rationale ||
                `Model '${model.model_type}' was selected based on validation error comparison against mandatory baseline benchmarks.`}
            </p>
          </div>

          <div className="text-xs text-[var(--text-muted)] space-y-2 leading-relaxed">
            <h4 className="font-bold text-[var(--text-primary)] uppercase text-[10px] tracking-wider">
              Governance Primacy Rules
            </h4>
            <ul className="list-disc list-inside space-y-1">
              <li>
                <strong>Baseline Primacy Rule:</strong> A complex machine learning candidate (e.g. SARIMAX, Ridge, Random Forest) is selected ONLY if it demonstrates a statistically meaningful validation error reduction over the strongest mandatory baseline.
              </li>
              <li>
                <strong>Tie-Breaking Protocol:</strong> If an ML candidate's validation MAE is within 1% of the strongest baseline, the simpler baseline forecaster is selected to prevent overfitting.
              </li>
              <li>
                <strong>Zero-Leakage Split:</strong> Models are trained strictly on history up to the validation cutoff, avoiding future observation leakage.
              </li>
            </ul>
          </div>
        </div>

        {/* Selected Model Details & Metrics */}
        <div className="lg:col-span-5 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-4 space-y-3 text-xs">
          <div className="flex justify-between items-center pb-2 border-b border-[var(--border-subtle)]">
            <span className="font-bold text-[var(--text-muted)] uppercase text-[10px] tracking-wider">
              Selected Model Type
            </span>
            <span className="font-extrabold text-[var(--purple-700)] text-sm">{model.model_type}</span>
          </div>

          <div className="flex justify-between items-center">
            <span className="text-[var(--text-muted)]">Model Category:</span>
            <span className={`font-extrabold ${isBaseline ? 'text-[var(--amber-700)]' : 'text-[var(--teal-700)]'}`}>
              {isBaseline ? 'Mandatory Baseline' : 'Machine Learning Candidate'}
            </span>
          </div>

          {trainingPeriod && (
            <div className="flex justify-between items-center">
              <span className="text-[var(--text-muted)]">Training Window:</span>
              <span className="font-bold text-[var(--text-primary)]">
                {trainingPeriod.start_month} → {trainingPeriod.end_month} ({trainingPeriod.total_observations} observations)
              </span>
            </div>
          )}

          {validationMetrics && (
            <div className="flex justify-between items-center">
              <span className="text-[var(--text-muted)]">Validation MAE:</span>
              <span className="font-mono font-extrabold text-[var(--text-primary)]">{validationMetrics.mae.toFixed(2)}</span>
            </div>
          )}

          {baselineMetrics && (
            <div className="flex justify-between items-center">
              <span className="text-[var(--text-muted)]">Benchmark Baseline MAE:</span>
              <span className="font-mono font-bold text-[var(--text-primary)]">
                {baselineMetrics.strongest_baseline_mae.toFixed(2)} ({baselineMetrics.strongest_baseline_name})
              </span>
            </div>
          )}

          <div className="flex justify-between items-center pt-2 border-t border-[var(--border-subtle)]">
            <span className="text-[var(--text-muted)]">Validation Improvement:</span>
            <span className={`font-mono font-extrabold ${impPct >= 0 ? 'text-[var(--teal-700)]' : 'text-[var(--amber-700)]'}`}>
              {impPct >= 0 ? `+${impPct.toFixed(1)}%` : `${impPct.toFixed(1)}%`}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
