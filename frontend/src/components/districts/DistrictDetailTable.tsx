import React, { useState, useMemo } from 'react';
import { Table, Search, CheckCircle, AlertTriangle, Download } from 'lucide-react';
import type { DistrictTrendObservation } from '../../api/types';

interface DistrictDetailTableProps {
  observations: DistrictTrendObservation[];
  district: string;
  sNo: string;
  parameterName: string;
  onExportCsv?: () => void;
  isExporting?: boolean;
}

export const DistrictDetailTable: React.FC<DistrictDetailTableProps> = ({
  observations,
  district,
  sNo,
  parameterName,
  onExportCsv,
  isExporting = false,
}) => {
  const [filterQuery, setFilterQuery] = useState('');

  const filteredObservations = useMemo(() => {
    if (!filterQuery.trim()) return observations;
    const q = filterQuery.toLowerCase();
    return observations.filter(
      (obs) =>
        obs.reporting_month.toLowerCase().includes(q) ||
        (obs.subgroup_type && obs.subgroup_type.toLowerCase().includes(q)) ||
        (obs.source_file && obs.source_file.toLowerCase().includes(q))
    );
  }, [observations, filterQuery]);

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-7 shadow-xs space-y-5">
      {/* Table Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Table className="w-4 h-4 text-[var(--teal-600)]" />
            <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
              Raw Observation Record Log — {district}
            </h3>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-0.5">
            Code: {sNo} — {parameterName}
          </p>
        </div>

        {/* Filter within table & Export Action */}
        <div className="flex items-center gap-3">
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search month or subgroup..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] focus-ring"
            />
          </div>

          {onExportCsv && (
            <button
              onClick={onExportCsv}
              disabled={isExporting}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white font-medium rounded-xl text-xs transition-colors cursor-pointer disabled:opacity-50 shrink-0 shadow-xs"
              title="Download filtered observation rows as RFC 4180 CSV"
            >
              <Download className="w-3.5 h-3.5 text-teal-300" />
              <span>{isExporting ? 'Exporting...' : 'Export CSV'}</span>
            </button>
          )}
        </div>
      </div>

      {/* Observations Table */}
      <div className="overflow-x-auto border border-[var(--border-subtle)] rounded-xl">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-[var(--bg-surface-subtle)] border-b border-[var(--border-subtle)] text-[var(--text-muted)] uppercase tracking-wider font-bold">
              <th className="py-2.5 px-3">Reporting Period</th>
              <th className="py-2.5 px-3">Subgroup Slice</th>
              <th className="py-2.5 px-3 text-right">Reported Value</th>
              <th className="py-2.5 px-3 text-center">Value Classification</th>
              <th className="py-2.5 px-3">Source Row</th>
              <th className="py-2.5 px-3">Source File & Job</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-subtle)]">
            {filteredObservations.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-[var(--text-muted)]">
                  No observation records match the query.
                </td>
              </tr>
            ) : (
              filteredObservations.map((obs, idx) => {
                const isMissing = obs.value_type === 'MISSING' || obs.value === null;
                const isZero = obs.value_type === 'ZERO' || obs.value === 0;

                return (
                  <tr key={`${obs.reporting_month}-${idx}`} className="hover:bg-[var(--bg-surface-subtle)] transition-colors">
                    <td className="py-2.5 px-3 font-mono font-bold text-[var(--text-primary)]">
                      {obs.reporting_month}
                    </td>
                    <td className="py-2.5 px-3 text-[var(--text-secondary)]">
                      {obs.subgroup_type || 'Total / Aggregate'}
                    </td>
                    <td className="py-2.5 px-3 text-right font-mono font-extrabold text-[var(--text-primary)]">
                      {isMissing ? (
                        <span className="text-amber-600 font-sans font-semibold text-[11px]">Null</span>
                      ) : (
                        obs.value?.toLocaleString()
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      {isMissing ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
                          <AlertTriangle className="w-2.5 h-2.5 text-amber-600" />
                          Missing / Absent
                        </span>
                      ) : isZero ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-700 border border-slate-300">
                          Zero Activity (0)
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                          <CheckCircle className="w-2.5 h-2.5 text-emerald-600" />
                          Valid Numeric
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[var(--text-muted)]">
                      #{obs.source_row ?? 'N/A'}
                    </td>
                    <td className="py-2.5 px-3 text-[11px] text-[var(--text-muted)] font-mono truncate max-w-xs" title={obs.source_file ?? ''}>
                      {obs.source_file ? obs.source_file.split(/[/\\]/).pop() : 'N/A'}
                      {obs.last_import_job_id ? ` [Job #${obs.last_import_job_id}]` : ''}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      <div className="text-[11px] text-[var(--text-muted)] flex items-center justify-between">
        <span>Showing {filteredObservations.length} of {observations.length} monthly observations</span>
        <span>Reversible Wide-to-Long HMIS Ingestion</span>
      </div>
    </div>
  );
};
