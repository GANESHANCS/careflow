import React from 'react';
import { Clock, Info } from 'lucide-react';
import type { MonthlyQualityPoint } from '../../api/types';

interface QualityTimelineProps {
  timeline: MonthlyQualityPoint[];
}

export const QualityTimeline: React.FC<QualityTimelineProps> = ({ timeline = [] }) => {
  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2 font-display">
            <Clock className="w-5 h-5 text-[var(--purple-600)]" />
            Historical Monthly Reporting Continuity Timeline
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Chronological audit tracking reporting completeness and flagged quality events across monthly return cycles.
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-3 text-xs font-bold text-[var(--text-muted)] self-start sm:self-auto">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--teal-600)] inline-block" />
            Reported
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--coral-500)] inline-block" />
            Missing
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-[var(--amber-500)] inline-block" />
            Flagged (!)
          </span>
        </div>
      </div>

      {timeline.length > 0 ? (
        <div className="space-y-6">
          {/* Timeline Grid Bars */}
          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-12 gap-2">
            {timeline.map((point) => {
              let barBg = 'bg-[var(--teal-500)]';
              let badgeColor = 'text-[var(--teal-700)]';
              let symbol = '●';

              if (point.status === 'CRITICAL' || point.completeness_pct < 60) {
                barBg = 'bg-[var(--coral-600)]';
                badgeColor = 'text-[var(--coral-700)]';
                symbol = '○';
              } else if (point.status === 'WARNING' || point.issue_count > 0 || point.completeness_pct < 85) {
                barBg = 'bg-[var(--amber-500)]';
                badgeColor = 'text-[var(--amber-700)]';
                symbol = '!';
              }

              return (
                <div
                  key={point.reporting_month}
                  className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] hover:border-[var(--purple-300)] rounded-2xl p-3 text-center transition-all cursor-pointer group relative"
                >
                  <span className="text-[11px] font-mono font-bold text-[var(--text-primary)] block mb-1">
                    {point.reporting_month}
                  </span>

                  <div className="w-full bg-[var(--bg-surface)] h-2 rounded-full overflow-hidden border border-[var(--border-subtle)] my-2">
                    <div className={`h-full ${barBg}`} style={{ width: `${point.completeness_pct}%` }} />
                  </div>

                  <div className="flex items-center justify-between text-[10px] font-mono font-bold">
                    <span className={badgeColor}>{symbol} {point.completeness_pct.toFixed(0)}%</span>
                    {point.issue_count > 0 && (
                      <span className="px-1 py-0.2 rounded bg-[var(--amber-100)] text-[var(--amber-900)]">
                        !{point.issue_count}
                      </span>
                    )}
                  </div>

                  {/* Tooltip on Hover */}
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute left-1/2 bottom-full -translate-x-1/2 mb-2 w-44 p-2.5 bg-gray-900 text-white text-[10px] rounded-xl shadow-lg pointer-events-none z-20 space-y-1 text-left">
                    <div className="font-bold border-b border-gray-700 pb-1 text-teal-300">
                      Month: {point.reporting_month}
                    </div>
                    <div>Reporting: {point.reporting_facilities} / {point.total_facilities} Facilities</div>
                    <div>Completeness: {point.completeness_pct}%</div>
                    <div>Flagged Logs: {point.issue_count}</div>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-3 text-[11px] text-[var(--text-muted)] flex items-center gap-2">
            <Info className="w-4 h-4 text-[var(--teal-600)] shrink-0" />
            <span>
              <strong>Continuity Rule:</strong> Gaps in reporting continuity (e.g. 3 consecutive missing months) trigger a temporal continuity warning in the 13-point governance audit pipeline.
            </span>
          </div>
        </div>
      ) : (
        <div className="text-center py-10 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-2xl">
          <Clock className="w-8 h-8 text-[var(--text-muted)] mx-auto mb-2" />
          <h4 className="text-sm font-bold text-[var(--text-primary)]">Monthly Timeline Data Awaiting Observations</h4>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            Historical reporting continuity timeline will render once multi-month HMIS returns are loaded into SQLite.
          </p>
        </div>
      )}
    </div>
  );
};
