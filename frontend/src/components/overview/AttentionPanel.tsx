import React from 'react';
import { AlertCircle, CheckCircle2, ShieldAlert, ChevronRight } from 'lucide-react';
import type { DataQualityAnalyticsResponse, AnalyticsSummary } from '../../api/types';

interface AttentionPanelProps {
  summary: AnalyticsSummary | null;
  quality: DataQualityAnalyticsResponse | null;
  loading: boolean;
}

export const AttentionPanel: React.FC<AttentionPanelProps> = ({ summary, quality, loading }) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse">
        <div className="h-4 w-32 bg-[var(--bg-surface-active)] rounded mb-4" />
        <div className="h-16 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  // Derive real attention signals
  const attentionItems: { id: string; title: string; subtitle: string; severity: 'critical' | 'warning' | 'info' }[] = [];

  if (quality) {
    if (quality.incomplete_facilities_count > 0) {
      attentionItems.push({
        id: 'incomplete-facilities',
        title: `${quality.incomplete_facilities_count} Facility Reporting Returns Incomplete`,
        subtitle: 'Facility observations are missing for recent reporting months.',
        severity: 'warning',
      });
    }

    if (quality.severity_counts.CRITICAL && quality.severity_counts.CRITICAL > 0) {
      attentionItems.push({
        id: 'critical-quality-issues',
        title: `${quality.severity_counts.CRITICAL} Critical Data Quality Flags`,
        subtitle: 'Invalid values or zero-value anomalies detected during data ingestion audit.',
        severity: 'critical',
      });
    }

    if (quality.issues && quality.issues.length > 0) {
      quality.issues.forEach((iss) => {
        if (!attentionItems.some((i) => i.id === iss.id)) {
          attentionItems.push({
            id: iss.id,
            title: iss.description,
            subtitle: `Category: ${iss.category} • Affected Records: ${iss.affected_records}`,
            severity: iss.severity.toLowerCase() === 'critical' ? 'critical' : 'warning',
          });
        }
      });
    }
  }

  if (summary && summary.reporting_completeness_pct < 80) {
    attentionItems.push({
      id: 'low-completeness',
      title: `Overall Reporting Completeness at ${summary.reporting_completeness_pct}%`,
      subtitle: 'System completeness baseline is below the recommended 80% operational target.',
      severity: 'warning',
    });
  }

  const hasAttentionItems = attentionItems.length > 0;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <ShieldAlert className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Operational Attention & Action Items</span>
        </div>
        <div className="text-xs text-[var(--text-muted)] font-medium">
          Automated Telemetry Audit
        </div>
      </div>

      {!hasAttentionItems ? (
        <div className="flex items-center gap-4 p-5 rounded-xl bg-[var(--green-50)] border border-[var(--green-100)] text-[var(--green-700)]">
          <CheckCircle2 className="w-6 h-6 shrink-0 text-[var(--green-600)]" />
          <div>
            <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
              Nothing requiring immediate attention.
            </h4>
            <p className="text-xs text-[var(--text-secondary)] mt-0.5 font-normal">
              All active reporting facilities are meeting completeness baselines and no critical data quality anomalies are flagged.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {attentionItems.map((item) => (
            <div
              key={item.id}
              className={`flex items-start justify-between p-4 rounded-xl border transition-all ${
                item.severity === 'critical'
                  ? 'bg-[var(--coral-50)] border-[var(--coral-100)] text-[var(--coral-700)]'
                  : 'bg-[var(--amber-50)] border-[var(--amber-100)] text-[var(--amber-700)]'
              }`}
            >
              <div className="flex items-start gap-3">
                <AlertCircle
                  className={`w-5 h-5 shrink-0 mt-0.5 ${
                    item.severity === 'critical' ? 'text-[var(--coral-600)]' : 'text-[var(--amber-600)]'
                  }`}
                />
                <div>
                  <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
                    {item.title}
                  </h4>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5 font-normal">
                    {item.subtitle}
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
