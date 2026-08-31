import React, { useState, useMemo } from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, ArrowUpDown, Building2, MapPin, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { RegionMetricPoint } from '../../api/types';

interface RegionalRankingProps {
  regions: RegionMetricPoint[];
  level: 'state' | 'district';
  onSelectRegion?: (regionName: string) => void;
}

type SortKey = 'utilization' | 'avg_facility' | 'completeness' | 'mom';

export const RegionalRanking: React.FC<RegionalRankingProps> = ({
  regions,
  level,
  onSelectRegion,
}) => {
  const [sortKey, setSortKey] = useState<SortKey>('utilization');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const sortedRegions = useMemo(() => {
    return [...regions].sort((a, b) => {
      let valA = 0;
      let valB = 0;

      if (sortKey === 'utilization') {
        valA = a.total_utilization || 0;
        valB = b.total_utilization || 0;
      } else if (sortKey === 'avg_facility') {
        valA = a.average_per_reporting_facility || 0;
        valB = b.average_per_reporting_facility || 0;
      } else if (sortKey === 'completeness') {
        valA = a.completeness_pct || 0;
        valB = b.completeness_pct || 0;
      } else if (sortKey === 'mom') {
        valA = a.mom_change_pct || 0;
        valB = b.mom_change_pct || 0;
      }

      return sortAsc ? valA - valB : valB - valA;
    });
  }, [regions, sortKey, sortAsc]);

  const maxUtilization = useMemo(() => {
    const vals = regions.map((r) => r.total_utilization || 0);
    return vals.length > 0 ? Math.max(...vals) : 1;
  }, [regions]);

  const handleSortChange = (key: SortKey) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(false);
    }
  };

  const getMoMBadge = (pct: number | null) => {
    if (pct === null) return null;
    const isPositive = pct > 0;
    const isNegative = pct < 0;

    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold ${
          isPositive
            ? 'bg-[var(--green-50)] text-[var(--green-700)] border border-[var(--green-100)]'
            : isNegative
            ? 'bg-[var(--coral-50)] text-[var(--coral-700)] border border-[var(--coral-100)]'
            : 'bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)] border border-[var(--border-subtle)]'
        }`}
      >
        {isPositive ? (
          <TrendingUp className="w-3 h-3 text-[var(--green-600)]" />
        ) : isNegative ? (
          <TrendingDown className="w-3 h-3 text-[var(--coral-600)]" />
        ) : (
          <Minus className="w-3 h-3" />
        )}
        <span>{pct > 0 ? `+${pct.toFixed(1)}%` : `${pct.toFixed(1)}%`}</span>
      </span>
    );
  };

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs">
      {/* Header & Sort Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[var(--teal-700)]">
            <MapPin className="w-4 h-4 text-[var(--teal-600)]" />
            <span>Spatial Ranked Intelligence ({level === 'state' ? 'State Level' : 'District Level'})</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            Geographic comparison sorted by relative utilization volume and reporting completeness.
          </p>
        </div>

        {/* Sort Pill Controls */}
        <div className="flex flex-wrap items-center gap-1.5 bg-[var(--bg-surface-subtle)] p-1 rounded-xl border border-[var(--border-subtle)]">
          <span className="text-[10px] font-bold uppercase text-[var(--text-muted)] px-2">Sort By:</span>
          {(
            [
              ['utilization', 'Utilization'],
              ['avg_facility', 'Avg/Facility'],
              ['completeness', 'Completeness'],
              ['mom', 'MoM Growth'],
            ] as const
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => handleSortChange(key)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg transition-colors cursor-pointer focus-ring flex items-center gap-1 ${
                sortKey === key
                  ? 'bg-[var(--bg-surface)] text-[var(--teal-700)] shadow-2xs border border-[var(--border-subtle)]'
                  : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              <span>{label}</span>
              {sortKey === key && <ArrowUpDown className="w-3 h-3 text-[var(--teal-600)]" />}
            </button>
          ))}
        </div>
      </div>

      {/* Ranked Editorial List */}
      <div className="space-y-4">
        {sortedRegions.map((reg, idx) => {
          const rankNum = String(idx + 1).padStart(2, '0');
          const pctWidth = Math.min(100, Math.max(8, (reg.total_utilization / maxUtilization) * 100));

          return (
            <div
              key={reg.region_name}
              onClick={() => onSelectRegion?.(reg.region_name)}
              className="group bg-[var(--bg-surface-subtle)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-subtle)] hover:border-[var(--teal-500)] rounded-xl p-4 sm:p-5 transition-all duration-200 cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              {/* Left Column: Rank + Name + Coverage */}
              <div className="flex items-start gap-4 flex-1">
                <span className="font-display font-extrabold text-lg sm:text-xl text-[var(--teal-700)] bg-[var(--teal-50)] border border-[var(--teal-100)] w-10 h-10 rounded-xl flex items-center justify-center shrink-0">
                  {rankNum}
                </span>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-display font-bold text-base text-[var(--text-primary)] group-hover:text-[var(--teal-700)] transition-colors truncate">
                      {reg.region_name}
                    </h3>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-subtle)] shrink-0">
                      {level}
                    </span>
                  </div>

                  {/* Relative Progress Bar */}
                  <div className="w-full bg-[var(--bg-surface)] rounded-full h-2 overflow-hidden border border-[var(--border-subtle)] my-2">
                    <div
                      className="bg-[var(--teal-600)] h-full rounded-full transition-all duration-500"
                      style={{ width: `${pctWidth}%` }}
                    />
                  </div>

                  <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--text-muted)] font-medium">
                    <span className="flex items-center gap-1 text-[var(--text-secondary)]">
                      <Building2 className="w-3.5 h-3.5 text-[var(--teal-600)] shrink-0" />
                      <span>{reg.reporting_facilities} / {reg.total_facilities} Facilities Reporting</span>
                    </span>
                    <span>•</span>
                    <span className="font-semibold text-[var(--teal-700)]">
                      {reg.completeness_pct.toFixed(1)}% Completeness
                    </span>
                  </div>
                </div>
              </div>

              {/* Right Column: Values & Actions */}
              <div className="flex items-center justify-between md:justify-end gap-6 pt-3 md:pt-0 border-t md:border-t-0 border-[var(--border-subtle)] shrink-0">
                <div className="text-right">
                  <div className="text-[10px] font-bold uppercase text-[var(--text-muted)]">
                    Total Attendance
                  </div>
                  <div className="text-xl font-extrabold font-display text-[var(--text-primary)] mt-0.5">
                    {reg.total_utilization.toLocaleString('en-IN')}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-[10px] font-bold uppercase text-[var(--text-muted)]">
                    Avg / Facility
                  </div>
                  <div className="text-sm font-bold font-display text-[var(--text-secondary)] mt-0.5">
                    {reg.average_per_reporting_facility.toLocaleString('en-IN')}
                  </div>
                  {getMoMBadge(reg.mom_change_pct)}
                </div>

                <NavLink
                  to={`/facilities?${level === 'state' ? `state=${encodeURIComponent(reg.region_name)}` : `district=${encodeURIComponent(reg.region_name)}`}`}
                  className="p-2 rounded-lg bg-[var(--bg-surface)] group-hover:bg-[var(--teal-700)] group-hover:text-white transition-colors focus-ring shrink-0"
                  aria-label={`Inspect facilities in ${reg.region_name}`}
                  onClick={(e) => e.stopPropagation()}
                >
                  <ArrowRight className="w-4 h-4" />
                </NavLink>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
