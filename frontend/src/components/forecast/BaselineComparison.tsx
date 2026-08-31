import React from 'react';
import { Trophy, Shield, Check } from 'lucide-react';
import type { CandidateEvaluation, ForecastResponse } from '../../api/types';

interface BaselineComparisonProps {
  data: ForecastResponse;
}

export const BaselineComparison: React.FC<BaselineComparisonProps> = ({ data }) => {
  if (data.status !== 'SUCCESS') return null;

  const candidates: CandidateEvaluation[] = data.candidate_evaluations || [];
  if (candidates.length === 0) return null;

  const selectedModelName = data.model?.model_type;
  const strongestBaselineName = data.baseline_metrics?.strongest_baseline_name;

  // Sort candidates by MAE ascending
  const sortedCandidates = [...candidates].sort((a, b) => a.mae - b.mae);
  const lowestMae = sortedCandidates.length > 0 ? sortedCandidates[0].mae : 1;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--purple-700)] mb-1">
            <Trophy className="w-4 h-4 text-[var(--purple-600)]" />
            <span>Candidate Model Tournament Benchmark</span>
          </div>
          <h3 className="text-base font-extrabold text-[var(--text-primary)]">
            Chronological Validation Metrics Across Candidates
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Evaluated on holdout validation split. Lower error metrics indicate superior forecast accuracy.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[var(--purple-100)] text-[var(--purple-800)] font-bold">
            <Check className="w-3.5 h-3.5" />
            Selected Winner
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[var(--teal-100)] text-[var(--teal-800)] font-bold">
            <Shield className="w-3.5 h-3.5" />
            Strongest Baseline
          </span>
        </div>
      </div>

      {/* Candidate Benchmark Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="border-b border-[var(--border-subtle)] text-[10px] font-extrabold uppercase text-[var(--text-muted)] tracking-wider">
              <th className="py-2.5 px-3">Candidate Model</th>
              <th className="py-2.5 px-3">Type</th>
              <th className="py-2.5 px-3 text-right">MAE (Val Error)</th>
              <th className="py-2.5 px-3 text-right">RMSE</th>
              <th className="py-2.5 px-3 text-right">sMAPE (%)</th>
              <th className="py-2.5 px-3 text-right">WAPE (%)</th>
              <th className="py-2.5 px-3 text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {sortedCandidates.map((c) => {
              const isSelected = c.model_name === selectedModelName;
              const isStrongestBaseline = c.model_name === strongestBaselineName;
              const relativeBarWidth = Math.min(100, Math.max(15, (lowestMae / (c.mae + 1e-6)) * 100));

              return (
                <tr
                  key={c.model_name}
                  className={`border-b border-[var(--border-subtle)]/60 transition-colors ${
                    isSelected
                      ? 'bg-[var(--purple-50)]/80 font-bold'
                      : isStrongestBaseline
                      ? 'bg-[var(--teal-50)]/50'
                      : 'hover:bg-[var(--bg-surface-subtle)]'
                  }`}
                >
                  <td className="py-3 px-3 font-semibold text-[var(--text-primary)] flex items-center gap-2">
                    <span>{c.model_name}</span>
                    {isSelected && (
                      <span className="px-2 py-0.5 rounded-full bg-[var(--purple-600)] text-white text-[9px] font-black uppercase tracking-wider">
                        WINNER
                      </span>
                    )}
                    {isStrongestBaseline && !isSelected && (
                      <span className="px-2 py-0.5 rounded-full bg-[var(--teal-600)] text-white text-[9px] font-black uppercase tracking-wider">
                        BENCHMARK
                      </span>
                    )}
                  </td>

                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        c.is_baseline
                          ? 'bg-gray-100 text-gray-700 border border-gray-200'
                          : 'bg-[var(--purple-100)] text-[var(--purple-800)]'
                      }`}
                    >
                      {c.is_baseline ? 'Baseline' : 'ML Candidate'}
                    </span>
                  </td>

                  <td className="py-3 px-3 text-right font-mono font-extrabold">
                    <div className="flex items-center justify-end gap-2">
                      <span>{c.mae.toFixed(2)}</span>
                      <div className="w-16 bg-gray-200 h-1.5 rounded-full overflow-hidden hidden sm:block">
                        <div
                          className={`h-full rounded-full ${
                            isSelected ? 'bg-[var(--purple-600)]' : 'bg-[var(--teal-600)]'
                          }`}
                          style={{ width: `${relativeBarWidth}%` }}
                        />
                      </div>
                    </div>
                  </td>

                  <td className="py-3 px-3 text-right font-mono text-[var(--text-muted)]">
                    {c.rmse.toFixed(2)}
                  </td>

                  <td className="py-3 px-3 text-right font-mono text-[var(--text-muted)]">
                    {(c.smape * 100).toFixed(1)}%
                  </td>

                  <td className="py-3 px-3 text-right font-mono text-[var(--text-muted)]">
                    {(c.wape * 100).toFixed(1)}%
                  </td>

                  <td className="py-3 px-3 text-center">
                    {isSelected ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-black text-[var(--purple-700)]">
                        <Check className="w-3.5 h-3.5" /> Selected
                      </span>
                    ) : isStrongestBaseline ? (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[var(--teal-700)]">
                        <Shield className="w-3.5 h-3.5" /> Baseline
                      </span>
                    ) : (
                      <span className="text-[10px] text-[var(--text-muted)]">Evaluated</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
