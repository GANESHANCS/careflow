import React from 'react';
import { Building2, AlertTriangle, RefreshCw, ArrowRight } from 'lucide-react';
import type { Facility } from '../../api/types';

interface ForecastEmptyStateProps {
  type: 'NO_SELECTION' | 'NOT_ELIGIBLE' | 'ERROR';
  facilities?: Facility[];
  onSelectFacility?: (id: string) => void;
  errorMessage?: string;
  onRetry?: () => void;
  reasonMessage?: string;
}

export const ForecastEmptyState: React.FC<ForecastEmptyStateProps> = ({
  type,
  facilities = [],
  onSelectFacility,
  errorMessage,
  onRetry,
  reasonMessage,
}) => {
  const sampleFacilities = facilities.slice(0, 4);

  if (type === 'NO_SELECTION') {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-8 sm:p-12 text-center max-w-3xl mx-auto my-8 shadow-xs">
        <div className="w-16 h-16 rounded-2xl bg-[var(--purple-100)] text-[var(--purple-600)] flex items-center justify-center mx-auto mb-4">
          <Building2 className="w-8 h-8" />
        </div>

        <h3 className="text-xl sm:text-2xl font-extrabold text-[var(--text-primary)] tracking-tight">
          Select a Target Facility for Demand Forecasting
        </h3>

        <p className="text-sm text-[var(--text-muted)] mt-2 max-w-xl mx-auto leading-relaxed">
          Select a healthcare facility from the control toolbar above to evaluate time-series eligibility, run candidate baseline & ML models, and generate predictive utilization forecasts.
        </p>

        {sampleFacilities.length > 0 && (
          <div className="mt-8 pt-6 border-t border-[var(--border-subtle)]">
            <span className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3">
              Or Explore Sample Facilities:
            </span>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {sampleFacilities.map((fac) => (
                <button
                  key={fac.id}
                  onClick={() => onSelectFacility && onSelectFacility(fac.id)}
                  className="px-3.5 py-2 rounded-xl bg-[var(--bg-surface-subtle)] hover:bg-[var(--purple-50)] border border-[var(--border-subtle)] hover:border-[var(--purple-300)] text-xs font-bold text-[var(--text-primary)] hover:text-[var(--purple-900)] transition-all cursor-pointer flex items-center gap-1.5 focus-ring"
                >
                  <span>{fac.facility_name}</span>
                  <span className="text-[10px] text-[var(--text-muted)] font-normal">({fac.district})</span>
                  <ArrowRight className="w-3 h-3 text-[var(--purple-600)]" />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  if (type === 'NOT_ELIGIBLE') {
    return (
      <div className="bg-[var(--amber-50)] border border-[var(--amber-200)] rounded-3xl p-8 text-center max-w-3xl mx-auto my-8 shadow-xs text-[var(--amber-950)]">
        <div className="w-14 h-14 rounded-2xl bg-[var(--amber-200)] text-[var(--amber-800)] flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-7 h-7" />
        </div>

        <h3 className="text-xl font-extrabold text-[var(--amber-950)] tracking-tight">
          Forecast Not Available for Selected Series
        </h3>

        <p className="text-sm text-[var(--amber-900)] mt-2 max-w-lg mx-auto leading-relaxed">
          {reasonMessage ||
            'The selected facility and indicator time-series does not satisfy minimum historical length or completeness requirements.'}
        </p>

        {sampleFacilities.length > 0 && (
          <div className="mt-6 pt-6 border-t border-[var(--amber-200)]">
            <span className="block text-xs font-bold uppercase tracking-wider text-[var(--amber-900)] mb-3">
              Try an Eligible Facility:
            </span>
            <div className="flex flex-wrap items-center justify-center gap-2">
              {sampleFacilities.map((fac) => (
                <button
                  key={fac.id}
                  onClick={() => onSelectFacility && onSelectFacility(fac.id)}
                  className="px-3.5 py-2 rounded-xl bg-white hover:bg-[var(--purple-50)] border border-[var(--amber-300)] text-xs font-bold text-gray-900 hover:text-[var(--purple-900)] transition-all cursor-pointer flex items-center gap-1.5 focus-ring"
                >
                  <span>{fac.facility_name}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-8 text-center max-w-2xl mx-auto my-8 shadow-xs">
      <div className="w-14 h-14 rounded-2xl bg-[var(--coral-100)] text-[var(--coral-700)] flex items-center justify-center mx-auto mb-4">
        <AlertTriangle className="w-7 h-7" />
      </div>

      <h3 className="text-xl font-extrabold text-[var(--text-primary)]">
        Unable to Load Forecast Model
      </h3>

      <p className="text-xs text-[var(--text-muted)] mt-2 max-w-md mx-auto">
        {errorMessage || 'Unable to connect to CAREFlow backend API forecasting service.'}
      </p>

      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 px-4 py-2 rounded-xl bg-[var(--purple-600)] hover:bg-[var(--purple-700)] text-white text-xs font-bold transition-all cursor-pointer inline-flex items-center gap-2 shadow-xs focus-ring"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Model Query</span>
        </button>
      )}
    </div>
  );
};
