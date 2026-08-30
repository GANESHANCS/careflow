import React, { useEffect, useState } from 'react';
import { Filter, RotateCcw } from 'lucide-react';
import { api } from '../../api/client';
import type { Indicator } from '../../api/types';

interface OverviewFiltersProps {
  selectedIndicator: string;
  selectedState: string;
  selectedDistrict: string;
  onIndicatorChange: (code: string) => void;
  onStateChange: (state: string) => void;
  onDistrictChange: (district: string) => void;
  onReset: () => void;
}

export const OverviewFilters: React.FC<OverviewFiltersProps> = ({
  selectedIndicator,
  selectedState,
  selectedDistrict,
  onIndicatorChange,
  onStateChange,
  onDistrictChange,
  onReset,
}) => {
  const [indicators, setIndicators] = useState<Indicator[]>([]);
  const [loadingIndicators, setLoadingIndicators] = useState(false);

  useEffect(() => {
    setLoadingIndicators(true);
    api.getIndicators()
      .then((data) => {
        setIndicators(data.filter((i) => i.active));
        setLoadingIndicators(false);
      })
      .catch(() => {
        setLoadingIndicators(false);
      });
  }, []);

  const hasActiveFilters = Boolean(selectedIndicator || selectedState || selectedDistrict);

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-3.5 shadow-2xs mb-6 flex flex-wrap items-center justify-between gap-3 text-xs font-medium text-[var(--text-secondary)]">
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-1.5 text-[var(--text-muted)] font-semibold uppercase tracking-wider text-[10px]">
          <Filter className="w-3.5 h-3.5 text-[var(--teal-600)]" />
          <span>Filters</span>
        </div>

        {/* Indicator Filter Dropdown */}
        <div className="flex items-center gap-1.5">
          <label htmlFor="indicator-select" className="text-[var(--text-muted)]">Indicator:</label>
          <select
            id="indicator-select"
            value={selectedIndicator}
            onChange={(e) => onIndicatorChange(e.target.value)}
            disabled={loadingIndicators}
            aria-label="Filter by healthcare indicator"
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-md px-2.5 py-1 text-xs text-[var(--text-primary)] font-medium focus-ring cursor-pointer"
          >
            <option value="">All Indicators (OPD, IPD, Care)</option>
            {indicators.map((ind) => (
              <option key={ind.code} value={ind.code}>
                {ind.name} ({ind.code})
              </option>
            ))}
          </select>
        </div>

        {/* State Filter */}
        <div className="flex items-center gap-1.5">
          <label htmlFor="state-input" className="text-[var(--text-muted)]">State:</label>
          <input
            id="state-input"
            type="text"
            placeholder="All States"
            value={selectedState}
            onChange={(e) => onStateChange(e.target.value)}
            aria-label="Filter by state"
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-md px-2.5 py-1 text-xs text-[var(--text-primary)] font-medium focus-ring w-28 sm:w-36"
          />
        </div>

        {/* District Filter */}
        <div className="flex items-center gap-1.5">
          <label htmlFor="district-input" className="text-[var(--text-muted)]">District:</label>
          <input
            id="district-input"
            type="text"
            placeholder="All Districts"
            value={selectedDistrict}
            onChange={(e) => onDistrictChange(e.target.value)}
            aria-label="Filter by district"
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-md px-2.5 py-1 text-xs text-[var(--text-primary)] font-medium focus-ring w-28 sm:w-36"
          />
        </div>
      </div>

      {/* Reset Action */}
      {hasActiveFilters && (
        <button
          onClick={onReset}
          className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-semibold text-[var(--teal-700)] hover:text-[var(--teal-600)] transition-colors rounded-md focus-ring"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Reset Filters</span>
        </button>
      )}
    </div>
  );
};
