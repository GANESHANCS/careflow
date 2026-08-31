import React from 'react';
import { AlertTriangle, AlertCircle, Info, ShieldAlert, Filter } from 'lucide-react';
import type { DataQualityAnalyticsResponse } from '../../api/types';

interface IssueDistributionProps {
  data: DataQualityAnalyticsResponse | null;
  selectedSeverity?: string;
  onSelectSeverity?: (sev: string) => void;
}

export const IssueDistribution: React.FC<IssueDistributionProps> = ({
  data,
  selectedSeverity = 'ALL',
  onSelectSeverity,
}) => {
  const severityCounts = data?.severity_counts || {};
  const categoryCounts = data?.category_counts || {};
  const totalIssues = data?.total_issues || 0;

  const critical = severityCounts['CRITICAL'] || 0;
  const error = severityCounts['ERROR'] || 0;
  const warning = severityCounts['WARNING'] || 0;
  const info = severityCounts['INFO'] || 0;

  const severities = [
    {
      key: 'CRITICAL',
      label: 'Critical Risk',
      count: critical,
      color: 'text-[var(--coral-700)]',
      bgColor: 'bg-[var(--coral-50)]',
      borderColor: 'border-[var(--coral-300)]',
      barColor: 'bg-[var(--coral-600)]',
      icon: ShieldAlert,
      desc: 'Impossible negative values or corrupt source files requiring immediate pipeline fix.',
    },
    {
      key: 'ERROR',
      label: 'Error Impact',
      count: error,
      color: 'text-[var(--coral-800)]',
      bgColor: 'bg-[var(--coral-100)]',
      borderColor: 'border-[var(--coral-300)]',
      barColor: 'bg-[var(--coral-700)]',
      icon: AlertCircle,
      desc: 'High missingness (>15%) or unparseable non-numeric cell formatting.',
    },
    {
      key: 'WARNING',
      label: 'Warning Flag',
      count: warning,
      color: 'text-[var(--amber-700)]',
      bgColor: 'bg-[var(--amber-50)]',
      borderColor: 'border-[var(--amber-300)]',
      barColor: 'bg-[var(--amber-500)]',
      icon: AlertTriangle,
      desc: 'Extreme statistical outliers (>5x IQR) or temporal facility reporting gaps.',
    },
    {
      key: 'INFO',
      label: 'Informational',
      count: info,
      color: 'text-[var(--blue-700)]',
      bgColor: 'bg-[var(--blue-50)]',
      borderColor: 'border-[var(--blue-200)]',
      barColor: 'bg-[var(--blue-600)]',
      icon: Info,
      desc: 'Composite facility identifier assignment or header catalog alias mapping.',
    },
  ];

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2 font-display">
            <AlertTriangle className="w-5 h-5 text-[var(--coral-600)]" />
            13-Point Pipeline Issue Severity & Category Distribution
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Audit logs generated across HMIS ingestion, schema validation, and missingness routines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-[var(--text-muted)] flex items-center gap-1">
            <Filter className="w-3 h-3 text-[var(--purple-600)]" />
            Filter Severity:
          </span>
          <button
            onClick={() => onSelectSeverity && onSelectSeverity('ALL')}
            className={`px-3 py-1 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              selectedSeverity === 'ALL'
                ? 'bg-[var(--purple-600)] text-white shadow-xs'
                : 'bg-[var(--bg-surface-subtle)] text-[var(--text-muted)] hover:text-[var(--text-primary)]'
            }`}
          >
            All ({totalIssues})
          </button>
        </div>
      </div>

      {/* Severity Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {severities.map((sev) => {
          const Icon = sev.icon;
          const isSelected = selectedSeverity === sev.key;
          const pct = totalIssues > 0 ? ((sev.count / totalIssues) * 100).toFixed(1) : '0.0';

          return (
            <button
              key={sev.key}
              onClick={() => onSelectSeverity && onSelectSeverity(isSelected ? 'ALL' : sev.key)}
              className={`rounded-2xl p-5 border text-left transition-all cursor-pointer focus-ring relative overflow-hidden ${
                sev.bgColor
              } ${sev.borderColor} ${isSelected ? 'ring-2 ring-[var(--purple-600)] shadow-sm' : 'hover:border-[var(--purple-300)]'}`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`text-xs font-bold ${sev.color} uppercase tracking-wider flex items-center gap-1.5`}>
                  <Icon className="w-4 h-4 shrink-0" />
                  {sev.label}
                </span>
                <span className="text-xs font-mono font-bold text-[var(--text-muted)]">{pct}%</span>
              </div>

              <div className="text-3xl font-extrabold text-[var(--text-primary)] font-mono my-1">
                {sev.count.toLocaleString()}
              </div>

              <div className="w-full bg-white/60 h-1.5 rounded-full overflow-hidden my-2 border border-[var(--border-subtle)]">
                <div className={`h-full ${sev.barColor}`} style={{ width: `${pct}%` }} />
              </div>

              <p className="text-[10px] text-[var(--text-muted)] leading-relaxed mt-2">{sev.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Category Breakdown list if categoryCounts exist */}
      {Object.keys(categoryCounts).length > 0 && (
        <div className="mt-6 border-t border-[var(--border-subtle)] pt-5">
          <span className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">
            Audit Findings by Issue Category:
          </span>
          <div className="flex flex-wrap items-center gap-2">
            {Object.entries(categoryCounts).map(([cat, count]) => (
              <div
                key={cat}
                className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] text-xs text-[var(--text-primary)] font-medium"
              >
                <span className="font-bold text-[var(--purple-700)]">{cat}</span>
                <span className="px-2 py-0.5 rounded-md bg-[var(--purple-100)] text-[var(--purple-800)] font-mono text-[10px] font-bold">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
