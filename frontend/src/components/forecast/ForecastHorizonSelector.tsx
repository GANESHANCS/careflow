import React from 'react';
import { Calendar, Loader2 } from 'lucide-react';

interface ForecastHorizonSelectorProps {
  currentHorizon: number;
  onHorizonSelect: (horizon: number) => void;
  isLoading?: boolean;
}

export const ForecastHorizonSelector: React.FC<ForecastHorizonSelectorProps> = ({
  currentHorizon,
  onHorizonSelect,
  isLoading = false,
}) => {
  const horizons = [
    { value: 3, label: '3 Months (Quarterly)', desc: 'Short-term operational planning' },
    { value: 6, label: '6 Months (Bi-Annual)', desc: 'Medium-term supply & staffing forecast' },
    { value: 12, label: '12 Months (Annual)', desc: 'Full annual seasonal capacity prediction' },
  ];

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 sm:p-5 shadow-xs mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-[var(--purple-600)]" />
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)]">
              Forecast Horizon Duration
            </h4>
            <p className="text-[11px] text-[var(--text-muted)]">
              Select predictive look-ahead window for model re-training and multi-step prediction
            </p>
          </div>
        </div>

        {/* Horizon Toggle Button Group */}
        <div className="flex items-center gap-2">
          {horizons.map((h) => {
            const isSelected = currentHorizon === h.value;
            return (
              <button
                key={h.value}
                onClick={() => onHorizonSelect(h.value)}
                disabled={isLoading}
                title={h.desc}
                className={`relative px-4 py-2 rounded-xl text-xs font-extrabold transition-all cursor-pointer focus-ring flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-[var(--purple-600)] text-white shadow-xs'
                    : 'bg-[var(--bg-surface-subtle)] text-[var(--text-muted)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)]'
                } ${isLoading ? 'opacity-60 cursor-not-allowed' : ''}`}
                aria-label={`Select ${h.label} forecast horizon`}
              >
                {isLoading && isSelected && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                <span>{h.value} Months</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
