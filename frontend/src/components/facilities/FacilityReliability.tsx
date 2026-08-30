import React from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, AlertCircle, HelpCircle } from 'lucide-react';
import type { FacilityAnalyticsResponse } from '../../api/types';

interface FacilityReliabilityProps {
  analytics: FacilityAnalyticsResponse | null;
  loading: boolean;
}

export const FacilityReliability: React.FC<FacilityReliabilityProps> = ({ analytics, loading }) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-4 w-40 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-24 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const expectedMonths = analytics?.total_expected_months ?? 12;
  const reportedCount = analytics?.reported_months_count ?? 0;
  const missingMonths = analytics?.missing_months ?? [];
  const completenessPct = analytics?.completeness_pct ?? 0;

  // Generate monthly timeline items (e.g. 12 months)
  // Derive list of months from history or generate last 12 months sequence
  const historyMonths = Array.from(new Set(analytics?.history.map((h) => h.reporting_month) || [])).sort();

  let theme = {
    badge: 'High Integrity',
    bg: 'bg-[var(--green-50)]',
    border: 'border-[var(--green-100)]',
    text: 'text-[var(--green-700)]',
    icon: CheckCircle2,
  };

  if (completenessPct < 60) {
    theme = {
      badge: 'Critical Data Gaps',
      bg: 'bg-[var(--coral-50)]',
      border: 'border-[var(--coral-100)]',
      text: 'text-[var(--coral-700)]',
      icon: AlertCircle,
    };
  } else if (completenessPct < 85) {
    theme = {
      badge: 'Partial Returns',
      bg: 'bg-[var(--amber-50)]',
      border: 'border-[var(--amber-100)]',
      text: 'text-[var(--amber-700)]',
      icon: AlertTriangle,
    };
  }

  const IconComp = theme.icon;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <ShieldCheck className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Reporting Reliability & Audit Governance</span>
        </div>
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold ${theme.bg} ${theme.border} ${theme.text}`}>
          <IconComp className="w-3.5 h-3.5" />
          <span>{theme.badge}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Completeness Score Badge */}
        <div className="lg:col-span-5 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-6 text-center">
          <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
            Reporting Completeness Rate
          </div>
          <div className="text-4xl sm:text-5xl font-extrabold font-display text-[var(--text-primary)]">
            {completenessPct.toFixed(1)}%
          </div>
          <div className="text-xs text-[var(--text-secondary)] mt-2 font-medium">
            {reportedCount} of {expectedMonths} expected monthly returns ingested.
          </div>
        </div>

        {/* Reporting Timeline Matrix (● / ○) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="text-xs font-bold text-[var(--text-primary)] mb-2 flex items-center justify-between">
            <span>Reporting Timeline Matrix</span>
            <span className="text-[10px] text-[var(--text-muted)] font-mono">
              Expected Target: {expectedMonths} Months
            </span>
          </div>

          <div className="grid grid-cols-6 sm:grid-cols-12 gap-2">
            {historyMonths.slice(0, 12).map((m) => {
              const isMissing = missingMonths.includes(m);
              return (
                <div
                  key={m}
                  className={`p-2 rounded-lg border text-center transition-all ${
                    isMissing
                      ? 'bg-[var(--amber-50)] border-[var(--amber-200)] text-[var(--amber-800)]'
                      : 'bg-[var(--green-50)] border-[var(--green-100)] text-[var(--green-700)]'
                  }`}
                  title={isMissing ? `${m}: Missing Return` : `${m}: Verified Observation`}
                >
                  <div className="text-[14px] font-bold leading-none mb-1">
                    {isMissing ? '○' : '●'}
                  </div>
                  <div className="text-[9px] font-mono font-semibold truncate">
                    {m.split('-')[1]}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Governance Notice */}
          <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-3.5 flex items-start gap-2.5 text-xs text-[var(--text-secondary)]">
            <HelpCircle className="w-4 h-4 text-[var(--teal-600)] shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-[var(--text-primary)]">Audit Principle: </span>
              A missing reporting period (○) indicates an unverified data return, NOT zero patient activity. Reporting quality and patient utilization are distinct operational vectors.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
