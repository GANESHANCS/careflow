import React from 'react';
import { NavLink } from 'react-router-dom';
import { BrainCircuit, CheckCircle2, AlertTriangle, ArrowRight, Sparkles } from 'lucide-react';
import type { ForecastResponse } from '../../api/types';

interface ForecastReadinessProps {
  facilityId: string;
  forecastData: ForecastResponse | null;
  loading: boolean;
}

export const ForecastReadiness: React.FC<ForecastReadinessProps> = ({
  facilityId,
  forecastData,
  loading,
}) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-3">
        <div className="h-4 w-44 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-24 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const isEligible = forecastData?.eligibility?.is_eligible ?? (forecastData?.status === 'SUCCESS');
  const reasonMessage = forecastData?.eligibility?.reason_message || forecastData?.message;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <BrainCircuit className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Predictive Intelligence & Forecast Readiness</span>
        </div>
        <div
          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-bold ${
            isEligible
              ? 'bg-[var(--green-50)] border-[var(--green-100)] text-[var(--green-700)]'
              : 'bg-[var(--amber-50)] border-[var(--amber-100)] text-[var(--amber-700)]'
          }`}
        >
          {isEligible ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-[var(--green-600)]" />
              <span>FORECAST READY</span>
            </>
          ) : (
            <>
              <AlertTriangle className="w-3.5 h-3.5 text-[var(--amber-600)]" />
              <span>NOT ELIGIBLE</span>
            </>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
        {/* Status Card */}
        <div className="lg:col-span-8 space-y-3">
          {isEligible ? (
            <div className="bg-[var(--green-50)] border border-[var(--green-100)] rounded-xl p-5 text-[var(--green-700)] space-y-2">
              <div className="flex items-center gap-2 font-display font-bold text-base text-[var(--text-primary)]">
                <Sparkles className="w-4 h-4 text-[var(--green-600)]" />
                <span>Phase 5 Time-Series ML Engine Validated</span>
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                This facility meets historical observations, seasonal length, and completeness baselines. The forecasting engine has benchmarked SARIMAX, Ridge, Random Forest, and Gradient Boosting models.
              </p>
              {forecastData?.explainability && (
                <div className="pt-2 text-xs font-mono text-[var(--teal-700)] font-semibold border-t border-[var(--green-200)]">
                  Selected Model: {forecastData.explainability.model_title} • Baseline Improvement: {forecastData.explainability.improvement_over_baseline}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-[var(--amber-50)] border border-[var(--amber-100)] rounded-xl p-5 text-[var(--amber-700)] space-y-2">
              <div className="flex items-center gap-2 font-display font-bold text-base text-[var(--text-primary)]">
                <AlertTriangle className="w-4 h-4 text-[var(--amber-600)]" />
                <span>Eligibility Diagnostic Notice</span>
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                {reasonMessage || 'This facility series does not currently meet the minimum 12-month contiguous historical baseline or seasonal observations threshold required for reliable machine learning forecasts.'}
              </p>
            </div>
          )}
        </div>

        {/* CTA Link to Forecast Module */}
        <div className="lg:col-span-4 flex flex-col justify-center">
          <NavLink
            to={`/forecast?facility_id=${facilityId}`}
            className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-[var(--teal-700)] hover:bg-[var(--teal-600)] text-white font-display font-bold text-xs uppercase tracking-wider transition-all duration-200 shadow-sm hover:shadow focus-ring text-center"
          >
            <span>Explore Forecasting Engine</span>
            <ArrowRight className="w-4 h-4" />
          </NavLink>
        </div>
      </div>
    </div>
  );
};
