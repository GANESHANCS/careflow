import React from 'react';
import { ShieldCheck, Calendar, Database, Building2, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import type { DataQualityAnalyticsResponse } from '../../api/types';

interface DataQualityHeaderProps {
  data: DataQualityAnalyticsResponse | null;
}

export const DataQualityHeader: React.FC<DataQualityHeaderProps> = ({ data }) => {
  const score = data?.overall_quality_score ?? 100;
  
  let statusBadge = {
    label: 'GOOD',
    bg: 'bg-[var(--teal-50)]',
    border: 'border-[var(--teal-200)]',
    text: 'text-[var(--teal-800)]',
    icon: CheckCircle2,
  };

  if (score < 60) {
    statusBadge = {
      label: 'CRITICAL REVIEW',
      bg: 'bg-[var(--coral-50)]',
      border: 'border-[var(--coral-200)]',
      text: 'text-[var(--coral-800)]',
      icon: XCircle,
    };
  } else if (score < 80) {
    statusBadge = {
      label: 'REVIEW REQUIRED',
      bg: 'bg-[var(--amber-50)]',
      border: 'border-[var(--amber-200)]',
      text: 'text-[var(--amber-800)]',
      icon: AlertTriangle,
    };
  }

  const StatusIcon = statusBadge.icon;
  const totalObs = data?.observation_breakdown?.total_observations ?? (data?.completeness_summary?.actual_reported_observations ?? 0);
  const latestPeriod = data?.latest_period ?? 'Current Cycle';
  const reportingFacs = data?.completeness_summary?.reporting_facilities ?? 0;
  const totalFacs = data?.completeness_summary?.total_facilities ?? 0;

  return (
    <div className="mb-8 border-b border-[var(--border-subtle)] pb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[var(--teal-700)] mb-1">
            <ShieldCheck className="w-4 h-4 text-[var(--teal-600)]" />
            <span>CAREFlow / Data Quality Intelligence & Governance</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-primary)] tracking-tight">
            Know how reliable the data is before acting on it.
          </h1>
          <p className="text-sm sm:text-base text-[var(--text-muted)] mt-1 max-w-3xl leading-relaxed">
            Continuous 13-point HMIS quality audit framework inspecting reporting completeness, observation validity, duplication frequency, and facility temporal continuity.
          </p>
        </div>

        {/* Development Framework Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[var(--purple-50)] border border-[var(--purple-200)] text-[var(--purple-800)] text-xs font-semibold self-start lg:self-auto">
          <ShieldCheck className="w-4 h-4 text-[var(--purple-600)] shrink-0" />
          <span>Synthetic Development Framework</span>
        </div>
      </div>

      {/* Metadata Chips */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] font-medium text-[var(--text-primary)]">
          <Calendar className="w-3.5 h-3.5 text-[var(--teal-600)]" />
          <span className="text-[var(--text-muted)]">Audit Period:</span>
          <span className="font-bold">{latestPeriod}</span>
        </div>

        <div className={`flex items-center gap-1.5 px-3 py-1 rounded-lg ${statusBadge.bg} border ${statusBadge.border} ${statusBadge.text} font-bold`}>
          <StatusIcon className="w-3.5 h-3.5" />
          <span>Quality Status: {statusBadge.label}</span>
        </div>

        {totalObs > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] font-medium text-[var(--text-primary)]">
            <Database className="w-3.5 h-3.5 text-[var(--purple-600)]" />
            <span className="text-[var(--text-muted)]">Audited Observations:</span>
            <span className="font-bold font-mono">{totalObs.toLocaleString()}</span>
          </div>
        )}

        {totalFacs > 0 && (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] font-medium text-[var(--text-primary)]">
            <Building2 className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span className="text-[var(--text-muted)]">Active Facilities:</span>
            <span className="font-bold">{reportingFacs} / {totalFacs}</span>
          </div>
        )}
      </div>
    </div>
  );
};
