import React from 'react';
import { Search, Filter, RotateCcw, X } from 'lucide-react';

interface FacilityFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedState: string;
  onStateChange: (state: string) => void;
  selectedDistrict: string;
  onDistrictChange: (district: string) => void;
  selectedType: string;
  onTypeChange: (type: string) => void;
  onReset: () => void;
  statesList: string[];
  districtsList: string[];
  typesList: string[];
}

export const FacilityFilters: React.FC<FacilityFiltersProps> = ({
  searchQuery,
  onSearchChange,
  selectedState,
  onStateChange,
  selectedDistrict,
  onDistrictChange,
  selectedType,
  onTypeChange,
  onReset,
  statesList,
  districtsList,
  typesList,
}) => {
  const hasActiveFilters = searchQuery !== '' || selectedState !== '' || selectedDistrict !== '' || selectedType !== '';

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 sm:p-5 shadow-xs mb-6 space-y-3">
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search facility name, district, or HMIS code..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-9 py-2 text-xs sm:text-sm bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl text-[var(--text-primary)] focus:border-[var(--teal-600)] transition-colors focus-ring"
            aria-label="Search facilities by name, district, or code"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] p-0.5 rounded-full"
              aria-label="Clear search text"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filters Row */}
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="flex items-center gap-1 text-[var(--text-muted)] text-xs font-bold uppercase tracking-wider pr-1">
            <Filter className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span>Filters</span>
          </div>

          {/* State Select */}
          <select
            value={selectedState}
            onChange={(e) => onStateChange(e.target.value)}
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-lg px-2.5 py-1.5 text-xs text-[var(--text-primary)] font-medium focus-ring cursor-pointer"
            aria-label="Filter by state"
          >
            <option value="">All States</option>
            {statesList.map((st) => (
              <option key={st} value={st}>
                {st}
              </option>
            ))}
          </select>

          {/* District Select */}
          <select
            value={selectedDistrict}
            onChange={(e) => onDistrictChange(e.target.value)}
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-lg px-2.5 py-1.5 text-xs text-[var(--text-primary)] font-medium focus-ring cursor-pointer"
            aria-label="Filter by district"
          >
            <option value="">All Districts</option>
            {districtsList.map((dt) => (
              <option key={dt} value={dt}>
                {dt}
              </option>
            ))}
          </select>

          {/* Facility Type Select */}
          <select
            value={selectedType}
            onChange={(e) => onTypeChange(e.target.value)}
            className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-lg px-2.5 py-1.5 text-xs text-[var(--text-primary)] font-medium focus-ring cursor-pointer"
            aria-label="Filter by facility type"
          >
            <option value="">All Facility Types</option>
            {typesList.map((tp) => (
              <option key={tp} value={tp}>
                {tp}
              </option>
            ))}
          </select>

          {/* Reset Filters CTA */}
          {hasActiveFilters && (
            <button
              onClick={onReset}
              className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--teal-700)] hover:text-[var(--teal-600)] transition-colors px-2 py-1.5 rounded-lg hover:bg-[var(--teal-50)] focus-ring cursor-pointer"
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
