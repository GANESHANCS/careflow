import React, { useState, useMemo } from 'react';
import { RotateCcw, MapPin, Tag, Calendar, Layers, Search, CheckCircle2, HelpCircle, ShieldCheck } from 'lucide-react';
import type { DistrictIndicatorItem } from '../../api/types';

interface DistrictFiltersProps {
  districts: string[];
  indicators: DistrictIndicatorItem[];
  reportingPeriods: string[];
  subgroups: string[];
  financialYears?: string[];
  selectedDistrict: string;
  onDistrictChange: (district: string) => void;
  selectedSNo: string;
  onSNoChange: (sNo: string) => void;
  selectedPeriod: string;
  onPeriodChange: (period: string) => void;
  selectedSubgroup: string;
  onSubgroupChange: (subgroup: string) => void;
  selectedFinancialYear?: string;
  onFinancialYearChange?: (fy: string) => void;
  onReset: () => void;
}

export const DistrictFilters: React.FC<DistrictFiltersProps> = ({
  districts,
  indicators,
  reportingPeriods,
  subgroups,
  financialYears = [],
  selectedDistrict,
  onDistrictChange,
  selectedSNo,
  onSNoChange,
  selectedPeriod,
  onPeriodChange,
  selectedSubgroup,
  onSubgroupChange,
  selectedFinancialYear,
  onFinancialYearChange,
  onReset,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'VERIFIED' | 'UNMAPPED'>('ALL');

  // Filter indicators by status and search query
  const filteredIndicators = useMemo(() => {
    let result = indicators;

    if (statusFilter === 'VERIFIED') {
      result = result.filter((ind) => ind.is_mapped);
    } else if (statusFilter === 'UNMAPPED') {
      result = result.filter((ind) => !ind.is_mapped);
    }

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (ind) =>
          ind.parameter_name.toLowerCase().includes(term) ||
          ind.s_no.toLowerCase().includes(term) ||
          (ind.canonical_indicator_id && ind.canonical_indicator_id.toLowerCase().includes(term))
      );
    }

    return result;
  }, [indicators, statusFilter, searchTerm]);

  // Current selected indicator detail
  const currentIndicator = useMemo(() => {
    return indicators.find((ind) => ind.s_no === selectedSNo);
  }, [indicators, selectedSNo]);

  const verifiedCount = useMemo(() => indicators.filter((i) => i.is_mapped).length, [indicators]);
  const unmappedCount = useMemo(() => indicators.filter((i) => !i.is_mapped).length, [indicators]);

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-6 shadow-xs space-y-5">
      {/* Primary Filter Bar */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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

        {/* Financial Year Selector */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span>Financial Year</span>
          </label>
          <select
            value={selectedFinancialYear || ''}
            onChange={(e) => onFinancialYearChange && onFinancialYearChange(e.target.value)}
            className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3.5 py-2 text-xs text-[var(--text-primary)] font-semibold focus-ring cursor-pointer"
            aria-label="Select financial year"
          >
            <option value="">All Observed FYs</option>
            {financialYears.map((fy) => (
              <option key={fy} value={fy}>
                FY {fy}
              </option>
            ))}
          </select>
        </div>

        {/* Indicator Search & Select */}
        <div className="space-y-1.5 lg:col-span-1">
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
                {ind.s_no} — {ind.parameter_name.slice(0, 42)}
                {ind.parameter_name.length > 42 ? '...' : ''}
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
            <span>Subgroup / Slice</span>
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
        {/* Mapping Status Filter Pills */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-[11px] font-bold text-[var(--text-muted)] uppercase tracking-wider mr-1">
            Registry:
          </span>
          <button
            type="button"
            onClick={() => setStatusFilter('ALL')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
              statusFilter === 'ALL'
                ? 'bg-slate-800 text-white'
                : 'bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)] hover:bg-[var(--bg-surface-active)]'
            }`}
          >
            All ({indicators.length})
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('VERIFIED')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center gap-1 transition-colors cursor-pointer ${
              statusFilter === 'VERIFIED'
                ? 'bg-teal-700 text-white'
                : 'bg-teal-50 text-teal-800 border border-teal-200 hover:bg-teal-100'
            }`}
          >
            <CheckCircle2 className="w-3 h-3" />
            <span>Verified ({verifiedCount})</span>
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter('UNMAPPED')}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
              statusFilter === 'UNMAPPED'
                ? 'bg-slate-700 text-white'
                : 'bg-slate-100 text-slate-700 border border-slate-200 hover:bg-slate-200'
            }`}
          >
            Unmapped ({unmappedCount})
          </button>
        </div>

        <div className="flex items-center gap-3 ml-auto">
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search parameter code or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] focus-ring"
            />
          </div>
          {searchTerm && (
            <button
              onClick={() => setSearchTerm('')}
              className="text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] underline cursor-pointer"
            >
              Clear
            </button>
          )}

          <button
            onClick={() => {
              setSearchTerm('');
              setStatusFilter('ALL');
              onReset();
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] bg-[var(--bg-surface-subtle)] hover:bg-[var(--bg-surface-active)] border border-[var(--border-subtle)] rounded-lg transition-colors cursor-pointer focus-ring shrink-0"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
        </div>
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
                  Unmapped Verbatim Parameter
                </span>
              )}
              {currentIndicator.is_stock_metric && (
                <span className="inline-flex items-center gap-1 text-[11px] font-sans font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full border border-amber-300">
                  <ShieldCheck className="w-3 h-3 text-amber-600" />
                  Non-Additive Stock Metric
                </span>
              )}
            </div>
            <div className="text-slate-600 font-medium">
              {currentIndicator.parameter_name}
            </div>
          </div>
          <div className="text-[11px] text-slate-500 shrink-0 font-mono">
            Subgroups: {currentIndicator.available_subgroups.length > 0 ? currentIndicator.available_subgroups.join(', ') : 'Total'}
          </div>
        </div>
      )}
    </div>
  );
};
