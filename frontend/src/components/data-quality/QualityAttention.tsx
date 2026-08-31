import React from 'react';
import { AlertTriangle, ShieldAlert, CheckCircle2, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { DataQualityAnalyticsResponse } from '../../api/types';

interface QualityAttentionProps {
  data: DataQualityAnalyticsResponse | null;
}

export const QualityAttention: React.FC<QualityAttentionProps> = ({ data }) => {
  const completeness = data?.completeness_summary?.completeness_pct ?? 100.0;
  const criticalCount = data?.severity_counts?.['CRITICAL'] ?? 0;
  const errorCount = data?.severity_counts?.['ERROR'] ?? 0;
  const incompleteCount = data?.incomplete_facilities_count ?? 0;

  const items: Array<{
    title: string;
    description: string;
    actionText: string;
    actionUrl?: string;
    severity: 'CRITICAL' | 'WARNING' | 'INFO';
  }> = [];

  if (criticalCount > 0) {
    items.push({
      title: `${criticalCount} CRITICAL QUALITY ISSUE(S) FLAGGED`,
      description: 'Critical audit logs (e.g. impossible negative values or file corruption) were detected during ingestion.',
      actionText: 'Review Audit Issue Registry',
      severity: 'CRITICAL',
    });
  }

  if (completeness < 85) {
    items.push({
      title: `LOW REPORTING COMPLETENESS YIELD (${completeness.toFixed(1)}%)`,
      description: 'Overall facility monthly return yield is below the 85% operational benchmark. Some facility series may be ineligible for forecasting.',
      actionText: 'Inspect Incomplete Facilities Directory',
      severity: 'WARNING',
    });
  }

  if (incompleteCount > 0 && completeness >= 85) {
    items.push({
      title: `${incompleteCount} FACILITY(IES) WITH MISSING MONTHLY RETURNS`,
      description: 'One or more facilities have unsubmitted monthly returns. Historical observations require administrative verification.',
      actionText: 'Inspect Facility Directory',
      actionUrl: '/facilities',
      severity: 'WARNING',
    });
  }

  if (errorCount > 0) {
    items.push({
      title: `${errorCount} HIGH MISSINGNESS / ERROR LOG(S)`,
      description: 'Pipeline identified monthly returns exceeding the 15% missingness threshold or non-numeric formatting.',
      actionText: 'Inspect Data Quality Methodology',
      severity: 'INFO',
    });
  }

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs mb-8">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2 font-display">
            <AlertTriangle className="w-5 h-5 text-[var(--amber-600)]" />
            Operational Governance Attention Required
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Automated governance flags requiring healthcare administrator investigation.
          </p>
        </div>
      </div>

      {items.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {items.map((item, idx) => {
            const isCritical = item.severity === 'CRITICAL';
            const isWarning = item.severity === 'WARNING';

            const bg = isCritical
              ? 'bg-[var(--coral-50)] border-[var(--coral-200)] text-[var(--coral-950)]'
              : isWarning
              ? 'bg-[var(--amber-50)] border-[var(--amber-200)] text-[var(--amber-950)]'
              : 'bg-[var(--purple-50)] border-[var(--purple-200)] text-[var(--purple-950)]';

            const iconColor = isCritical
              ? 'text-[var(--coral-600)]'
              : isWarning
              ? 'text-[var(--amber-600)]'
              : 'text-[var(--purple-600)]';

            const Icon = isCritical ? ShieldAlert : AlertTriangle;

            return (
              <div key={idx} className={`rounded-2xl p-5 border ${bg} flex flex-col justify-between`}>
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className={`w-4 h-4 ${iconColor} shrink-0`} />
                    <span className="text-xs font-extrabold tracking-wide uppercase">{item.title}</span>
                  </div>
                  <p className="text-xs leading-relaxed opacity-90">{item.description}</p>
                </div>

                {item.actionUrl ? (
                  <Link
                    to={item.actionUrl}
                    className="inline-flex items-center gap-1.5 text-xs font-bold text-[var(--teal-800)] hover:underline mt-4 self-start"
                  >
                    <span>{item.actionText}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                ) : (
                  <span className="text-[11px] font-bold text-[var(--text-muted)] mt-4 block">
                    {item.actionText}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-[var(--teal-50)] border border-[var(--teal-200)] rounded-2xl p-6 text-center">
          <CheckCircle2 className="w-8 h-8 text-[var(--teal-600)] mx-auto mb-2" />
          <h4 className="text-base font-extrabold text-[var(--teal-950)]">No Immediate Data-Quality Action Required</h4>
          <p className="text-xs text-[var(--teal-800)] mt-1 max-w-md mx-auto">
            All 13 pipeline quality checks passed cleanly. Data satisfies operational decision support and ML forecasting criteria.
          </p>
        </div>
      )}
    </div>
  );
};
