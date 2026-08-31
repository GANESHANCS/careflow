import React, { useState, useMemo } from 'react';
import { ShieldAlert, AlertTriangle, AlertCircle, Info, Search, CheckCircle2 } from 'lucide-react';
import type { DataQualityIssueItem } from '../../api/types';

interface QualityIssueTableProps {
  issues: DataQualityIssueItem[];
  selectedSeverity?: string;
  onSelectSeverity?: (sev: string) => void;
}

export const QualityIssueTable: React.FC<QualityIssueTableProps> = ({
  issues = [],
  selectedSeverity = 'ALL',
  onSelectSeverity,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredIssues = useMemo(() => {
    return (issues || []).filter((issue) => {
      const matchSeverity = selectedSeverity === 'ALL' || issue.severity.toUpperCase() === selectedSeverity.toUpperCase();
      const matchSearch =
        !searchTerm ||
        issue.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
        issue.description.toLowerCase().includes(searchTerm.toLowerCase());
      return matchSeverity && matchSearch;
    });
  }, [issues, selectedSeverity, searchTerm]);

  const getSeverityBadge = (sev: string) => {
    const s = sev.toUpperCase();
    if (s === 'CRITICAL') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-[var(--coral-100)] text-[var(--coral-800)] border border-[var(--coral-300)] text-[10px] font-extrabold uppercase font-mono">
          <ShieldAlert className="w-3 h-3 text-[var(--coral-600)]" />
          CRITICAL
        </span>
      );
    }
    if (s === 'ERROR') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-[var(--coral-50)] text-[var(--coral-700)] border border-[var(--coral-200)] text-[10px] font-extrabold uppercase font-mono">
          <AlertCircle className="w-3 h-3 text-[var(--coral-600)]" />
          ERROR
        </span>
      );
    }
    if (s === 'WARNING') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-[var(--amber-100)] text-[var(--amber-800)] border border-[var(--amber-300)] text-[10px] font-extrabold uppercase font-mono">
          <AlertTriangle className="w-3 h-3 text-[var(--amber-600)]" />
          WARNING
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-[var(--blue-50)] text-[var(--blue-700)] border border-[var(--blue-200)] text-[10px] font-extrabold uppercase font-mono">
        <Info className="w-3 h-3 text-[var(--blue-600)]" />
        INFO
      </span>
    );
  };

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs mb-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2 font-display">
            <ShieldAlert className="w-5 h-5 text-[var(--purple-600)]" />
            13-Point Pipeline Audit Issue Registry
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Operational issue log detailing affected records, severity classifications, and descriptions.
          </p>
        </div>

        {/* Toolbar Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Filter */}
          <div className="relative min-w-[200px]">
            <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search category or description..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl pl-8 pr-3 py-1.5 text-xs text-[var(--text-primary)] font-medium focus-ring"
              aria-label="Search data quality issues"
            />
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-1 bg-[var(--bg-surface-subtle)] p-1 rounded-xl border border-[var(--border-subtle)]">
            {['ALL', 'CRITICAL', 'WARNING', 'INFO'].map((sev) => (
              <button
                key={sev}
                onClick={() => onSelectSeverity && onSelectSeverity(sev)}
                className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all cursor-pointer ${
                  selectedSeverity === sev
                    ? 'bg-[var(--purple-600)] text-white shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
                }`}
                aria-label={`Filter issues by severity ${sev}`}
              >
                {sev}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Issues Table */}
      {filteredIssues.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] uppercase tracking-wider text-[10px] font-bold bg-[var(--bg-surface-subtle)]">
                <th className="py-3 px-4 rounded-l-xl">Severity</th>
                <th className="py-3 px-4">Audit Timestamp</th>
                <th className="py-3 px-4">Issue Category</th>
                <th className="py-3 px-4 text-right">Affected Records</th>
                <th className="py-3 px-4 rounded-r-xl">Audit Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-subtle)]">
              {filteredIssues.map((issue) => (
                <tr key={issue.id} className="hover:bg-[var(--purple-50)]/40 transition-colors">
                  <td className="py-3.5 px-4 whitespace-nowrap">{getSeverityBadge(issue.severity)}</td>
                  <td className="py-3.5 px-4 font-mono text-[var(--text-muted)] whitespace-nowrap">
                    {issue.audit_timestamp.split('T')[0] || issue.audit_timestamp}
                  </td>
                  <td className="py-3.5 px-4 font-bold text-[var(--text-primary)]">{issue.category}</td>
                  <td className="py-3.5 px-4 text-right font-mono font-bold text-[var(--purple-700)]">
                    {issue.affected_records.toLocaleString()}
                  </td>
                  <td className="py-3.5 px-4 text-[var(--text-muted)] leading-relaxed">{issue.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-12 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-2xl">
          <CheckCircle2 className="w-8 h-8 text-[var(--teal-600)] mx-auto mb-2" />
          <h4 className="text-sm font-bold text-[var(--text-primary)]">No Audit Logs Match Active Filter</h4>
          <p className="text-xs text-[var(--text-muted)] mt-1">
            All 13 pipeline quality checks passed without raising flags for the selected criteria.
          </p>
        </div>
      )}
    </div>
  );
};
