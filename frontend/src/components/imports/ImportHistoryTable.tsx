import React from 'react';
import { clsx } from 'clsx';
import {
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Clock,
  Search,
  RefreshCw,
  ShieldCheck,
  FileText,
  ChevronLeft,
  ChevronRight,
  Database,
  Loader2,
} from 'lucide-react';
import type { ImportJob, ImportJobStatus } from '../../api/types';
import { Button } from '../buttons/Button';
import { LoadingState } from '../feedback/LoadingState';
import { ErrorState } from '../feedback/ErrorState';

export interface ImportHistoryTableProps {
  jobs: ImportJob[];
  total: number;
  loading: boolean;
  error: string | null;
  currentPage: number;
  pageSize: number;
  selectedStatus: string;
  searchQuery: string;
  onPageChange: (page: number) => void;
  onStatusChange: (status: string) => void;
  onSearchChange: (search: string) => void;
  onRefresh: () => void;
  onInspectQuality: (job: ImportJob) => void;
  onViewErrors: (job: ImportJob) => void;
  className?: string;
}

export const ImportHistoryTable: React.FC<ImportHistoryTableProps> = ({
  jobs,
  total,
  loading,
  error,
  currentPage,
  pageSize,
  selectedStatus,
  searchQuery,
  onPageChange,
  onStatusChange,
  onSearchChange,
  onRefresh,
  onInspectQuality,
  onViewErrors,
  className,
}) => {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const formatTimestamp = (isoString?: string | null) => {
    if (!isoString) return '—';
    try {
      const d = new Date(isoString);
      return d.toLocaleString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      });
    } catch {
      return isoString;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status.toUpperCase() as ImportJobStatus) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--emerald-50)] text-[var(--emerald-800)] border border-[var(--emerald-200)]">
            <CheckCircle2 className="w-3.5 h-3.5 text-[var(--emerald-600)]" />
            COMPLETED
          </span>
        );
      case 'COMPLETED_WITH_WARNINGS':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--amber-50)] text-[var(--amber-800)] border border-[var(--amber-200)]">
            <AlertTriangle className="w-3.5 h-3.5 text-[var(--amber-600)]" />
            WARNINGS
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--teal-50)] text-[var(--teal-800)] border border-[var(--teal-200)]">
            <Loader2 className="w-3.5 h-3.5 animate-spin text-[var(--teal-600)]" />
            PROCESSING
          </span>
        );
      case 'VALIDATED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-sky-50 text-sky-800 border border-sky-200">
            <Clock className="w-3.5 h-3.5 text-sky-600" />
            VALIDATED
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            QUEUED
          </span>
        );
      case 'FAILED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--coral-50)] text-[var(--coral-800)] border border-[var(--coral-200)]">
            <AlertCircle className="w-3.5 h-3.5 text-[var(--coral-600)]" />
            FAILED
          </span>
        );
    }
  };

  return (
    <div className={clsx('w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-xs overflow-hidden flex flex-col', className)}>
      {/* Table Toolbar */}
      <div className="p-5 sm:p-6 border-b border-[var(--border-subtle)] flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 bg-[var(--bg-surface)]">
        <div>
          <h3 className="font-display font-bold text-base sm:text-lg text-[var(--text-primary)]">
            Ingestion History & Audit Registry
          </h3>
          <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-0.5">
            Audit logs, lifecycle verification states, and data quality evaluations across all submitted datasets.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Search Input */}
          <div className="relative min-w-[200px] flex-1 sm:flex-initial">
            <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search filename..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full text-xs pl-9 pr-3 py-2 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] focus-ring text-[var(--text-primary)] placeholder-[var(--text-muted)]"
            />
          </div>

          {/* Status Filter */}
          <select
            value={selectedStatus}
            onChange={(e) => onStatusChange(e.target.value)}
            className="text-xs px-3 py-2 rounded-lg bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] focus-ring text-[var(--text-primary)] font-medium"
            aria-label="Filter by status"
          >
            <option value="ALL">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="COMPLETED_WITH_WARNINGS">With Warnings</option>
            <option value="PROCESSING">Processing</option>
            <option value="QUEUED">Queued</option>
            <option value="FAILED">Failed</option>
          </select>

          {/* Refresh Button */}
          <Button
            variant="secondary"
            size="sm"
            onClick={onRefresh}
            isLoading={loading}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Table Content */}
      <div className="flex-1">
        {loading && (
          <div className="p-6">
            <LoadingState type="table" />
          </div>
        )}

        {error && !loading && (
          <div className="p-6">
            <ErrorState
              title="Unable to Retrieve Import History"
              message={error}
              onRetry={onRefresh}
            />
          </div>
        )}

        {!loading && !error && jobs.length === 0 && (
          <div className="py-16 px-6 text-center flex flex-col items-center justify-center">
            <div className="w-12 h-12 rounded-full bg-[var(--teal-50)] text-[var(--teal-600)] border border-[var(--teal-100)] flex items-center justify-center mb-3 shadow-xs">
              <Database className="w-6 h-6" />
            </div>
            <h4 className="font-display font-bold text-base text-[var(--text-primary)] mb-1">
              No HMIS Import Jobs Found
            </h4>
            <p className="text-xs sm:text-sm text-[var(--text-secondary)] max-w-md mx-auto mb-4">
              {searchQuery || selectedStatus !== 'ALL'
                ? 'No import jobs match your current search or status filters. Try resetting the filters.'
                : 'No spreadsheet files have been submitted for ingestion yet. Upload your first HMIS dataset above.'}
            </p>
            {(searchQuery || selectedStatus !== 'ALL') && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  onSearchChange('');
                  onStatusChange('ALL');
                }}
              >
                Clear Filters
              </Button>
            )}
          </div>
        )}

        {!loading && !error && jobs.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-[var(--bg-surface-subtle)] border-b border-[var(--border-subtle)] text-[var(--text-muted)] font-bold uppercase tracking-wider text-[11px]">
                  <th className="py-3.5 px-4">Job Code</th>
                  <th className="py-3.5 px-4">File Name</th>
                  <th className="py-3.5 px-4">Upload Timestamp</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Records Imported</th>
                  <th className="py-3.5 px-4 text-center">Quality Score</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border-subtle)]">
                {jobs.map((job) => (
                  <tr
                    key={job.id}
                    className="hover:bg-[var(--bg-surface-subtle)]/60 transition-colors"
                  >
                    <td className="py-3.5 px-4 font-mono font-medium text-[var(--text-primary)] whitespace-nowrap">
                      {job.job_code}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <FileSpreadsheet className="w-4 h-4 text-[var(--teal-600)] shrink-0" />
                        <span className="font-semibold text-[var(--text-primary)] max-w-[220px] truncate" title={job.original_filename}>
                          {job.original_filename}
                        </span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-[var(--text-secondary)] whitespace-nowrap">
                      {formatTimestamp(job.created_at)}
                    </td>
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      {getStatusBadge(job.status)}
                    </td>
                    <td className="py-3.5 px-4 text-right font-mono text-[var(--text-secondary)] whitespace-nowrap">
                      <span className="font-semibold text-[var(--text-primary)]">
                        {job.records_imported.toLocaleString()}
                      </span>
                      <span className="text-[var(--text-muted)]"> / {job.total_records.toLocaleString()}</span>
                    </td>
                    <td className="py-3.5 px-4 text-center whitespace-nowrap">
                      {job.quality_score !== null && job.quality_score !== undefined ? (
                        <span
                          className={clsx(
                            'font-mono font-bold px-2 py-0.5 rounded text-xs',
                            job.quality_score >= 90
                              ? 'bg-[var(--emerald-50)] text-[var(--emerald-700)] border border-[var(--emerald-200)]'
                              : job.quality_score >= 75
                              ? 'bg-[var(--amber-50)] text-[var(--amber-700)] border border-[var(--amber-200)]'
                              : 'bg-[var(--coral-50)] text-[var(--coral-700)] border border-[var(--coral-200)]'
                          )}
                        >
                          {job.quality_score.toFixed(1)}%
                        </span>
                      ) : (
                        <span className="text-[var(--text-muted)] italic font-mono">—</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right whitespace-nowrap">
                      <div className="inline-flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onInspectQuality(job)}
                          title="Inspect Data Quality Audit"
                          leftIcon={<ShieldCheck className="w-3.5 h-3.5 text-[var(--teal-600)]" />}
                        >
                          Quality
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onViewErrors(job)}
                          title="View Diagnostic Logs"
                          leftIcon={<FileText className="w-3.5 h-3.5 text-[var(--amber-600)]" />}
                        >
                          Logs
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination Footer */}
      {!loading && !error && jobs.length > 0 && (
        <div className="px-6 py-4 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <span className="text-[var(--text-muted)]">
            Showing {(currentPage - 1) * pageSize + 1}–{Math.min(currentPage * pageSize, total)} of {total} import jobs
          </span>

          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onPageChange(Math.max(1, currentPage - 1))}
              disabled={currentPage <= 1}
              leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
            >
              Previous
            </Button>
            <span className="px-2 font-mono text-[var(--text-secondary)] font-medium">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage >= totalPages}
              rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
