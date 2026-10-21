import React, { useState, useMemo } from 'react';
import { RotateCcw, MapPin, Tag, Calendar, Layers, Search, CheckCircle2, HelpCircle } from 'lucide-react';
import type { DistrictIndicatorItem } from '../../api/types';

interface DistrictFiltersProps {
  districts: string[];
  indicators: DistrictIndicatorItem[];
  reportingPeriods: string[];
  subgroups: string[];
  selectedDistrict: string;
  onDistrictChange: (district: string) => void;
  selectedSNo: string;
  onSNoChange: (sNo: string) => void;
  selectedPeriod: string;
  onPeriodChange: (period: string) => void;
  selectedSubgroup: string;
  onSubgroupChange: (subgroup: string) => void;
  onReset: () => void;
}

export const DistrictFilters: React.FC<DistrictFiltersProps> = ({
  districts,
  indicators,
  reportingPeriods,
  subgroups,
  selectedDistrict,
  onDistrictChange,
  selectedSNo,
  onSNoChange,
  selectedPeriod,
  onPeriodChange,
  selectedSubgroup,
  onSubgroupChange,
  onReset,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Filter indicators for the dropdown
  const filteredIndicators = useMemo(() => {
    if (!searchTerm.trim()) return indicators;
    const term = searchTerm.toLowerCase();
    return indicators.filter(
      (ind) =>
        ind.parameter_name.toLowerCase().includes(term) ||
        ind.s_no.toLowerCase().includes(term) ||
        (ind.canonical_indicator_id && ind.canonical_indicator_id.toLowerCase().includes(term))
    );
  }, [indicators, searchTerm]);

  // Current selected indicator detail
  const currentIndicator = useMemo(() => {
    return indicators.find((ind) => ind.s_no === selectedSNo);
  }, [indicators, selectedSNo]);

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-6 shadow-xs space-y-5">
      {/* Primary Filter Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* District Selector */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span>Select District</span>
          </label>
          <select
            value={selectedDistrict}
            onChange={(e) => onDistrictChange(e.target.value)}
            className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3.5 py-2 text-xs text-[var(--text-primary)] font-semibold focus-ring cursor-pointer"
            aria-label="Select district"
          >
            {districts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {/* Indicator Search & Select */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Tag className="w-3.5 h-3.5 text-[var(--teal-600)]" />
              <span>HMIS Indicator</span>
            </span>
            {currentIndicator?.is_mapped && (
              <span className="text-[10px] text-teal-700 font-bold bg-teal-50 px-1.5 py-0.2 rounded border border-teal-200">
                Mapped
              </span>
            )}
          </label>
          <select
            value={selectedSNo}
            onChange={(e) => onSNoChange(e.target.value)}
            className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3.5 py-2 text-xs text-[var(--text-primary)] font-semibold focus-ring cursor-pointer"
            aria-label="Select HMIS Indicator"
          >
            {filteredIndicators.map((ind) => (
              <option key={ind.s_no} value={ind.s_no}>
                {ind.s_no} — {ind.parameter_name.slice(0, 48)}
                {ind.parameter_name.length > 48 ? '...' : ''}
                {ind.is_mapped ? ' (✓ Mapped)' : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Reporting Period Selector */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span>Comparison Month</span>
          </label>
          <select
            value={selectedPeriod}
            onChange={(e) => onPeriodChange(e.target.value)}
            className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3.5 py-2 text-xs text-[var(--text-primary)] font-semibold focus-ring cursor-pointer"
            aria-label="Select comparison reporting period"
          >
            {reportingPeriods.map((period) => (
              <option key={period} value={period}>
                {period}
              </option>
            ))}
          </select>
        </div>

        {/* Subgroup Filter */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span>Subgroup / Demographic Slice</span>
          </label>
          <select
            value={selectedSubgroup}
            onChange={(e) => onSubgroupChange(e.target.value)}
            className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3.5 py-2 text-xs text-[var(--text-primary)] font-semibold focus-ring cursor-pointer"
            aria-label="Select subgroup slice"
          >
            <option value="">All Subgroups (Aggregate)</option>
            {subgroups.map((sg) => (
              <option key={sg} value={sg}>
                {sg}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Filter Quick Action & Search Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[var(--border-subtle)]">
        <div className="flex items-center gap-2 max-w-md w-full sm:w-80">
          <div className="relative w-full">
            <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search parameter label or code..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] focus-ring"
            />
          </div>
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] underline"
            >
              Clear
            </button>
          )}
        </div>

        <button
          onClick={onReset}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--bg-surface-subtle)] hover:bg-[var(--bg-surface-active)] border border-[var(--border-subtle)] rounded-lg transition-colors cursor-pointer focus-ring"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset Filters</span>
        </button>
      </div>

      {/* Selected Indicator Metadata Callout */}
      {currentIndicator && (
        <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
          <div className="space-y-1">
            <div className="flex items-center gap-2 font-mono font-bold text-slate-800">
              <span>Code S.No: {currentIndicator.s_no}</span>
              {currentIndicator.is_mapped ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-sans font-bold text-teal-700 bg-teal-100/70 px-2 py-0.5 rounded-full">
                  <CheckCircle2 className="w-3 h-3" />
                  Canonical: {currentIndicator.canonical_indicator_id} ({currentIndicator.canonical_indicator_name})
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-sans font-medium text-slate-600 bg-slate-200/70 px-2 py-0.5 rounded-full">
                  <HelpCircle className="w-3 h-3 text-slate-500" />
                  Unmapped Verbatim Indicator
                </span>
              )}
            </div>
            <div className="text-slate-600 font-medium">
              {currentIndicator.parameter_name}
            </div>
          </div>
          <div className="text-[11px] text-slate-500 shrink-0 font-mono">
            Subgroups Observed: {currentIndicator.available_subgroups.length > 0 ? currentIndicator.available_subgroups.join(', ') : 'Total'}
          </div>
        </div>
      )}
    </div>
  );
};
