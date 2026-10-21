import React, { useState } from 'react';
import { LineChart as LineChartIcon, Info, AlertTriangle, CheckCircle, Download } from 'lucide-react';
import type { DistrictMonthlyTrendsResponse, DistrictTrendObservation } from '../../api/types';

interface DistrictMonthlyTrendChartProps {
  trendData: DistrictMonthlyTrendsResponse | null;
  loading: boolean;
  onExportCsv?: () => void;
  isExporting?: boolean;
}

export const DistrictMonthlyTrendChart: React.FC<DistrictMonthlyTrendChartProps> = ({
  trendData,
  loading,
  onExportCsv,
  isExporting = false,
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<DistrictTrendObservation | null>(null);

  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-5 w-64 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-64 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const observations = trendData?.observations ?? [];

  if (!trendData || observations.length === 0) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 shadow-xs text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mx-auto border border-amber-200">
          <Info className="w-6 h-6" />
        </div>
        <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
          No Monthly Observations Matching Filter
        </h3>
        <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto leading-relaxed">
          No monthly HMIS returns were recorded for the selected combination of district, indicator, and subgroup slice.
        </p>
      </div>
    );
  }

  // SVG parameters
  const svgWidth = 850;
  const svgHeight = 260;
  const padding = { top: 35, right: 40, bottom: 45, left: 65 };

  // Determine numeric bounds (only from numeric valid/zero values, excluding missing)
  const numericValues = observations
    .map((s) => s.value)
    .filter((v): v is number => typeof v === 'number' && !isNaN(v));

  const minVal = numericValues.length > 0 ? Math.min(0, Math.min(...numericValues)) : 0;
  const maxVal = numericValues.length > 0 ? Math.max(10, Math.max(...numericValues)) : 100;
  const valRange = maxVal - minVal || 1;

  // Map series to SVG coordinates
  const plottedPoints = observations.map((pt, idx) => {
    const x =
      padding.left +
      (idx / Math.max(1, observations.length - 1)) * (svgWidth - padding.left - padding.right);
    const y =
      typeof pt.value === 'number' && !isNaN(pt.value)
        ? padding.top +
          (1 - (pt.value - minVal) / valRange) * (svgHeight - padding.top - padding.bottom)
        : null; // Missing values have y = null, NEVER plotted at 0!
    return { ...pt, x, y };
  });

  // Build SVG path segments, cleanly broken whenever a point is missing (y === null)
  const pathSegments: string[] = [];
  let currentSegment = '';

  plottedPoints.forEach((pt) => {
    if (pt.y === null) {
      if (currentSegment) {
        pathSegments.push(currentSegment);
        currentSegment = '';
      }
    } else {
      if (!currentSegment) {
        currentSegment = `M ${pt.x} ${pt.y}`;
      } else {
        currentSegment += ` L ${pt.x} ${pt.y}`;
      }
    }
  });
  if (currentSegment) {
    pathSegments.push(currentSegment);
  }

  // Month label formatter (e.g. 2015-04 -> Apr '15)
  const formatMonth = (mStr: string) => {
    const parts = mStr.split('-');
    if (parts.length === 2) {
      const year = parts[0].slice(2);
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const mIdx = parseInt(parts[1], 10) - 1;
      return `${monthNames[mIdx]} '${year}`;
    }
    return mStr;
  };

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-7 shadow-xs space-y-6">
      {/* Header and Integrity Pill */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <LineChartIcon className="w-4 h-4 text-[var(--teal-600)]" />
            <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
              {trendData.district} — 12-Month Time-Series Movement
            </h3>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            {trendData.parameter_name} (Code: {trendData.s_no})
          </p>
        </div>

        {/* Data Quality Counters & Export Action */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold">
          <span className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1">
            <CheckCircle className="w-3 h-3 text-emerald-600" />
            <span>Valid: {trendData.valid_months_count}</span>
          </span>
          <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-300 flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            <span>Zero: {trendData.zero_months_count}</span>
          </span>
          {trendData.missing_months_count > 0 && (
            <span className="px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-amber-600" />
              <span>Missing: {trendData.missing_months_count}</span>
            </span>
          )}

          {onExportCsv && (
            <button
              onClick={onExportCsv}
              disabled={isExporting}
              className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-900 text-white font-medium rounded-lg text-xs transition-colors cursor-pointer disabled:opacity-50 ml-1 shadow-xs"
              title="Download RFC 4180 CSV export with formula injection protection"
            >
              <Download className="w-3.5 h-3.5 text-teal-300" />
              <span>{isExporting ? 'Exporting...' : 'Export CSV'}</span>
            </button>
          )}
        </div>
      </div>

      {/* SVG Chart Area */}
      <div className="relative">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto overflow-visible select-none">
          {/* Horizontal grid lines & Y-axis labels */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = padding.top + ratio * (svgHeight - padding.top - padding.bottom);
            const val = Math.round(maxVal - ratio * valRange);
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={svgWidth - padding.right}
                  y2={y}
                  stroke="var(--border-subtle)"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="text-[10px] fill-[var(--text-muted)] font-mono font-medium"
                >
                  {val.toLocaleString()}
                </text>
              </g>
            );
          })}

          {/* Zero reference baseline */}
          {minVal <= 0 && maxVal >= 0 && (
            <line
              x1={padding.left}
              y1={padding.top + (1 - (0 - minVal) / valRange) * (svgHeight - padding.top - padding.bottom)}
              x2={svgWidth - padding.right}
              y2={padding.top + (1 - (0 - minVal) / valRange) * (svgHeight - padding.top - padding.bottom)}
              stroke="var(--text-muted)"
              strokeWidth="1.5"
              strokeDasharray="2 2"
            />
          )}

          {/* Continuous path segments */}
          {pathSegments.map((d, sIdx) => (
            <path
              key={sIdx}
              d={d}
              fill="none"
              stroke="var(--teal-600)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          ))}

          {/* Plotted Points with distinct markers for valid vs zero vs missing */}
          {plottedPoints.map((pt, idx) => {
            const isMissing = pt.value_type === 'MISSING' || pt.value === null;
            const isZero = pt.value_type === 'ZERO' || pt.value === 0;

            // For missing values, render an amber marker on the bottom baseline
            const pointY = isMissing
              ? svgHeight - padding.bottom
              : (pt.y as number);

            return (
              <g
                key={idx}
                className="cursor-pointer group"
                onMouseEnter={() => setHoveredPoint(pt)}
                onMouseLeave={() => setHoveredPoint(null)}
              >
                {/* Invisible hover capture target */}
                <circle cx={pt.x} cy={pointY} r="16" fill="transparent" />

                {isMissing ? (
                  // Missing value representation: Amber cross, never drawn on value line
                  <g>
                    <line
                      x1={pt.x - 4}
                      y1={pointY - 4}
                      x2={pt.x + 4}
                      y2={pointY + 4}
                      stroke="#d97706"
                      strokeWidth="2"
                    />
                    <line
                      x1={pt.x + 4}
                      y1={pointY - 4}
                      x2={pt.x - 4}
                      y2={pointY + 4}
                      stroke="#d97706"
                      strokeWidth="2"
                    />
                  </g>
                ) : isZero ? (
                  // Zero value marker: Solid gray square with dark border
                  <rect
                    x={pt.x - 4}
                    y={pointY - 4}
                    width="8"
                    height="8"
                    fill="#94a3b8"
                    stroke="#475569"
                    strokeWidth="1.5"
                    className="transition-transform group-hover:scale-125"
                  />
                ) : (
                  // Valid numeric marker: Teal circle
                  <circle
                    cx={pt.x}
                    cy={pointY}
                    r={hoveredPoint?.reporting_month === pt.reporting_month ? '6' : '4'}
                    fill="var(--bg-surface)"
                    stroke="var(--teal-600)"
                    strokeWidth="2.5"
                    className="transition-transform group-hover:scale-125"
                  />
                )}

                {/* X-axis Month Label */}
                <text
                  x={pt.x}
                  y={svgHeight - padding.bottom + 18}
                  textAnchor="middle"
                  className="text-[10px] fill-[var(--text-secondary)] font-mono font-medium"
                >
                  {formatMonth(pt.reporting_month)}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Interactive Hover Tooltip */}
        {hoveredPoint && (
          <div className="absolute top-2 right-2 bg-slate-900/90 text-white rounded-xl p-3 shadow-lg backdrop-blur-xs text-xs space-y-1.5 max-w-xs z-20 pointer-events-none border border-slate-700">
            <div className="flex items-center justify-between font-mono font-bold text-teal-300 border-b border-slate-700 pb-1">
              <span>{hoveredPoint.reporting_month}</span>
              <span className="uppercase text-[10px] tracking-wider text-slate-400">
                {hoveredPoint.value_type}
              </span>
            </div>
            <div className="flex items-baseline justify-between gap-4">
              <span className="text-slate-300">Observed Value:</span>
              <span className="font-bold text-base text-white">
                {hoveredPoint.value === null ? 'Null (Missing)' : hoveredPoint.value.toLocaleString()}
              </span>
            </div>
            {hoveredPoint.subgroup_type && (
              <div className="flex items-center justify-between text-[11px] text-slate-300">
                <span>Subgroup Slice:</span>
                <span className="font-medium text-slate-200">{hoveredPoint.subgroup_type}</span>
              </div>
            )}
            <div className="pt-1 border-t border-slate-800 text-[10px] text-slate-400 flex items-center justify-between">
              <span>Source Row: #{hoveredPoint.source_row ?? 'N/A'}</span>
              <span>Job: #{hoveredPoint.last_import_job_id ?? 'N/A'}</span>
            </div>
          </div>
        )}
      </div>

      {/* Chart Legend & Non-Additive Aggregation Caution */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pt-3 border-t border-[var(--border-subtle)] text-xs text-[var(--text-secondary)]">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full border-2 border-[var(--teal-600)] bg-[var(--bg-surface)]" />
            <span>Valid Observation</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 bg-slate-400 border border-slate-600 rounded-xs" />
            <span>Explicit Zero Activity</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-amber-600 font-bold">✕</span>
            <span>Missing / Unreported Month</span>
          </div>
        </div>

        {/* Aggregation & Totals Card */}
        <div className="text-[11px] text-[var(--text-muted)] flex items-center gap-2">
          {trendData.annual_total_reported !== null && (
            <span className="bg-[var(--bg-surface-subtle)] px-2.5 py-1 rounded-md border border-[var(--border-subtle)] font-mono">
              Reported FY Total: <strong className="text-[var(--text-primary)]">{trendData.annual_total_reported.toLocaleString()}</strong>
            </span>
          )}
          {trendData.calculated_sum !== null && (
            <span className="bg-[var(--bg-surface-subtle)] px-2.5 py-1 rounded-md border border-[var(--border-subtle)] font-mono">
              Sum of Months: <strong className="text-[var(--text-primary)]">{trendData.calculated_sum.toLocaleString()}</strong>
            </span>
          )}
        </div>
      </div>

      {/* Stock metric & annual total disclaimer */}
      <div className="p-3 bg-amber-50/60 border border-amber-200/80 rounded-xl text-xs text-amber-900 flex items-start gap-2.5">
        <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
        <div className="leading-relaxed text-[11px]">
          <strong>Aggregation Integrity:</strong> {trendData.limitations || 'Monthly values represent discrete reporting periods. Stock/capacity parameters must not be aggregated across time.'} Missing months are represented with distinct breaks and are never interpolated or replaced with zeroes.
        </div>
      </div>
    </div>
  );
};
