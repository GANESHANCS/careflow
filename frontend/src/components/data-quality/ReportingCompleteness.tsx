import React from 'react';
import { FileCheck, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import type { DataQualityAnalyticsResponse } from '../../api/types';

interface ReportingCompletenessProps {
  data: DataQualityAnalyticsResponse | null;
}

export const ReportingCompleteness: React.FC<ReportingCompletenessProps> = ({ data }) => {
  const summary = data?.completeness_summary;
  const completeness = summary?.completeness_pct ?? 100.0;
  const expected = summary?.expected_observations ?? 0;
  const actual = summary?.actual_reported_observations ?? 0;
  const missing = expected > actual ? expected - actual : 0;

  const totalFacs = summary?.total_facilities ?? 0;
  const incompleteFacsCount = data?.incomplete_facilities_count ?? 0;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2 font-display">
            <FileCheck className="w-5 h-5 text-[var(--teal-600)]" />
            HMIS Facility Reporting Completeness & Expected Yield
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Evaluating expected monthly facility submissions against verified database records.
          </p>
        </div>

        <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-2xl bg-[var(--teal-50)] border border-[var(--teal-200)] text-[var(--teal-800)] text-xs font-extrabold font-mono self-start sm:self-auto">
          <span>{completeness.toFixed(1)}% Completeness</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
        {/* Left Column: Progress Bar & Primary Metrics */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center justify-between text-xs font-bold text-[var(--text-primary)]">
            <span>Overall Facility Returns Yield</span>
            <span className="font-mono">{actual.toLocaleString()} / {expected.toLocaleString()} Reports</span>
          </div>

          <div className="w-full bg-[var(--bg-surface-subtle)] h-4 rounded-xl overflow-hidden border border-[var(--border-subtle)] p-0.5">
            <div
              className="h-full bg-[var(--teal-600)] rounded-xs transition-all duration-1000 ease-out"
              style={{ width: `${Math.min(100, Math.max(0, completeness))}%` }}
              role="progressbar"
              aria-valuenow={completeness}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Overall facility reporting completeness percentage"
            />
          </div>

          <div className="grid grid-cols-3 gap-3 pt-2">
            <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-2xl p-3.5 text-center">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">Expected Returns</span>
              <span className="text-lg font-extrabold text-[var(--text-primary)] font-mono block mt-1">
                {expected > 0 ? expected.toLocaleString() : 'N/A'}
              </span>
            </div>

            <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-2xl p-3.5 text-center">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-[var(--teal-700)]">Actual Received</span>
              <span className="text-lg font-extrabold text-[var(--teal-800)] font-mono block mt-1">
                {actual.toLocaleString()}
              </span>
            </div>

            <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-2xl p-3.5 text-center">
              <span className="block text-[10px] font-bold uppercase tracking-wider text-[var(--coral-700)]">Missing Returns</span>
              <span className="text-lg font-extrabold text-[var(--coral-800)] font-mono block mt-1">
                {missing.toLocaleString()}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Facility Tier Breakdown Cards */}
        <div className="lg:col-span-6 space-y-3">
          <span className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1">
            Facility Network Reporting Health
          </span>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-[var(--teal-50)] border border-[var(--teal-200)] rounded-2xl p-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[var(--teal-900)] block">Full Reporting Facilities</span>
                <span className="text-2xl font-extrabold text-[var(--teal-800)] font-mono mt-1 block">
                  {totalFacs > 0 ? totalFacs - incompleteFacsCount : 0}
                </span>
                <span className="text-[10px] text-[var(--teal-700)]">100% expected monthly returns</span>
              </div>
              <CheckCircle2 className="w-6 h-6 text-[var(--teal-600)]" />
            </div>

            <div className="bg-[var(--amber-50)] border border-[var(--amber-200)] rounded-2xl p-4 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-[var(--amber-900)] block">Incomplete Facilities</span>
                <span className="text-2xl font-extrabold text-[var(--amber-800)] font-mono mt-1 block">
                  {incompleteFacsCount}
                </span>
                <span className="text-[10px] text-[var(--amber-700)]">One or more missing months</span>
              </div>
              <AlertTriangle className="w-6 h-6 text-[var(--amber-600)]" />
            </div>
          </div>

          <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-3 text-[11px] text-[var(--text-muted)] leading-relaxed flex items-center gap-2">
            <Info className="w-4 h-4 text-[var(--teal-600)] shrink-0" />
            <span>
              <strong>Crucial Distinction:</strong> Facilities with incomplete reporting are flagged for administrative follow-up. Their missing months are excluded from average utilization calculations to avoid artificial metric deflation.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
