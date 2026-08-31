import React from 'react';
import { PieChart, CheckCircle2, MinusCircle, AlertCircle, Sparkles, HelpCircle, Info } from 'lucide-react';
import type { DataQualityAnalyticsResponse } from '../../api/types';

interface QualityBreakdownProps {
  data: DataQualityAnalyticsResponse | null;
}

export const QualityBreakdown: React.FC<QualityBreakdownProps> = ({ data }) => {
  const breakdown = data?.observation_breakdown;
  const total = breakdown?.total_observations ?? 0;

  const valid = breakdown?.valid_count ?? 0;
  const zero = breakdown?.zero_count ?? 0;
  const missing = breakdown?.missing_count ?? 0;
  const invalid = breakdown?.invalid_count ?? 0;
  const imputed = breakdown?.imputed_count ?? 0;

  const getPct = (val: number) => (total > 0 ? ((val / total) * 100).toFixed(1) : '0.0');

  const categories = [
    {
      key: 'VALID',
      label: 'Valid Non-Zero',
      count: valid,
      pct: getPct(valid),
      color: 'bg-[var(--teal-600)]',
      textColor: 'text-[var(--teal-700)]',
      bgColor: 'bg-[var(--teal-50)]',
      borderColor: 'border-[var(--teal-200)]',
      icon: CheckCircle2,
      description: 'Confirmed positive healthcare observations meeting validation schema.',
    },
    {
      key: 'ZERO',
      label: 'Reported Zero (0)',
      count: zero,
      pct: getPct(zero),
      color: 'bg-[var(--blue-600)]',
      textColor: 'text-[var(--blue-700)]',
      bgColor: 'bg-[var(--blue-50)]',
      borderColor: 'border-[var(--blue-200)]',
      icon: MinusCircle,
      description: 'Confirmed zero healthcare count reported by facility. Valid observation.',
    },
    {
      key: 'MISSING',
      label: 'Unreported (Missing)',
      count: missing,
      pct: getPct(missing),
      color: 'bg-[var(--coral-500)]',
      textColor: 'text-[var(--coral-700)]',
      bgColor: 'bg-[var(--coral-50)]',
      borderColor: 'border-[var(--coral-200)]',
      icon: HelpCircle,
      description: 'Monthly observation cell left blank or unsubmitted. Preserved as NULL.',
    },
    {
      key: 'INVALID',
      label: 'Out of Range / Invalid',
      count: invalid,
      pct: getPct(invalid),
      color: 'bg-[var(--amber-500)]',
      textColor: 'text-[var(--amber-700)]',
      bgColor: 'bg-[var(--amber-50)]',
      borderColor: 'border-[var(--amber-200)]',
      icon: AlertCircle,
      description: 'Flagged for negative count or unparseable non-numeric character strings.',
    },
    {
      key: 'IMPUTED',
      label: 'Algorithmic Imputations',
      count: imputed,
      pct: getPct(imputed),
      color: 'bg-[var(--purple-600)]',
      textColor: 'text-[var(--purple-700)]',
      bgColor: 'bg-[var(--purple-50)]',
      borderColor: 'border-[var(--purple-200)]',
      icon: Sparkles,
      description: 'Values derived via time-series imputation. Explicitly tracked for auditability.',
    },
  ];

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2 font-display">
            <PieChart className="w-5 h-5 text-[var(--teal-600)]" />
            Observation Classification Breakdown
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Strict preservation of semantic observation states across ingested HMIS returns.
          </p>
        </div>

        {total > 0 && (
          <div className="px-3 py-1 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] text-xs font-mono font-bold text-[var(--text-primary)] self-start sm:self-auto">
            {total.toLocaleString()} Total Records
          </div>
        )}
      </div>

      {/* Proportional Stacked Progress Bar */}
      {total > 0 ? (
        <div className="mb-6 space-y-2">
          <div className="w-full bg-[var(--bg-surface-subtle)] h-4 rounded-xl overflow-hidden flex border border-[var(--border-subtle)] p-0.5 gap-0.5">
            {categories.map(
              (cat) =>
                cat.count > 0 && (
                  <div
                    key={cat.key}
                    className={`h-full ${cat.color} transition-all duration-700 rounded-xs`}
                    style={{ width: `${cat.pct}%` }}
                    title={`${cat.label}: ${cat.count.toLocaleString()} (${cat.pct}%)`}
                  />
                )
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-6 text-xs text-[var(--text-muted)] font-mono">
          No raw observation data loaded in current pipeline database.
        </div>
      )}

      {/* Categories Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
        {categories.map((cat) => {
          const Icon = cat.icon;
          return (
            <div
              key={cat.key}
              className={`rounded-2xl p-4 border ${cat.borderColor} ${cat.bgColor} flex flex-col justify-between`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-xs font-bold ${cat.textColor} flex items-center gap-1.5`}>
                    <Icon className="w-3.5 h-3.5 shrink-0" />
                    {cat.label}
                  </span>
                </div>

                <div className="text-2xl font-extrabold text-[var(--text-primary)] font-mono">
                  {cat.count.toLocaleString()}
                </div>

                <span className="text-xs font-bold text-[var(--text-muted)] font-mono block mt-0.5">
                  {cat.pct}% of total
                </span>
              </div>

              <p className="text-[10px] text-[var(--text-muted)] mt-3 leading-relaxed border-t border-[var(--border-subtle)] pt-2">
                {cat.description}
              </p>
            </div>
          );
        })}
      </div>

      {/* Governance Rule Reminder */}
      <div className="mt-6 bg-[var(--purple-50)] border border-[var(--purple-200)] rounded-2xl p-4 text-xs text-[var(--purple-900)] leading-relaxed flex items-start gap-2.5">
        <Info className="w-4 h-4 text-[var(--purple-600)] shrink-0 mt-0.5" />
        <div>
          <span className="font-bold block text-[var(--purple-950)] mb-0.5">
            Strict Governance Rule: Unreported (MISSING) $\neq$ Reported Zero (0)
          </span>
          CAREFlow never imputes missing monthly returns as zero (0). Zero represents confirmed zero patient visits, while missing represents an unsubmitted monthly report. Imputed records remain explicitly flagged for provenance tracking.
        </div>
      </div>
    </div>
  );
};
