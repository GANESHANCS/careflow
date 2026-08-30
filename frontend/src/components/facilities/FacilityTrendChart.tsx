import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { LineChart as LineChartIcon, Calendar, Layers } from 'lucide-react';
import type { FacilityAnalyticsResponse, FacilityObservationPoint } from '../../api/types';

interface TrendPoint extends FacilityObservationPoint {
  x: number;
  y: number | null;
}

interface FacilityTrendChartProps {
  analytics: FacilityAnalyticsResponse | null;
  loading: boolean;
  selectedIndicator?: string;
  onIndicatorChange?: (code: string) => void;
}

export const FacilityTrendChart: React.FC<FacilityTrendChartProps> = ({
  analytics,
  loading,
}) => {
  const shouldReduceMotion = useReducedMotion();
  const [activeIndicator, setActiveIndicator] = useState<string>('opd_attendance');
  const [hoveredPoint, setHoveredPoint] = useState<TrendPoint | null>(null);

  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-4 w-48 bg-[var(--bg-surface-active)] rounded" />
        <div className="h-64 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  const history = analytics?.history ?? [];

  // Group history by indicator_code
  const availableIndicators = Array.from(new Set(history.map((h) => h.indicator_code)));
  const currentCode = availableIndicators.includes(activeIndicator)
    ? activeIndicator
    : availableIndicators[0] || 'opd_attendance';

  const series = history.filter((h) => h.indicator_code === currentCode);

  if (series.length === 0) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs text-center">
        <div className="text-sm font-bold text-[var(--text-muted)] mb-1">
          No Historical Observations Available
        </div>
        <p className="text-xs text-[var(--text-secondary)]">
          Historical monthly data points for indicator &quot;{currentCode}&quot; have not been ingested for this facility yet.
        </p>
      </div>
    );
  }

  // Calculate SVG dimensions
  const svgWidth = 800;
  const svgHeight = 220;
  const padding = { top: 25, right: 30, bottom: 35, left: 45 };

  const validValues = series
    .map((s) => s.value)
    .filter((v): v is number => typeof v === 'number');

  const minVal = validValues.length > 0 ? Math.min(...validValues) : 0;
  const maxVal = validValues.length > 0 ? Math.max(...validValues) : 100;
  const valRange = maxVal - minVal || 1;

  const points = series.map((pt, idx) => {
    const x =
      padding.left +
      (idx / Math.max(1, series.length - 1)) * (svgWidth - padding.left - padding.right);
    const y =
      typeof pt.value === 'number'
        ? padding.top +
          (1 - (pt.value - minVal) / valRange) * (svgHeight - padding.top - padding.bottom)
        : null;
    return { ...pt, x, y };
  });

  // Construct SVG path string skipping missing points safely
  const pathD = points.reduce((acc, pt, idx) => {
    if (pt.y === null) return acc;
    const prevValid = points.slice(0, idx).reverse().find((p) => p.y !== null);
    if (!prevValid) return `M ${pt.x} ${pt.y}`;
    return `${acc} L ${pt.x} ${pt.y}`;
  }, '');

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Header & Indicator Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
          <LineChartIcon className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Historical Attendance Movement</span>
        </div>

        {availableIndicators.length > 1 && (
          <div className="flex items-center gap-2 text-xs">
            <Layers className="w-3.5 h-3.5 text-[var(--text-muted)]" />
            <select
              value={currentCode}
              onChange={(e) => setActiveIndicator(e.target.value)}
              className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-lg px-2.5 py-1 text-xs text-[var(--text-primary)] font-medium focus-ring cursor-pointer"
              aria-label="Select historical indicator to view"
            >
              {availableIndicators.map((code) => {
                const item = history.find((h) => h.indicator_code === code);
                return (
                  <option key={code} value={code}>
                    {item?.indicator_name || code}
                  </option>
                );
              })}
            </select>
          </div>
        )}
      </div>

      {/* SVG Chart Container */}
      <div className="relative">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto overflow-visible select-none"
        >
          {/* Horizontal Gridlines */}
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
              // Missing Observation Marker (Open Circle ○)
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
            style={{
              left: `${((hoveredPoint.x - padding.left) / (svgWidth - padding.left - padding.right)) * 80 + 10}%`,
              top: '20%',
            }}
          >
            <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase text-[var(--text-muted)]">
              <Calendar className="w-3 h-3 text-[var(--teal-600)]" />
              <span>{hoveredPoint.reporting_month}</span>
            </div>
            <div className="text-sm font-extrabold font-display text-[var(--text-primary)] mt-1">
              {typeof hoveredPoint.value === 'number' ? (
                `${hoveredPoint.value.toLocaleString('en-IN')} ${hoveredPoint.indicator_name}`
              ) : (
                <span className="text-[var(--amber-700)] font-semibold">Missing Return (○)</span>
              )}
            </div>
            {typeof hoveredPoint.value !== 'number' && (
              <p className="text-[10px] text-[var(--text-secondary)] mt-0.5">
                Return missing in raw HMIS batch. Preserved as non-zero missing observation.
              </p>
            )}
          </div>
        )}
      </div>

      {/* Legend Note */}
      <div className="flex items-center justify-between border-t border-[var(--border-subtle)] pt-3 mt-4 text-[10px] text-[var(--text-muted)]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--bg-surface)] border-2 border-[var(--teal-600)] inline-block" />
            <span>● Verified Observation</span>
          </span>
          <span className="flex items-center gap-1.5 font-medium text-[var(--amber-700)]">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--bg-surface)] border-2 border-[var(--amber-600)] stroke-dasharray-2 inline-block" />
            <span>○ Preserved Missing Month (Data Gaps $\neq$ Zero Utilization)</span>
          </span>
        </div>
      </div>
    </div>
  );
};
