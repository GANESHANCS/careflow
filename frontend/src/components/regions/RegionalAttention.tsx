import React from 'react';
import { AlertCircle, CheckCircle2, TrendingUp, TrendingDown, ShieldAlert, ChevronRight } from 'lucide-react';
import type { RegionMetricPoint } from '../../api/types';

interface RegionalAttentionProps {
  regions: RegionMetricPoint[];
  loading: boolean;
}

export const RegionalAttention: React.FC<RegionalAttentionProps> = ({ regions, loading }) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-3">
        <div className="h-4 w-36 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-16 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const signals: { id: string; title: string; subtitle: string; type: 'warning' | 'positive' | 'info' }[] = [];

  // Identify regional signals from actual data
  regions.forEach((reg) => {
    if (reg.completeness_pct < 60) {
      signals.push({
        id: `completeness-${reg.region_name}`,
        title: `Low Reporting Completeness in ${reg.region_name}`,
        subtitle: `Only ${reg.completeness_pct.toFixed(1)}% of registered facilities submitted returns (${reg.reporting_facilities}/${reg.total_facilities}).`,
        type: 'warning',
      });
    }

    if (typeof reg.mom_change_pct === 'number') {
      if (reg.mom_change_pct >= 10) {
        signals.push({
          id: `demand-inc-${reg.region_name}`,
          title: `Rapid Attendance Expansion in ${reg.region_name}`,
          subtitle: `Month-over-month growth of +${reg.mom_change_pct.toFixed(1)}% observed across reporting outlets.`,
          type: 'positive',
        });
      } else if (reg.mom_change_pct <= -10) {
        signals.push({
          id: `demand-dec-${reg.region_name}`,
          title: `Utilization Contraction in ${reg.region_name}`,
          subtitle: `Month-over-month reduction of ${reg.mom_change_pct.toFixed(1)}% registered in latest period.`,
          type: 'warning',
        });
      }
    }
  });

  const hasSignals = signals.length > 0;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <ShieldAlert className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Regional Diagnostic Attention Flags</span>
        </div>
        <div className="text-xs text-[var(--text-muted)] font-medium">
          Automated Spatial Anomaly Stream
        </div>
      </div>

      {!hasSignals ? (
        <div className="flex items-center gap-4 p-5 rounded-xl bg-[var(--green-50)] border border-[var(--green-100)] text-[var(--green-700)]">
          <CheckCircle2 className="w-6 h-6 shrink-0 text-[var(--green-600)]" />
          <div>
            <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
              No immediate regional attention flag.
            </h4>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5 font-normal">
              All reporting jurisdictions maintain healthy completeness levels and stable utilization trajectories.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
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
