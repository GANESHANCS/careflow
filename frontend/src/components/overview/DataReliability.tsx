import React from 'react';
import { ShieldCheck, AlertTriangle, CheckCircle, Building2, AlertCircle } from 'lucide-react';
import type { DataQualityAnalyticsResponse, IncompleteFacilityItem } from '../../api/types';

interface DataReliabilityProps {
  data: DataQualityAnalyticsResponse | null;
  loading: boolean;
}

export const DataReliability: React.FC<DataReliabilityProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse">
        <div className="h-4 w-36 bg-[var(--bg-surface-active)] rounded mb-4" />
        <div className="h-24 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const score = data?.overall_quality_score ?? 100;
  const totalIssues = data?.total_issues ?? 0;
  const severity = data?.severity_counts ?? {};
  const incompleteCount = data?.incomplete_facilities_count ?? 0;
  const incompleteFacilities = data?.incomplete_facilities ?? [];

  // Determine overall audit semantic badge
  let scoreTheme = {
    badge: 'GREEN',
    bg: 'bg-[var(--green-50)]',
    border: 'border-[var(--green-100)]',
    text: 'text-[var(--green-700)]',
    icon: CheckCircle,
    label: 'High Integrity Audit',
  };

  if (score < 50 || (severity.CRITICAL && severity.CRITICAL > 0)) {
    scoreTheme = {
      badge: 'CORAL',
      bg: 'bg-[var(--coral-50)]',
      border: 'border-[var(--coral-100)]',
      text: 'text-[var(--coral-700)]',
      icon: AlertCircle,
      label: 'Critical Audit Warnings',
    };
  } else if (score < 80 || totalIssues > 0) {
    scoreTheme = {
      badge: 'AMBER',
      bg: 'bg-[var(--amber-50)]',
      border: 'border-[var(--amber-100)]',
      text: 'text-[var(--amber-700)]',
      icon: AlertTriangle,
      label: 'Audit Action Required',
    };
  }

  const IconComp = scoreTheme.icon;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <ShieldCheck className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Data Governance & Reporting Reliability</span>
        </div>
        <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold ${scoreTheme.bg} ${scoreTheme.border} ${scoreTheme.text}`}>
          <IconComp className="w-3.5 h-3.5" />
          <span>{scoreTheme.label}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Score Display Card */}
        <div className="md:col-span-5 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-6 text-center">
          <div className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-1">
            Overall Quality Score
          </div>
          <div className="text-4xl sm:text-5xl font-extrabold font-display text-[var(--text-primary)]">
            {score.toFixed(1)}%
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-2 font-normal">
            Automated completeness, missing return audit, and zero-value check score.
          </p>
        </div>

        {/* Severity & Incomplete Metrics */}
        <div className="md:col-span-7 space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-3.5 text-center shadow-2xs">
              <div className="text-[10px] font-bold uppercase text-[var(--coral-700)] tracking-wider">Critical Issues</div>
              <div className="text-2xl font-extrabold font-display text-[var(--text-primary)] mt-0.5">
                {severity.CRITICAL ?? 0}
              </div>
            </div>
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-3.5 text-center shadow-2xs">
              <div className="text-[10px] font-bold uppercase text-[var(--amber-700)] tracking-wider">Warnings</div>
              <div className="text-2xl font-extrabold font-display text-[var(--text-primary)] mt-0.5">
                {severity.WARNING ?? 0}
              </div>
            </div>
            <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-3.5 text-center shadow-2xs">
              <div className="text-[10px] font-bold uppercase text-[var(--teal-700)] tracking-wider">Incomplete Outlets</div>
              <div className="text-2xl font-extrabold font-display text-[var(--text-primary)] mt-0.5">
                {incompleteCount}
              </div>
            </div>
          </div>

          {/* Incomplete Facilities List Preview */}
          {incompleteFacilities.length > 0 && (
            <div className="border-t border-[var(--border-subtle)] pt-3">
              <div className="text-xs font-bold text-[var(--text-primary)] mb-2 flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-[var(--amber-600)]" />
                <span>Facilities Awaiting Reporting Returns ({incompleteFacilities.length})</span>
              </div>
              <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                {incompleteFacilities.slice(0, 3).map((fac: IncompleteFacilityItem) => (
                  <div
                    key={fac.facility_id}
                    className="flex items-center justify-between text-xs p-2 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)]"
                  >
                    <span className="font-semibold text-[var(--text-primary)] truncate max-w-[200px]">
                      {fac.facility_name}
                    </span>
                    <span className="text-[var(--text-muted)] font-medium">
                      {fac.reported_months} / {fac.expected_months} Months ({fac.completeness_pct}%)
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
