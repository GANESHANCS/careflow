import React, { useState, useId } from 'react';
import type { HistoricalPoint, ForecastPoint } from '../../api/types';

interface ForecastChartProps {
  historicalPoints?: HistoricalPoint[];
  forecastPoints: ForecastPoint[];
  indicatorName?: string;
  unit?: string;
  isEligible?: boolean;
}

export const ForecastChart: React.FC<ForecastChartProps> = ({
  historicalPoints = [],
  forecastPoints = [],
  indicatorName = 'Attendance',
  unit = 'count',
  isEligible = true,
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const chartId = useId();

  const safeHistorical = Array.isArray(historicalPoints) ? historicalPoints : [];
  const safeForecast = Array.isArray(forecastPoints) ? forecastPoints : [];

  // Combine timelines for layout
  interface TimelinePoint {
    month: string;
    date: string;
    type: 'historical' | 'forecast';
    value: number | null;
    lowerBound?: number;
    upperBound?: number;
    isMissing?: boolean;
    isImputed?: boolean;
  }

  const timeline: TimelinePoint[] = [];

  safeHistorical.forEach((h) => {
    timeline.push({
      month: h.observation_month,
      date: h.observation_date,
      type: 'historical',
      value: h.observed_value,
      isMissing: h.is_missing,
      isImputed: h.is_imputed,
    });
  });

  safeForecast.forEach((f) => {
    timeline.push({
      month: f.forecast_month,
      date: f.forecast_date,
      type: 'forecast',
      value: f.predicted_value,
      lowerBound: f.lower_bound,
      upperBound: f.upper_bound,
    });
  });

  if (timeline.length === 0) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 text-center text-[var(--text-muted)] text-xs">
        No observation data available to display chart.
      </div>
    );
  }

  // Calculate Y min/max bounds across historical, forecast, and prediction interval bounds
  const validValues: number[] = [];

  timeline.forEach((pt) => {
    if (pt.value !== null && pt.value !== undefined) validValues.push(pt.value);
    if (pt.lowerBound !== undefined) validValues.push(pt.lowerBound);
    if (pt.upperBound !== undefined) validValues.push(pt.upperBound);
  });

  const rawMin = validValues.length > 0 ? Math.min(...validValues) : 0;
  const rawMax = validValues.length > 0 ? Math.max(...validValues) : 100;
  const yMin = Math.max(0, Math.floor(rawMin * 0.9));
  const yMax = Math.ceil(rawMax * 1.1);
  const yRange = Math.max(1, yMax - yMin);

  // Dimensions
  const svgWidth = 900;
  const svgHeight = 360;
  const paddingLeft = 60;
  const paddingRight = 40;
  const paddingTop = 30;
  const paddingBottom = 50;

  const chartWidth = svgWidth - paddingLeft - paddingRight;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  const getX = (index: number) => {
    if (timeline.length <= 1) return paddingLeft + chartWidth / 2;
    return paddingLeft + (index / (timeline.length - 1)) * chartWidth;
  };

  const getY = (val: number) => {
    return paddingTop + chartHeight - ((val - yMin) / yRange) * chartHeight;
  };

  // Find index split where forecast begins
  const forecastStartIndex = timeline.findIndex((pt) => pt.type === 'forecast');

  // Build SVG path strings
  // 1. Historical Path (solid teal)
  const historicalPathPoints: string[] = [];
  let isConnectingHist = false;

  safeHistorical.forEach((h, idx) => {
    if (h.observed_value !== null && h.observed_value !== undefined && !h.is_missing) {
      const x = getX(idx);
      const y = getY(h.observed_value);
      if (!isConnectingHist) {
        historicalPathPoints.push(`M ${x} ${y}`);
        isConnectingHist = true;
      } else {
        historicalPathPoints.push(`L ${x} ${y}`);
      }
    } else {
      isConnectingHist = false; // Do not connect line through missing periods!
    }
  });

  // Connect last historical valid point to first forecast point if available
  const lastHistIdx = safeHistorical.map((h, i) => (h.observed_value !== null && !h.is_missing ? i : -1)).filter((i) => i >= 0).pop();

  // 2. Forecast Path (dashed purple)
  const forecastPathPoints: string[] = [];

  if (lastHistIdx !== undefined && safeForecast.length > 0) {
    const startX = getX(lastHistIdx);
    const startY = getY(safeHistorical[lastHistIdx].observed_value!);
    forecastPathPoints.push(`M ${startX} ${startY}`);
  }

  safeForecast.forEach((f, idx) => {
    const globalIdx = safeHistorical.length + idx;
    const x = getX(globalIdx);
    const y = getY(f.predicted_value);
    if (forecastPathPoints.length === 0) {
      forecastPathPoints.push(`M ${x} ${y}`);
    } else {
      forecastPathPoints.push(`L ${x} ${y}`);
    }
  });

  // 3. Prediction Interval Area Path (upper bounds forward, lower bounds backward)
  const intervalPathPoints: string[] = [];

  if (lastHistIdx !== undefined && safeForecast.length > 0) {
    const startX = getX(lastHistIdx);
    const startY = getY(safeHistorical[lastHistIdx].observed_value!);
    intervalPathPoints.push(`M ${startX} ${startY}`);
  }

  // Forward upper bounds
  safeForecast.forEach((f, idx) => {
    const globalIdx = safeHistorical.length + idx;
    const x = getX(globalIdx);
    const y = getY(f.upper_bound);
    if (intervalPathPoints.length === 0) {
      intervalPathPoints.push(`M ${x} ${y}`);
    } else {
      intervalPathPoints.push(`L ${x} ${y}`);
    }
  });

  // Backward lower bounds
  for (let idx = safeForecast.length - 1; idx >= 0; idx--) {
    const f = safeForecast[idx];
    const globalIdx = safeHistorical.length + idx;
    const x = getX(globalIdx);
    const y = getY(f.lower_bound);
    intervalPathPoints.push(`L ${x} ${y}`);
  }

  intervalPathPoints.push('Z');

  // Selected point for tooltip
  const activePt = hoverIndex !== null ? timeline[hoverIndex] : null;

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-6 shadow-xs mb-8">
      {/* Title & Legend Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="text-base font-extrabold text-[var(--text-primary)] tracking-tight">
            Demand Trajectory & ~95% Prediction Interval
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Historical observations vs. {safeForecast.length}-month model forecast for {indicatorName} ({unit})
          </p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-xs font-semibold">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-[var(--teal-600)]" />
            <span className="text-[var(--text-primary)]">Historical Actual</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-4 h-0 border-b-2 border-dashed border-[var(--purple-600)]" />
            <span className="text-[var(--text-primary)]">Predicted Demand</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded bg-[var(--purple-200)] border border-[var(--purple-400)]" />
            <span className="text-[var(--text-primary)]">95% Prediction Band</span>
          </div>
        </div>
      </div>

      {/* Responsive SVG Container */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto text-xs select-none"
          aria-labelledby={`${chartId}-title`}
          role="img"
        >
          <title id={`${chartId}-title`}>
            Healthcare demand forecast line chart showing {safeHistorical.length} historical months and {safeForecast.length} forecast months.
          </title>

          {/* Grid Lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const y = paddingTop + chartHeight * ratio;
            const val = Math.round(yMax - ratio * yRange);
            return (
              <g key={ratio}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={svgWidth - paddingRight}
                  y2={y}
                  stroke="var(--border-subtle)"
                  strokeDasharray="4,4"
                  strokeWidth="1"
                />
                <text
                  x={paddingLeft - 8}
                  y={y + 4}
                  textAnchor="end"
                  className="fill-[var(--text-muted)] text-[10px] font-medium"
                >
                  {val.toLocaleString()}
                </text>
              </g>
            );
          })}

          {/* Forecast Boundary Marker Line */}
          {forecastStartIndex > 0 && (
            <g>
              <line
                x1={getX(forecastStartIndex - 0.5)}
                y1={paddingTop - 10}
                x2={getX(forecastStartIndex - 0.5)}
                y2={paddingTop + chartHeight + 10}
                stroke="var(--purple-400)"
                strokeDasharray="6,4"
                strokeWidth="1.5"
              />
              <text
                x={getX(forecastStartIndex - 0.5) + 6}
                y={paddingTop + 12}
                className="fill-[var(--purple-700)] text-[10px] font-black uppercase tracking-wider"
              >
                Forecast Horizon Start →
              </text>
            </g>
          )}

          {/* 95% Prediction Interval Shaded Band */}
          {intervalPathPoints.length > 0 && isEligible && (
            <path
              d={intervalPathPoints.join(' ')}
              fill="var(--purple-500)"
              fillOpacity="0.15"
              stroke="var(--purple-400)"
              strokeWidth="1"
              strokeDasharray="3,3"
            />
          )}

          {/* Historical Solid Line */}
          {historicalPathPoints.length > 0 && (
            <path
              d={historicalPathPoints.join(' ')}
              fill="none"
              stroke="var(--teal-600)"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Forecast Dashed Line */}
          {forecastPathPoints.length > 0 && isEligible && (
            <path
              d={forecastPathPoints.join(' ')}
              fill="none"
              stroke="var(--purple-600)"
              strokeWidth="3"
              strokeDasharray="6,6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          )}

          {/* Points & Interactive Nodes */}
          {timeline.map((pt, idx) => {
            const x = getX(idx);
            const isForecast = pt.type === 'forecast';

            if (pt.isMissing) {
              // Draw missing indicator cross
              const y = paddingTop + chartHeight / 2;
              return (
                <g key={idx}>
                  <circle cx={x} cy={y} r="4" fill="var(--amber-100)" stroke="var(--amber-500)" strokeWidth="1.5" />
                  <line x1={x - 2} y1={y - 2} x2={x + 2} y2={y + 2} stroke="var(--amber-700)" strokeWidth="1" />
                </g>
              );
            }

            if (pt.value === null || pt.value === undefined) return null;

            const y = getY(pt.value);
            const isHovered = hoverIndex === idx;

            return (
              <g
                key={idx}
                onMouseEnter={() => setHoverIndex(idx)}
                onMouseLeave={() => setHoverIndex(null)}
                className="cursor-pointer"
              >
                {/* Active Hover Pulse Ring */}
                {isHovered && (
                  <circle
                    cx={x}
                    cy={y}
                    r="10"
                    fill={isForecast ? 'var(--purple-300)' : 'var(--teal-300)'}
                    fillOpacity="0.4"
                  />
                )}

                {/* Point Circle */}
                <circle
                  cx={x}
                  cy={y}
                  r={isHovered ? '6' : '4'}
                  fill={isForecast ? '#ffffff' : 'var(--teal-600)'}
                  stroke={isForecast ? 'var(--purple-700)' : 'var(--teal-800)'}
                  strokeWidth="2.5"
                />
              </g>
            );
          })}

          {/* Crosshair Line on Hover */}
          {hoverIndex !== null && (
            <line
              x1={getX(hoverIndex)}
              y1={paddingTop}
              x2={getX(hoverIndex)}
              y2={paddingTop + chartHeight}
              stroke="var(--text-muted)"
              strokeDasharray="2,2"
              strokeWidth="1"
            />
          )}

          {/* Month Labels (Show subset to avoid overlap) */}
          {timeline.map((pt, idx) => {
            // Show every Nth label depending on timeline length
            const step = Math.ceil(timeline.length / 12);
            if (idx % step !== 0 && idx !== timeline.length - 1) return null;

            const x = getX(idx);
            const isForecast = pt.type === 'forecast';

            return (
              <text
                key={idx}
                x={x}
                y={paddingTop + chartHeight + 20}
                textAnchor="middle"
                className={`text-[10px] font-semibold ${
                  isForecast ? 'fill-[var(--purple-700)] font-bold' : 'fill-[var(--text-muted)]'
                }`}
              >
                {pt.month}
              </text>
            );
          })}
        </svg>

        {/* Hover Floating Tooltip Overlay */}
        {hoverIndex !== null && activePt && (
          <div
            className="absolute z-20 bg-[var(--purple-950)] text-white p-3 rounded-xl shadow-lg border border-[var(--purple-700)] text-xs pointer-events-none transition-all duration-150"
            style={{
              left: `${Math.min(Math.max((getX(hoverIndex) / svgWidth) * 100, 15), 85)}%`,
              top: '20px',
              transform: 'translateX(-50%)',
            }}
          >
            <div className="flex items-center justify-between gap-3 border-b border-[var(--purple-800)] pb-1.5 mb-1.5">
              <span className="font-extrabold text-[var(--purple-300)] uppercase tracking-wider text-[10px]">
                {activePt.month} ({activePt.type.toUpperCase()})
              </span>
              <span
                className={`px-1.5 py-0.5 rounded text-[9px] font-black ${
                  activePt.type === 'forecast' ? 'bg-[var(--purple-600)] text-white' : 'bg-[var(--teal-600)] text-white'
                }`}
              >
                {activePt.type === 'forecast' ? 'MODEL PREDICTION' : 'HISTORICAL OBSERVATION'}
              </span>
            </div>

            {activePt.isMissing ? (
              <span className="text-[var(--amber-300)] font-bold">Data Missing for Period</span>
            ) : (
              <div className="space-y-1">
                <div className="flex justify-between gap-4">
                  <span className="text-[var(--purple-200)]">Value:</span>
                  <span className="font-extrabold text-white">
                    {activePt.value !== null ? Math.round(activePt.value).toLocaleString() : 'N/A'} {unit}
                  </span>
                </div>

                {activePt.lowerBound !== undefined && activePt.upperBound !== undefined && (
                  <div className="flex justify-between gap-4 text-[10px] text-[var(--purple-300)] pt-1 border-t border-[var(--purple-800)]">
                    <span>95% Confidence Interval:</span>
                    <span className="font-mono font-bold text-[var(--teal-300)]">
                      [{Math.round(activePt.lowerBound).toLocaleString()} – {Math.round(activePt.upperBound).toLocaleString()}]
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Accessible Text Table Alternative */}
      <details className="mt-4 pt-3 border-t border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">
        <summary className="cursor-pointer font-bold hover:text-[var(--text-primary)]">
          View Accessible Data Table Summary ({timeline.length} months)
        </summary>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] text-[10px] uppercase font-bold text-[var(--text-muted)]">
                <th className="py-1 px-2">Month</th>
                <th className="py-1 px-2">Type</th>
                <th className="py-1 px-2 text-right">Observed / Predicted</th>
                <th className="py-1 px-2 text-right">95% Lower Bound</th>
                <th className="py-1 px-2 text-right">95% Upper Bound</th>
              </tr>
            </thead>
            <tbody>
              {timeline.map((pt, i) => (
                <tr key={i} className="border-b border-[var(--border-subtle)]/50 hover:bg-[var(--bg-surface-subtle)]">
                  <td className="py-1 px-2 font-mono">{pt.month}</td>
                  <td className="py-1 px-2 capitalize">{pt.type}</td>
                  <td className="py-1 px-2 text-right font-bold">
                    {pt.value !== null ? Math.round(pt.value).toLocaleString() : 'Missing'}
                  </td>
                  <td className="py-1 px-2 text-right font-mono">
                    {pt.lowerBound !== undefined ? Math.round(pt.lowerBound).toLocaleString() : '—'}
                  </td>
                  <td className="py-1 px-2 text-right font-mono">
                    {pt.upperBound !== undefined ? Math.round(pt.upperBound).toLocaleString() : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
};
