import React from 'react';
import { Filter, Layers, RotateCcw } from 'lucide-react';
import type { Indicator } from '../../api/types';

interface RegionalFiltersProps {
  level: 'state' | 'district';
  onLevelChange: (level: 'state' | 'district') => void;
  selectedIndicator: string;
  onIndicatorChange: (code: string) => void;
  selectedState: string;
  onStateChange: (state: string) => void;
  indicators: Indicator[];
  statesList: string[];
  onReset: () => void;
}

export const RegionalFilters: React.FC<RegionalFiltersProps> = ({
  level,
  onLevelChange,
  selectedIndicator,
  onIndicatorChange,
  selectedState,
  onStateChange,
  indicators = [],
  statesList = [],
  onReset,
}) => {
  const hasActiveFilters = selectedIndicator !== '' || selectedState !== '';

  const safeIndicators = Array.isArray(indicators) ? indicators : [];
  const safeStatesList = Array.isArray(statesList) ? statesList : [];

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 sm:p-5 shadow-xs mb-8 space-y-4">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Level Navigation Toggle */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span>Jurisdiction Level:</span>
          </span>
          <div className="inline-flex rounded-xl border border-[var(--border-subtle)] p-1 bg-[var(--bg-surface-subtle)]">
            <button
              onClick={() => onLevelChange('state')}
              className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all cursor-pointer focus-ring ${
                level === 'state'
                  ? 'bg-[var(--bg-surface)] text-[var(--teal-700)] shadow-xs border border-[var(--border-subtle)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              State Level
            </button>
            <button
              onClick={() => onLevelChange('district')}
              className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all cursor-pointer focus-ring ${
                level === 'district'
                  ? 'bg-[var(--bg-surface)] text-[var(--teal-700)] shadow-xs border border-[var(--border-subtle)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              District Level
            </button>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1 text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider pr-1">
            <Filter className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span>Filters</span>
          </div>

          {/* Indicator Selector */}
          <select
            value={selectedIndicator}
            onChange={(e) => onIndicatorChange(e.target.value)}
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3 py-1.5 text-xs text-[var(--text-primary)] font-semibold focus-ring cursor-pointer max-w-xs"
            aria-label="Select healthcare indicator"
          >
            <option value="">All Health Indicators</option>
            {safeIndicators.map((ind) => (
              <option key={ind.code} value={ind.code}>
                {ind.name} ({ind.code})
              </option>
            ))}
          </select>

          {/* State Selector */}
          <select
            value={selectedState}
            onChange={(e) => onStateChange(e.target.value)}
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3 py-1.5 text-xs text-[var(--text-primary)] font-semibold focus-ring cursor-pointer"
            aria-label="Filter by state"
          >
            <option value="">All States</option>
            {safeStatesList.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>

          {/* Reset Filters CTA */}
          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--teal-700)] hover:text-[var(--teal-600)] transition-colors px-2.5 py-1.5 rounded-lg hover:bg-[var(--teal-50)] focus-ring cursor-pointer"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
