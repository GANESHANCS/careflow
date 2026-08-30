import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { LineChart as LineChartIcon, Calendar, Building2, Layers } from 'lucide-react';
import type { AnalyticsTrendsResponse, MonthlyTrendPoint } from '../../api/types';

interface TrendChartProps {
  data: AnalyticsTrendsResponse | null;
  loading: boolean;
  error?: string | null;
  title?: string;
  subtitle?: string;
}

export const TrendChart: React.FC<TrendChartProps> = ({
  data,
  loading,
  error,
  title = 'Monthly Healthcare Attendance Movement',
  subtitle = 'Consolidated time-series trend line across reporting months',
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<MonthlyTrendPoint | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const shouldReduceMotion = useReducedMotion();

  const series = data?.series ?? [];
  const hasData = series.length > 0;

  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse">
        <div className="h-4 w-48 bg-[var(--bg-surface-active)] rounded mb-4" />
        <div className="h-64 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--coral-100)] rounded-2xl p-6 shadow-xs text-center text-xs text-[var(--coral-700)]">
        <p className="font-semibold">Unable to load time-series trend data.</p>
        <p className="text-[var(--text-muted)] mt-1">{error}</p>
      </div>
    );
  }

  if (!hasData) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 shadow-xs text-center">
        <div className="w-12 h-12 rounded-2xl bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] flex items-center justify-center text-[var(--text-muted)] mx-auto mb-3">
          <LineChartIcon className="w-6 h-6" />
        </div>
        <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
          No Time-Series Observations Available
        </h3>
        <p className="text-xs text-[var(--text-secondary)] mt-1 max-w-md mx-auto">
          Time-series trends will populate automatically once monthly HMIS facility returns are ingested into the database.
        </p>
      </div>
    );
  }

  // Calculate SVG dimensions and scale coordinates
  const width = 800;
  const height = 300;
  const padding = 40;

  const minVal = Math.min(...series.map((s) => s.total_value));
  const maxVal = Math.max(...series.map((s) => s.total_value));
  const valRange = maxVal - minVal || 1;

  const points = series.map((pt, i) => {
    const x = padding + (i / Math.max(series.length - 1, 1)) * (width - 2 * padding);
    const y = height - padding - ((pt.total_value - minVal) / valRange) * (height - 2 * padding);
    return { ...pt, x, y };
  });

  const pathD = points.reduce((acc, pt, i) => (i === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`), '');

  const areaD = `${pathD} L ${points[points.length - 1].x} ${height - padding} L ${points[0].x} ${height - padding} Z`;

  // Latest month trend indicator
  const latestPt = points[points.length - 1];
  const firstPt = points[0];
  const totalChangePct = firstPt.total_value > 0 ? ((latestPt.total_value - firstPt.total_value) / firstPt.total_value) * 100 : 0;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs relative overflow-hidden">
      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
            <LineChartIcon className="w-4 h-4 text-[var(--teal-600)]" />
            <span>Analytical Trend Visualization</span>
          </div>
          <h3 className="font-display font-extrabold text-xl text-[var(--text-primary)] tracking-tight mt-0.5">
            {title}
          </h3>
          <p className="text-xs text-[var(--text-secondary)] font-normal">{subtitle}</p>
        </div>

        {/* Editorial Annotation Badge */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[10px] uppercase font-bold text-[var(--text-muted)] tracking-wider">Overall Shift</div>
            <div className={`text-xs font-bold ${totalChangePct >= 0 ? 'text-[var(--green-700)]' : 'text-[var(--coral-700)]'}`}>
              {totalChangePct >= 0 ? `+${totalChangePct.toFixed(1)}%` : `${totalChangePct.toFixed(1)}%`}
            </div>
          </div>
          <div className="text-right border-l border-[var(--border-subtle)] pl-3">
            <div className="text-[10px] uppercase font-bold text-[var(--text-muted)] tracking-wider">Latest Period</div>
            <div className="text-xs font-bold text-[var(--text-primary)]">{latestPt.reporting_month}</div>
          </div>
        </div>
      </div>

      {/* SVG Chart Box */}
      <div className="relative w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-auto min-w-[500px]"
          role="img"
          aria-label={`Time-series trend chart showing monthly attendance for ${data?.filters?.indicator_code || 'healthcare indicators'}`}
        >
          <defs>
            <linearGradient id="trendGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--teal-500)" stopOpacity="0.25" />
              <stop offset="100%" stopColor="var(--teal-500)" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Horizontal Gridlines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = padding + pct * (height - 2 * padding);
            return (
              <line
                key={i}
                x1={padding}
                y1={y}
                x2={width - padding}
                y2={y}
                stroke="var(--border-subtle)"
                strokeDasharray="4 4"
                strokeWidth="1"
              />
            );
          })}

          {/* Area Fill */}
          <path d={areaD} fill="url(#trendGradient)" />

          {/* Animated Line Path */}
          <motion.path
            d={pathD}
            fill="none"
            stroke="var(--teal-600)"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            initial={shouldReduceMotion ? { pathLength: 1 } : { pathLength: 0 }}
            whileInView={{ pathLength: 1 }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
            viewport={{ once: true }}
          />

          {/* Interactive Data Points */}
          {points.map((pt, idx) => (
            <circle
              key={idx}
              cx={pt.x}
              cy={pt.y}
              r={hoveredPoint?.reporting_month === pt.reporting_month ? '6' : '4'}
              fill={hoveredPoint?.reporting_month === pt.reporting_month ? 'var(--teal-700)' : 'var(--bg-surface)'}
              stroke="var(--teal-600)"
              strokeWidth="2.5"
              className="cursor-pointer transition-all duration-150"
              onMouseEnter={(e) => {
                const rect = e.currentTarget.getBoundingClientRect();
                setHoveredPoint(pt);
                setTooltipPos({ x: rect.left + rect.width / 2, y: rect.top });
              }}
              onMouseLeave={() => setHoveredPoint(null)}
              tabIndex={0}
              role="button"
              aria-label={`Reporting month ${pt.reporting_month}: ${pt.total_value.toLocaleString('en-IN')}`}
            />
          ))}

          {/* X Axis Month Labels */}
          {points.map((pt, idx) => (
            <text
              key={idx}
              x={pt.x}
              y={height - 12}
              textAnchor="middle"
              className="text-[10px] font-medium fill-[var(--text-muted)] font-body"
            >
              {pt.reporting_month}
            </text>
          ))}
        </svg>

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <div
            className="fixed z-50 pointer-events-none -translate-x-1/2 -translate-y-full mb-3 bg-[var(--text-primary)] text-white p-3 rounded-lg shadow-lg text-xs font-medium space-y-1"
            style={{ left: `${tooltipPos.x}px`, top: `${tooltipPos.y}px` }}
          >
            <div className="flex items-center justify-between border-b border-slate-700 pb-1 text-[11px] text-slate-300">
              <span className="flex items-center gap-1 font-semibold text-teal-300">
                <Calendar className="w-3 h-3" />
                <span>{hoveredPoint.reporting_month}</span>
              </span>
              <span>{hoveredPoint.observation_date}</span>
            </div>
            <div className="text-sm font-bold font-display text-white">
              {hoveredPoint.total_value.toLocaleString('en-IN')}
            </div>
            <div className="text-[10px] text-slate-300 flex items-center justify-between gap-3 pt-1 border-t border-slate-700/50">
              <span className="flex items-center gap-1">
                <Building2 className="w-3 h-3 text-sky-400" />
                <span>Facilities: {hoveredPoint.reporting_facilities} / {hoveredPoint.total_facilities}</span>
              </span>
              <span className="flex items-center gap-1">
                <Layers className="w-3 h-3 text-emerald-400" />
                <span>{hoveredPoint.completeness_pct}%</span>
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Accessible Text Summary for Screen Readers */}
      <div className="sr-only">
        Overall trend for {data?.filters?.indicator_code || 'health indicator'} over {series.length} months. Latest observation in {latestPt.reporting_month} recorded {latestPt.total_value.toLocaleString('en-IN')} across {latestPt.reporting_facilities} facilities.
      </div>
    </div>
  );
};
