import React from 'react';
import { ShieldCheck, CheckCircle2, AlertTriangle, AlertCircle, HelpCircle } from 'lucide-react';
import type { RegionMetricPoint } from '../../api/types';

interface RegionalReliabilityProps {
  regions: RegionMetricPoint[];
  loading: boolean;
  level: 'state' | 'district';
}

export const RegionalReliability: React.FC<RegionalReliabilityProps> = ({
  regions,
  loading,
  level,
}) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-4 w-40 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-32 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  // Sort regions by completeness percentage ascending to highlight areas with reporting gaps
  const regionsByCompleteness = [...regions].sort((a, b) => (a.completeness_pct || 0) - (b.completeness_pct || 0));

  const totalFacilities = regions.reduce((acc, r) => acc + (r.total_facilities || 0), 0);
  const totalReporting = regions.reduce((acc, r) => acc + (r.reporting_facilities || 0), 0);
  const overallCompleteness = totalFacilities > 0 ? (totalReporting / totalFacilities) * 100 : 0;

  let theme = {
    badge: 'High Governance',
    bg: 'bg-[var(--green-50)]',
    border: 'border-[var(--green-100)]',
    text: 'text-[var(--green-700)]',
    icon: CheckCircle2,
  };

  if (overallCompleteness < 60) {
    theme = {
      badge: 'Critical Data Gaps',
      bg: 'bg-[var(--coral-50)]',
      border: 'border-[var(--coral-100)]',
      text: 'text-[var(--coral-700)]',
      icon: AlertCircle,
    };
  } else if (overallCompleteness < 85) {
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
          <span>Regional Reporting Governance & Audit</span>
        </div>
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold ${theme.bg} ${theme.border} ${theme.text}`}>
          <IconComp className="w-3.5 h-3.5" />
          <span>{theme.badge}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center mb-6">
        {/* Aggregate Completeness Gauge */}
        <div className="lg:col-span-5 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-6 text-center">
          <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
            System Completeness Rate ({level === 'state' ? 'State' : 'District'})
          </div>
          <div className="text-4xl sm:text-5xl font-extrabold font-display text-[var(--text-primary)]">
            {overallCompleteness.toFixed(1)}%
          </div>
          <div className="text-xs text-[var(--text-secondary)] mt-2 font-medium">
            {totalReporting} of {totalFacilities} facilities submitting returns.
          </div>
        </div>

        {/* Region Breakdown List */}
        <div className="lg:col-span-7 space-y-2.5 max-h-48 overflow-y-auto pr-1">
          {regionsByCompleteness.map((reg) => (
            <div
              key={reg.region_name}
              className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] text-xs"
            >
              <span className="font-bold text-[var(--text-primary)]">{reg.region_name}</span>
              <div className="flex items-center gap-3">
                <span className="text-[10px] text-[var(--text-muted)] font-mono">
                  {reg.reporting_facilities}/{reg.total_facilities} Fac.
                </span>
                <span
                  className={`font-extrabold px-2 py-0.5 rounded text-[10px] ${
                    reg.completeness_pct >= 85
                      ? 'bg-[var(--green-50)] text-[var(--green-700)] border border-[var(--green-100)]'
                      : reg.completeness_pct >= 60
                      ? 'bg-[var(--amber-50)] text-[var(--amber-700)] border border-[var(--amber-100)]'
                      : 'bg-[var(--coral-50)] text-[var(--coral-700)] border border-[var(--coral-100)]'
                  }`}
                >
                  {reg.completeness_pct.toFixed(1)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Audit Notice */}
      <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-3.5 flex items-start gap-2.5 text-xs text-[var(--text-secondary)]">
        <HelpCircle className="w-4 h-4 text-[var(--teal-600)] shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-[var(--text-primary)]">Governance Policy: </span>
          Regional reporting completeness reflects facility return submission rates. High completeness ensures reliable time-series modeling, whereas incomplete returns indicate reporting gaps rather than low healthcare demand.
        </div>
      </div>
    </div>
  );
};
