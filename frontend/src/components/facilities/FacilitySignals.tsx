import React from 'react';
import { AlertCircle, CheckCircle2, TrendingUp, TrendingDown, ShieldAlert, ChevronRight } from 'lucide-react';
import type { FacilityAnalyticsResponse } from '../../api/types';

interface FacilitySignalsProps {
  analytics: FacilityAnalyticsResponse | null;
  loading: boolean;
}

export const FacilitySignals: React.FC<FacilitySignalsProps> = ({ analytics, loading }) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-3">
        <div className="h-4 w-36 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-16 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const signals: { id: string; title: string; subtitle: string; type: 'warning' | 'positive' | 'info' }[] = [];

  if (analytics) {
    // 1. Missing reporting gap signal
    if (analytics.missing_months && analytics.missing_months.length > 0) {
      signals.push({
        id: 'missing-gaps',
        title: `Reporting Gap Detected (${analytics.missing_months.length} Months Missing)`,
        subtitle: `Monthly observations missing for: ${analytics.missing_months.slice(0, 3).join(', ')}${analytics.missing_months.length > 3 ? '...' : ''}`,
        type: 'warning',
      });
    }

    // 2. MoM trend movement signals
    const primaryMetric = analytics.latest_metrics.find((m) => typeof m.mom_change_pct === 'number');
    if (primaryMetric && primaryMetric.mom_change_pct !== null) {
      if (primaryMetric.mom_change_pct >= 5) {
        signals.push({
          id: 'demand-increasing',
          title: `Increasing Demand (${primaryMetric.indicator_name})`,
          subtitle: `Month-over-month increase of +${primaryMetric.mom_change_pct.toFixed(1)}% observed in latest reporting period.`,
          type: 'positive',
        });
      } else if (primaryMetric.mom_change_pct <= -5) {
        signals.push({
          id: 'demand-declining',
          title: `Declining Attendance (${primaryMetric.indicator_name})`,
          subtitle: `Month-over-month reduction of ${primaryMetric.mom_change_pct.toFixed(1)}% observed in latest reporting period.`,
          type: 'warning',
        });
      }
    }

    // 3. Insufficient history signal
    if (analytics.reported_months_count < 6) {
      signals.push({
        id: 'insufficient-history',
        title: 'Limited Historical Observations',
        subtitle: `Facility has only ${analytics.reported_months_count} reported months, below recommended 12-month baseline.`,
        type: 'info',
      });
    }
  }

  const hasSignals = signals.length > 0;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <ShieldAlert className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Operational Signals & Diagnostic Flags</span>
        </div>
        <div className="text-xs text-[var(--text-muted)] font-medium">
          Automated Telemetry Diagnostic
        </div>
      </div>

      {!hasSignals ? (
        <div className="flex items-center gap-4 p-5 rounded-xl bg-[var(--green-50)] border border-[var(--green-100)] text-[var(--green-700)]">
          <CheckCircle2 className="w-6 h-6 shrink-0 text-[var(--green-600)]" />
          <div>
            <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
              No immediate operational signal.
            </h4>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5 font-normal">
              Attendance levels remain stable across recent months and no unexpected reporting gaps were detected.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {signals.map((sig) => (
            <div
              key={sig.id}
              className={`flex items-start justify-between p-4 rounded-xl border transition-all ${
                sig.type === 'positive'
                  ? 'bg-[var(--green-50)] border-[var(--green-100)] text-[var(--green-700)]'
                  : sig.type === 'warning'
                  ? 'bg-[var(--amber-50)] border-[var(--amber-100)] text-[var(--amber-700)]'
                  : 'bg-[var(--blue-50)] border-[var(--blue-100)] text-[var(--blue-700)]'
              }`}
            >
              <div className="flex items-start gap-3">
                {sig.type === 'positive' ? (
                  <TrendingUp className="w-5 h-5 shrink-0 text-[var(--green-600)] mt-0.5" />
                ) : sig.type === 'warning' ? (
                  <AlertCircle className="w-5 h-5 shrink-0 text-[var(--amber-600)] mt-0.5" />
                ) : (
                  <TrendingDown className="w-5 h-5 shrink-0 text-[var(--blue-600)] mt-0.5" />
                )}
                <div>
                  <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
                    {sig.title}
                  </h4>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5 font-normal">
                    {sig.subtitle}
                  </p>
                </div>
              </div>

              <ChevronRight className="w-4 h-4 text-[var(--text-muted)] shrink-0 self-center" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
