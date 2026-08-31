import React from 'react';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

interface ForecastReadinessProps {
  eligibility?: {
    is_eligible: boolean;
    status: string;
    reason_code: string | null;
    reason_message: string;
  } | null;
  dataQuality?: {
    reporting_completeness_pct?: number;
    quality_score?: number;
    total_observations?: number;
    missing_count?: number;
  } | null;
  totalHistoricalMonths?: number;
}

export const ForecastReadiness: React.FC<ForecastReadinessProps> = ({
  eligibility,
  dataQuality,
  totalHistoricalMonths,
}) => {
  if (!eligibility) return null;

  const isEligible = eligibility.is_eligible;

  // Format human-friendly diagnostic title
  const getDiagnosticTitle = (code: string | null) => {
    switch (code) {
      case 'INSUFFICIENT_HISTORY':
        return 'Insufficient Historical Observations';
      case 'INSUFFICIENT_SEASONAL_HISTORY':
        return 'Insufficient Seasonal Observations (At Least 24 Months Required)';
      case 'EXCESSIVE_MISSINGNESS':
        return 'Excessive Missing Data (>30% Missingness)';
      case 'EXCESSIVE_GAPS':
        return 'Consecutive Reporting Gaps (>3 Months Gap)';
      case 'LOW_REPORTING_COMPLETENESS':
        return 'Low Reporting Completeness Rate';
      default:
        return code ? code.replace(/_/g, ' ') : 'Data Eligibility Check Failed';
    }
  };

  return (
    <div
      className={`rounded-2xl p-5 border shadow-xs mb-8 transition-all ${
        isEligible
          ? 'bg-[var(--teal-50)] border-[var(--teal-200)] text-[var(--teal-950)]'
          : 'bg-[var(--amber-50)] border-[var(--amber-200)] text-[var(--amber-950)]'
      }`}
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Eligibility Badge & Message */}
        <div className="flex items-start gap-3.5">
          {isEligible ? (
            <div className="p-2.5 rounded-xl bg-[var(--teal-600)] text-white shadow-xs flex-shrink-0 mt-0.5">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          ) : (
            <div className="p-2.5 rounded-xl bg-[var(--amber-600)] text-white shadow-xs flex-shrink-0 mt-0.5">
              <AlertTriangle className="w-5 h-5" />
            </div>
          )}

          <div>
            <div className="flex items-center gap-2">
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider ${
                  isEligible
                    ? 'bg-[var(--teal-200)] text-[var(--teal-900)]'
                    : 'bg-[var(--amber-200)] text-[var(--amber-900)]'
                }`}
              >
                {isEligible ? 'FORECAST ELIGIBLE' : 'NOT ELIGIBLE FOR FORECASTING'}
              </span>

              <span className="text-xs font-semibold text-[var(--text-muted)]">
                Status: {eligibility.status}
              </span>
            </div>

            <h3 className="text-base font-bold mt-1 text-[var(--text-primary)]">
              {isEligible
                ? 'Time-Series Meets All Rigorous Validation & Seasonal Thresholds'
                : getDiagnosticTitle(eligibility.reason_code)}
            </h3>

            <p className="text-xs text-[var(--text-muted)] mt-1 max-w-2xl leading-relaxed">
              {eligibility.reason_message}
            </p>
          </div>
        </div>

        {/* Data Quality Metrics Pills */}
        <div className="flex flex-wrap items-center gap-3 bg-[var(--bg-surface)] p-3 rounded-xl border border-[var(--border-subtle)] shadow-2xs self-start md:self-auto">
          <div className="text-center px-2">
            <span className="block text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
              Observed Months
            </span>
            <span className="text-sm font-extrabold text-[var(--text-primary)]">
              {totalHistoricalMonths ?? dataQuality?.total_observations ?? 0}
            </span>
          </div>

          <div className="h-6 w-px bg-[var(--border-subtle)]" />

          <div className="text-center px-2">
            <span className="block text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
              Completeness
            </span>
            <span className="text-sm font-extrabold text-[var(--teal-700)]">
              {dataQuality?.reporting_completeness_pct !== undefined
                ? `${dataQuality.reporting_completeness_pct}%`
                : '100%'}
            </span>
          </div>

          <div className="h-6 w-px bg-[var(--border-subtle)]" />

          <div className="text-center px-2">
            <span className="block text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
              Missing Months
            </span>
            <span className={`text-sm font-extrabold ${(dataQuality?.missing_count ?? 0) > 0 ? 'text-[var(--coral-600)]' : 'text-[var(--text-primary)]'}`}>
              {dataQuality?.missing_count ?? 0}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
