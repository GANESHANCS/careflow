import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { LineChart as LineChartIcon, Calendar, Info } from 'lucide-react';
import type { AnalyticsTrendsResponse, MonthlyTrendPoint } from '../../api/types';

interface RegionalTrendProps {
  trends: AnalyticsTrendsResponse | null;
  loading: boolean;
  regionName?: string | null;
}

export const RegionalTrend: React.FC<RegionalTrendProps> = ({ trends, loading, regionName }) => {
  const shouldReduceMotion = useReducedMotion();
  const [hoveredPoint, setHoveredPoint] = useState<MonthlyTrendPoint | null>(null);

  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-4 w-48 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-64 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const series = trends?.series ?? [];

  if (!trends || series.length === 0) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs text-center">
        <div className="w-10 h-10 rounded-full bg-[var(--amber-50)] text-[var(--amber-600)] flex items-center justify-center mx-auto mb-3 border border-[var(--amber-100)]">
          <Info className="w-5 h-5" />
        </div>
        <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
          No Time-Series Trend Data Available
        </h3>
        <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto mt-1 leading-relaxed">
          Monthly time-series observation trends for {regionName || 'the selected regional scope'} are awaiting raw HMIS return ingestion.
        </p>
      </div>
    );
  }

  // SVG parameters
  const svgWidth = 800;
  const svgHeight = 220;
  const padding = { top: 25, right: 30, bottom: 35, left: 55 };

  const validValues = series.map((s) => s.total_value).filter((v): v is number => typeof v === 'number');
  const minVal = validValues.length > 0 ? Math.min(...validValues) : 0;
  const maxVal = validValues.length > 0 ? Math.max(...validValues) : 100;
  const valRange = maxVal - minVal || 1;

  const points = series.map((pt, idx) => {
    const x =
      padding.left +
      (idx / Math.max(1, series.length - 1)) * (svgWidth - padding.left - padding.right);
    const y =
      typeof pt.total_value === 'number'
        ? padding.top +
          (1 - (pt.total_value - minVal) / valRange) * (svgHeight - padding.top - padding.bottom)
        : null;
    return { ...pt, x, y };
  });

  const pathD = points.reduce((acc, pt, idx) => {
    if (pt.y === null) return acc;
    const prevValid = points.slice(0, idx).reverse().find((p) => p.y !== null);
    if (!prevValid) return `M ${pt.x} ${pt.y}`;
    return `${acc} L ${pt.x} ${pt.y}`;
  }, '');

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <LineChartIcon className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Regional Monthly Time-Series Movement</span>
        </div>
        <div className="text-xs text-[var(--text-muted)] font-mono font-medium">
          Scope: {regionName || 'All Regions'} ({series.length} Months)
        </div>
      </div>

      {/* SVG Chart Container */}
      <div className="relative">
        <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} className="w-full h-auto overflow-visible select-none">
          {/* Gridlines */}
          {[0, 0.5, 1].map((ratio) => {
            const y = padding.top + ratio * (svgHeight - padding.top - padding.bottom);
            const val = maxVal - ratio * valRange;
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={svgWidth - padding.right}
                  y2={y}
                  stroke="var(--border-subtle)"
                  strokeDasharray="4 4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-[var(--text-muted)] text-[10px] font-mono"
                >
                  {Math.round(val).toLocaleString('en-IN')}
                </text>
              </g>
            );
          })}

          {/* Line Path */}
          {pathD && (
            <motion.path
              d={pathD}
              fill="none"
              stroke="var(--teal-600)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              initial={shouldReduceMotion ? { pathLength: 1 } : { pathLength: 0 }}
              animate={{ pathLength: 1 }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          )}

          {/* Data Points */}
          {points.map((pt) => {
            if (pt.y === null) {
              return (
                <g
                  key={pt.reporting_month}
                  onMouseEnter={() => setHoveredPoint(pt)}
                  onMouseLeave={() => setHoveredPoint(null)}
                  className="cursor-pointer"
                >
                  <circle
                    cx={pt.x}
                    cy={padding.top + (svgHeight - padding.top - padding.bottom) / 2}
                    r="5"
                    fill="var(--bg-surface)"
                    stroke="var(--amber-600)"
                    strokeWidth="2"
                    strokeDasharray="2 2"
                  />
                  <text
                    x={pt.x}
                    y={svgHeight - 10}
                    textAnchor="middle"
                    className="fill-[var(--amber-700)] text-[9px] font-mono font-bold"
                  >
                    {pt.reporting_month}
                  </text>
                </g>
              );
            }

            const isHovered = hoveredPoint?.reporting_month === pt.reporting_month;

            return (
              <g
                key={pt.reporting_month}
                onMouseEnter={() => setHoveredPoint(pt)}
                onMouseLeave={() => setHoveredPoint(null)}
                className="cursor-pointer"
              >
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isHovered ? '6' : '4'}
                  fill={isHovered ? 'var(--teal-700)' : 'var(--bg-surface)'}
                  stroke="var(--teal-600)"
                  strokeWidth="2"
                  className="transition-all duration-150"
                />
                <text
                  x={pt.x}
                  y={svgHeight - 10}
                  textAnchor="middle"
                  className="fill-[var(--text-muted)] text-[9px] font-mono"
                >
                  {pt.reporting_month}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Overlay */}
        {hoveredPoint && (
          <div
            className="absolute z-10 bg-[var(--bg-surface)] border border-[var(--border-default)] rounded-xl p-3 shadow-lg text-xs pointer-events-none -translate-x-1/2 -translate-y-full mb-2"
            style={{ left: '50%', top: '20%' }}
          >
            <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-[var(--text-muted)]">
              <Calendar className="w-3 h-3 text-[var(--teal-600)]" />
              <span>{hoveredPoint.reporting_month}</span>
            </div>
            <div className="text-sm font-extrabold font-display text-[var(--text-primary)] mt-1">
              {hoveredPoint.total_value.toLocaleString('en-IN')} Total Attendance
            </div>
            <div className="text-[10px] text-[var(--text-secondary)] mt-0.5">
              Reporting Coverage: {hoveredPoint.reporting_facilities} Facilities
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
