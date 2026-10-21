import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../api/client';
import { useAuth } from '../../auth/AuthContext';
import type { ImportBatch, ImportBatchDetail } from '../../api/types';
import {
  FolderSync,
  RefreshCw,
  Play,
  RotateCcw,
  XCircle,
  AlertTriangle,
  CheckCircle2,
  AlertOctagon,
  Clock,
  Loader2,
  ChevronDown,
  ChevronRight,
  FileSpreadsheet,
  Layers,
} from 'lucide-react';

interface BatchMonitoringPanelProps {
  onRefreshParent?: () => void;
}

export const BatchMonitoringPanel: React.FC<BatchMonitoringPanelProps> = ({ onRefreshParent }) => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';

  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [expandedBatchCode, setExpandedBatchCode] = useState<string | null>(null);
  const [expandedDetail, setExpandedDetail] = useState<ImportBatchDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const fetchBatches = useCallback((showSpinner = true) => {
    if (showSpinner) setLoading(true);
    setError(null);

    const statusParam = selectedStatus !== 'ALL' ? selectedStatus : undefined;

    api.getImportBatches({
      skip: 0,
      limit: 50,
      status: statusParam,
    })
      .then((res) => {
        setBatches(res.items);
        setTotal(res.total);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load import batches.');
        setLoading(false);
      });
  }, [selectedStatus]);

  useEffect(() => {
    fetchBatches(true);
  }, [fetchBatches]);

  // Auto-poll active batches
  const hasActiveBatches = batches.some((b) => b.status === 'QUEUED' || b.status === 'PROCESSING');
  useEffect(() => {
    if (!hasActiveBatches) return;
    const interval = setInterval(() => {
      fetchBatches(false);
      if (expandedBatchCode) {
        api.getImportBatchDetail(expandedBatchCode).then(setExpandedDetail).catch(() => {});
      }
    }, 2500);
    return () => clearInterval(interval);
  }, [hasActiveBatches, fetchBatches, expandedBatchCode]);

  const handleScanDirectory = async () => {
    if (!isAdmin || scanning) return;
    setScanning(true);
    setScanMessage(null);
    setError(null);

    try {
      const res = await api.triggerDirectoryScan();
      setScanMessage(res.message);
      fetchBatches(false);
      if (onRefreshParent) onRefreshParent();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Directory scan trigger failed.';
      setError(msg);
    } finally {
      setScanning(false);
    }
  };

  const handleToggleExpand = async (batchCode: string) => {
    if (expandedBatchCode === batchCode) {
      setExpandedBatchCode(null);
      setExpandedDetail(null);
      return;
    }

    setExpandedBatchCode(batchCode);
    setLoadingDetail(true);
    try {
      const detail = await api.getImportBatchDetail(batchCode);
      setExpandedDetail(detail);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load batch detail.';
      setError(msg);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleRetryBatch = async (batchCode: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isAdmin) return;
    setActionInProgress(batchCode);
    try {
      await api.retryImportBatch(batchCode);
      fetchBatches(false);
      if (onRefreshParent) onRefreshParent();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Retry failed.');
    } finally {
      setActionInProgress(null);
    }
  };

  const handleCancelBatch = async (batchCode: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!isAdmin) return;
    if (!window.confirm(`Are you sure you want to cancel batch ${batchCode}?`)) return;
    setActionInProgress(batchCode);
    try {
      await api.cancelImportBatch(batchCode, 'Cancelled by operator');
      fetchBatches(false);
      if (onRefreshParent) onRefreshParent();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Cancel failed.');
    } finally {
      setActionInProgress(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Completed
          </span>
        );
      case 'PARTIALLY_FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            Partially Failed
          </span>
        );
      case 'PROCESSING':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-teal-50 text-teal-700 border border-teal-200">
            <Loader2 className="w-3.5 h-3.5 text-teal-600 animate-spin" />
            Processing
          </span>
        );
      case 'QUEUED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-50 text-slate-700 border border-slate-200">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            Queued
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <AlertOctagon className="w-3.5 h-3.5 text-rose-600" />
            Failed
          </span>
        );
      case 'CANCELLED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-gray-50 text-gray-700 border border-gray-200">
            <XCircle className="w-3.5 h-3.5 text-gray-500" />
            Cancelled
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-800">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <FolderSync className="w-5 h-5 text-[var(--teal-600)]" />
            <h2 className="font-display font-bold text-lg text-[var(--text-primary)]">
              Automated Batch Ingestion & Incoming Directory
            </h2>
          </div>
          <p className="text-xs text-[var(--text-secondary)] mt-1">
            Monitors incoming files, aggregates batch lifecycle metrics, and supports partial-failure recovery ({total} batches recorded).
          </p>
        </div>

        <div className="flex items-center gap-3">
          {isAdmin && (
            <button
              onClick={handleScanDirectory}
              disabled={scanning}
              data-testid="scan-incoming-directory-btn"
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold bg-[var(--teal-600)] text-white hover:bg-[var(--teal-700)] transition-colors disabled:opacity-50 shadow-xs cursor-pointer"
            >
              {scanning ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Play className="w-3.5 h-3.5" />
              )}
              <span>{scanning ? 'Scanning...' : 'Scan Incoming Dir'}</span>
            </button>
          )}

          <button
            onClick={() => fetchBatches(true)}
            disabled={loading}
            className="p-2 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] hover:bg-[var(--border-subtle)] text-[var(--text-secondary)] transition-colors cursor-pointer"
            title="Refresh batches"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Notifications */}
      {scanMessage && (
        <div className="p-3.5 rounded-2xl bg-teal-50 border border-teal-200 text-teal-800 text-xs flex items-center justify-between">
          <span>{scanMessage}</span>
          <button onClick={() => setScanMessage(null)} className="text-teal-600 hover:text-teal-800 font-bold ml-2">×</button>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-800 font-bold ml-2">×</button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-[var(--border-subtle)] pb-3">
        {['ALL', 'PROCESSING', 'QUEUED', 'COMPLETED', 'PARTIALLY_FAILED', 'FAILED', 'CANCELLED'].map((st) => (
          <button
            key={st}
            onClick={() => setSelectedStatus(st)}
            className={`px-3 py-1 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
              selectedStatus === st
                ? 'bg-[var(--teal-600)] text-white'
                : 'bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)] hover:bg-[var(--border-subtle)]'
            }`}
          >
            {st.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Batches List */}
      {loading ? (
        <div className="py-12 flex flex-col items-center justify-center text-[var(--text-muted)] space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-[var(--teal-600)]" />
          <p className="text-xs font-medium">Loading batch telemetry...</p>
        </div>
      ) : batches.length === 0 ? (
        <div className="py-12 text-center rounded-2xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] p-6 space-y-3">
          <Layers className="w-8 h-8 mx-auto text-[var(--text-muted)]" />
          <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
            No Ingestion Batches Found
          </h4>
          <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto">
            Place HMIS spreadsheets in the incoming directory or trigger an on-demand scan.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {batches.map((batch) => {
            const isExpanded = expandedBatchCode === batch.batch_code;
            const progress = batch.progress_percent ?? (batch.total_files > 0 ? Math.round((batch.processed_files / batch.total_files) * 100) : 0);
            const canRetry = isAdmin && (batch.status === 'FAILED' || batch.status === 'PARTIALLY_FAILED');
            const canCancel = isAdmin && (batch.status === 'QUEUED' || batch.status === 'PROCESSING');

            return (
              <div
                key={batch.batch_code}
                className="border border-[var(--border-subtle)] rounded-2xl bg-[var(--bg-surface-subtle)] p-4 transition-all hover:border-[var(--teal-300)]"
              >
                <div
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer"
                  onClick={() => handleToggleExpand(batch.batch_code)}
                >
                  <div className="flex items-center gap-3">
                    <button className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
                      {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-xs text-[var(--text-primary)]">
                          {batch.batch_code}
                        </span>
                        {getStatusBadge(batch.status)}
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                          {batch.source}
                        </span>
                      </div>
                      <div className="text-[11px] text-[var(--text-muted)] mt-1 flex items-center gap-3">
                        <span>Created: {new Date(batch.created_at).toLocaleString()}</span>
                        <span>•</span>
                        <span>Files: {batch.processed_files} / {batch.total_files}</span>
                        <span>•</span>
                        <span>Records: {batch.imported_records.toLocaleString()} imported</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {/* Progress Bar Widget */}
                    <div className="w-32 hidden md:block">
                      <div className="flex items-center justify-between text-[10px] font-mono mb-1 text-[var(--text-muted)]">
                        <span>Progress</span>
                        <span>{progress}%</span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-[var(--teal-600)] h-1.5 rounded-full transition-all"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="flex items-center gap-2">
                      {canRetry && (
                        <button
                          onClick={(e) => handleRetryBatch(batch.batch_code, e)}
                          disabled={actionInProgress === batch.batch_code}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100 transition-colors"
                          title="Retry failed jobs in batch"
                        >
                          <RotateCcw className="w-3 h-3" />
                          <span>Retry</span>
                        </button>
                      )}

                      {canCancel && (
                        <button
                          onClick={(e) => handleCancelBatch(batch.batch_code, e)}
                          disabled={actionInProgress === batch.batch_code}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors"
                          title="Cancel in-flight batch"
                        >
                          <XCircle className="w-3 h-3" />
                          <span>Cancel</span>
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Error Summary Note */}
                {batch.error_summary && (
                  <div className="mt-3 p-2.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-[11px] flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                    <span>{batch.error_summary}</span>
                  </div>
                )}

                {/* Expanded Child Jobs */}
                {isExpanded && (
                  <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] space-y-2">
                    <h5 className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1.5">
                      <FileSpreadsheet className="w-3.5 h-3.5" />
                      Constituent Import Jobs ({batch.total_files})
                    </h5>

                    {loadingDetail ? (
                      <div className="py-4 text-center text-xs text-[var(--text-muted)] flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin text-[var(--teal-600)]" />
                        <span>Loading job details...</span>
                      </div>
                    ) : expandedDetail?.import_jobs && expandedDetail.import_jobs.length > 0 ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                          <thead>
                            <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] font-mono text-[10px]">
                              <th className="py-1.5 px-2">Job Code</th>
                              <th className="py-1.5 px-2">Filename</th>
                              <th className="py-1.5 px-2">Status</th>
                              <th className="py-1.5 px-2">Imported</th>
                              <th className="py-1.5 px-2">Rejected</th>
                              <th className="py-1.5 px-2">Quality</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[var(--border-subtle)]">
                            {expandedDetail.import_jobs.map((job) => (
                              <tr key={job.job_code} className="hover:bg-[var(--bg-surface)] font-mono text-[11px]">
                                <td className="py-1.5 px-2 font-bold text-[var(--teal-700)]">{job.job_code}</td>
                                <td className="py-1.5 px-2 font-sans text-[var(--text-primary)]">{job.original_filename}</td>
                                <td className="py-1.5 px-2">{getStatusBadge(job.status)}</td>
                                <td className="py-1.5 px-2 text-emerald-700 font-bold">{job.records_imported.toLocaleString()}</td>
                                <td className="py-1.5 px-2 text-rose-700">{job.records_rejected.toLocaleString()}</td>
                                <td className="py-1.5 px-2 font-bold">
                                  {job.quality_score !== null ? `${job.quality_score}%` : '—'}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="text-xs text-[var(--text-muted)] italic py-2">No child jobs found in batch.</p>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
