import React, { useState, useMemo } from 'react';
import { BarChart3, Info, Download } from 'lucide-react';
import type { DistrictComparisonResponse } from '../../api/types';

interface DistrictComparisonChartProps {
  comparisonData: DistrictComparisonResponse | null;
  loading: boolean;
  selectedDistrict: string;
  onSelectDistrict: (district: string) => void;
  onExportCsv?: () => void;
  isExporting?: boolean;
}

export const DistrictComparisonChart: React.FC<DistrictComparisonChartProps> = ({
  comparisonData,
  loading,
  selectedDistrict,
  onSelectDistrict,
  onExportCsv,
  isExporting = false,
}) => {
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc' | 'alpha'>('desc');

  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-5 w-72 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-96 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const items = comparisonData?.items ?? [];

  if (!comparisonData || items.length === 0) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 shadow-xs text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mx-auto border border-amber-200">
          <Info className="w-6 h-6" />
        </div>
        <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
          No District Comparison Observations Available
        </h3>
        <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto leading-relaxed">
          No matching records were found for indicator {comparisonData?.s_no ?? 'selected'} in month {comparisonData?.reporting_month ?? 'selected'}.
        </p>
      </div>
    );
  }

  // Sort items
  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => {
      if (sortOrder === 'alpha') {
        return a.district.localeCompare(b.district);
      }
      // Place missing values at the end
      if (a.value === null && b.value === null) return a.district.localeCompare(b.district);
      if (a.value === null) return 1;
      if (b.value === null) return -1;
      return sortOrder === 'desc' ? b.value - a.value : a.value - b.value;
    });
  }, [items, sortOrder]);

  // Determine max value for bar scaling
  const numericValues = items
    .map((item) => item.value)
    .filter((v): v is number => typeof v === 'number' && !isNaN(v));

  const maxVal = numericValues.length > 0 ? Math.max(1, Math.max(...numericValues)) : 100;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-7 shadow-xs space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-[var(--teal-600)]" />
            <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
              Cross-District Comparison — {comparisonData.reporting_month}
            </h3>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            {comparisonData.parameter_name} (Code S.No: {comparisonData.s_no})
          </p>
        </div>

        {/* Sort Controls & State Stats */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex rounded-xl border border-[var(--border-subtle)] p-1 bg-[var(--bg-surface-subtle)] text-xs font-semibold">
            <button
              onClick={() => setSortOrder('desc')}
              className={`px-3 py-1 rounded-lg transition-colors cursor-pointer ${
                sortOrder === 'desc'
                  ? 'bg-[var(--bg-surface)] text-[var(--teal-700)] shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Highest First
            </button>
            <button
              onClick={() => setSortOrder('asc')}
              className={`px-3 py-1 rounded-lg transition-colors cursor-pointer ${
                sortOrder === 'asc'
                  ? 'bg-[var(--bg-surface)] text-[var(--teal-700)] shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Lowest First
            </button>
            <button
              onClick={() => setSortOrder('alpha')}
              className={`px-3 py-1 rounded-lg transition-colors cursor-pointer ${
                sortOrder === 'alpha'
                  ? 'bg-[var(--bg-surface)] text-[var(--teal-700)] shadow-xs'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              A–Z
            </button>
          </div>

          {onExportCsv && (
            <button
              onClick={onExportCsv}
              disabled={isExporting}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white font-medium rounded-xl text-xs transition-colors cursor-pointer disabled:opacity-50 shadow-xs"
              title="Download cross-district comparison CSV stream with formula injection protection"
            >
              <Download className="w-3.5 h-3.5 text-teal-300" />
              <span>{isExporting ? 'Exporting...' : 'Export CSV'}</span>
            </button>
          )}
        </div>
      </div>

      {/* State Average / Summary Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl">
          <div className="text-[var(--text-muted)] font-bold uppercase tracking-wider text-[10px]">Districts Reporting</div>
          <div className="text-base font-extrabold text-[var(--text-primary)] mt-0.5">{items.length}</div>
        </div>
        <div className="p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl">
          <div className="text-[var(--text-muted)] font-bold uppercase tracking-wider text-[10px]">District Mean</div>
          <div className="text-base font-extrabold text-[var(--teal-700)] mt-0.5">
            {comparisonData.state_mean !== null ? Math.round(comparisonData.state_mean).toLocaleString() : 'N/A'}
          </div>
        </div>
        <div className="p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl">
          <div className="text-[var(--text-muted)] font-bold uppercase tracking-wider text-[10px]">District Median</div>
          <div className="text-base font-extrabold text-[var(--teal-700)] mt-0.5">
            {comparisonData.state_median !== null ? Math.round(comparisonData.state_median).toLocaleString() : 'N/A'}
          </div>
        </div>
        <div className="p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl">
          <div className="text-[var(--text-muted)] font-bold uppercase tracking-wider text-[10px]">Max Observation</div>
          <div className="text-base font-extrabold text-[var(--text-primary)] mt-0.5">
            {maxVal.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Bar Chart List */}
      <div className="space-y-2.5 max-h-[500px] overflow-y-auto pr-2 no-scrollbar">
        {sortedItems.map((item) => {
          const isSelected = item.district === selectedDistrict;
          const isMissing = item.value === null;
          const isZero = item.value === 0;
          const pct = !isMissing && typeof item.value === 'number' ? Math.max(1, (item.value / maxVal) * 100) : 0;

          return (
            <div
              key={item.district}
              onClick={() => onSelectDistrict(item.district)}
              className={`group p-2.5 rounded-xl border transition-all cursor-pointer flex items-center gap-3 ${
                isSelected
                  ? 'bg-teal-50/70 border-teal-300 shadow-xs'
                  : 'bg-[var(--bg-surface-subtle)] border-[var(--border-subtle)] hover:border-slate-300'
              }`}
            >
              {/* District Name */}
              <div className="w-36 sm:w-44 shrink-0 text-xs font-bold text-[var(--text-primary)] flex items-center justify-between">
                <span className="truncate">{item.district}</span>
                {isSelected && (
                  <span className="text-[10px] text-teal-700 font-bold bg-teal-100 px-1.5 py-0.2 rounded">Active</span>
                )}
              </div>

              {/* Bar track */}
              <div className="flex-1 h-5 bg-slate-200/60 rounded-md overflow-hidden relative flex items-center">
                {isMissing ? (
                  <div className="w-full text-center text-[10px] font-semibold text-amber-700 bg-amber-100/80 h-full flex items-center justify-center">
                    Missing / Not Reported
                  </div>
                ) : isZero ? (
                  <div className="w-full text-center text-[10px] font-semibold text-slate-500 bg-slate-200 h-full flex items-center justify-center">
                    Reported Zero (0)
                  </div>
                ) : (
                  <div
                    style={{ width: `${pct}%` }}
                    className={`h-full rounded-md transition-all duration-300 ${
                      isSelected ? 'bg-teal-600' : 'bg-teal-500/85 group-hover:bg-teal-600'
                    }`}
                  />
                )}
              </div>

              {/* Value label */}
              <div className="w-20 sm:w-24 text-right shrink-0 text-xs font-mono font-bold text-[var(--text-primary)]">
                {isMissing ? (
                  <span className="text-amber-600 font-sans text-[11px]">Missing</span>
                ) : (
                  item.value?.toLocaleString()
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Cross-District Comparability Notice */}
      <div className="p-3 bg-slate-100/80 border border-slate-200 rounded-xl text-xs text-slate-700 flex items-start gap-2.5">
        <Info className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <div className="leading-relaxed text-[11px]">
          <strong>Epidemiological Context:</strong> Observations reflect absolute activity counts. Variations across districts reflect geographic scale and population differences rather than operational underperformance. Data is sourced exclusively from official HMIS district returns and never combined with facility records.
        </div>
      </div>
    </div>
  );
};
