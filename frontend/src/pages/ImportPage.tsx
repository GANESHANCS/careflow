import React, { useState, useEffect, useCallback } from 'react';
import { PageTransition } from '../components/motion/PageTransition';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import { FileUploadZone } from '../components/imports/FileUploadZone';
import { ImportHistoryTable } from '../components/imports/ImportHistoryTable';
import { ImportQualityModal } from '../components/imports/ImportQualityModal';
import { ImportErrorLogViewer } from '../components/imports/ImportErrorLogViewer';
import { ImportRollbackModal } from '../components/imports/ImportRollbackModal';
import { BatchMonitoringPanel } from '../components/imports/BatchMonitoringPanel';
import type { ImportJob, ImportRollbackResponse } from '../api/types';

import {
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Activity,
  Layers,
  Loader2,
  Clock,
} from 'lucide-react';

export const ImportPage: React.FC = () => {
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<'individual' | 'batches'>('individual');
  const [jobs, setJobs] = useState<ImportJob[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Selected jobs for modal inspection
  const [qualityJobCode, setQualityJobCode] = useState<string | null>(null);
  const [errorJobCode, setErrorJobCode] = useState<string | null>(null);
  const [rollbackJob, setRollbackJob] = useState<ImportJob | null>(null);

  const fetchImports = useCallback((showLoadingSpinner = true) => {
    if (showLoadingSpinner) setLoading(true);
    setError(null);

    const skip = (currentPage - 1) * pageSize;
    const statusParam = selectedStatus !== 'ALL' ? selectedStatus : undefined;
    const searchParam = searchQuery.trim() ? searchQuery.trim() : undefined;

    api.getImports({
      skip,
      limit: pageSize,
      status: statusParam,
      search: searchParam,
    })
      .then((res) => {
        setJobs(res.items);
        setTotal(res.total);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to retrieve import jobs from server.');
        setLoading(false);
      });
  }, [currentPage, pageSize, selectedStatus, searchQuery]);

  useEffect(() => {
    fetchImports(true);
  }, [fetchImports]);

  // Phase 9A Active Ingestion Auto-Polling
  const hasActiveJobs = jobs.some((j) => j.status === 'QUEUED' || j.status === 'PROCESSING');
  useEffect(() => {
    if (!hasActiveJobs) return;
    const interval = setInterval(() => {
      fetchImports(false);
    }, 2000);
    return () => clearInterval(interval);
  }, [hasActiveJobs, fetchImports]);

  const activeJob = jobs.find((j) => j.status === 'PROCESSING') || jobs.find((j) => j.status === 'QUEUED');

  const handleRetry = async (job: ImportJob) => {
    try {
      await api.retryImport(job.job_code);
      fetchImports(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Retry failed';
      setError(msg);
    }
  };

  const handleUploadSuccess = (_newJob: ImportJob) => {
    // Refresh history from page 1 to include latest upload
    if (currentPage === 1) {
      fetchImports(false);
    } else {
      setCurrentPage(1);
    }
  };

  const handleRollbackSuccess = (_result: ImportRollbackResponse) => {
    fetchImports(true);
  };

  // Quick stats computed across current view
  const completedCount = jobs.filter((j) => j.status === 'COMPLETED').length;
  const warningsCount = jobs.filter((j) => j.status === 'COMPLETED_WITH_WARNINGS').length;
  const failedCount = jobs.filter((j) => j.status === 'FAILED').length;

  return (
    <PageTransition className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Operational Workspace Header */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--teal-50)] text-[var(--teal-700)] border border-[var(--teal-200)]">
              <Activity className="w-3.5 h-3.5" />
              <span>MoHFW HMIS Operational Gateway</span>
              <span className="text-[var(--text-muted)]">•</span>
              <span className="font-mono uppercase">{user?.role || 'VIEWER'} Session</span>
            </div>
            <h1 className="font-display font-extrabold text-2xl sm:text-3xl text-[var(--text-primary)] tracking-tight">
              HMIS Ingestion & Quality Audit Workspace
            </h1>
            <p className="text-xs sm:text-sm text-[var(--text-secondary)] max-w-3xl leading-relaxed">
              Automated ingestion engine for Ministry of Health & Family Welfare monthly healthcare facility reports.
              Executes SHA-256 idempotency verification, preserves zero versus missing data integrity, and generates 13-point data quality audit telemetry.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="p-3 rounded-2xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[var(--teal-600)] text-white flex items-center justify-center font-bold text-sm shadow-xs">
                <Layers className="w-4 h-4" />
              </div>
              <div className="text-left">
                <span className="text-[10px] uppercase font-bold tracking-wider text-[var(--text-muted)] block">
                  Total Jobs Logged
                </span>
                <span className="text-base font-display font-extrabold text-[var(--text-primary)]">
                  {total.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 2. File Upload Zone */}
      <FileUploadZone onUploadSuccess={handleUploadSuccess} />

      {/* 2b. Phase 9A Active Ingestion Progress Banner */}
      {activeJob && (
        <div className="bg-[var(--bg-surface)] border-2 border-[var(--teal-500)] rounded-2xl p-6 shadow-md transition-all">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-[var(--teal-50)] text-[var(--teal-600)] flex items-center justify-center font-bold">
                {activeJob.status === 'PROCESSING' ? (
                  <Loader2 className="w-5 h-5 animate-spin text-[var(--teal-600)]" />
                ) : (
                  <Clock className="w-5 h-5 text-slate-500" />
                )}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
                    {activeJob.status === 'PROCESSING' ? 'Batch Ingestion in Progress' : 'Import Job Queued for Worker'}
                  </h3>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-[var(--teal-50)] text-[var(--teal-700)] border border-[var(--teal-200)] font-semibold">
                    {activeJob.job_code}
                  </span>
                </div>
                <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                  File: <span className="font-semibold text-[var(--text-primary)]">{activeJob.original_filename}</span>
                  {activeJob.schema_profile && (
                    <> • Schema Profile: <code className="font-mono text-[11px] text-[var(--teal-700)]">{activeJob.schema_profile}</code></>
                  )}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs font-mono">
              <div>
                <span className="text-[var(--text-muted)] block text-[10px] uppercase">Processed</span>
                <span className="font-bold text-[var(--text-primary)] text-sm">
                  {(activeJob.processed_records ?? activeJob.records_imported).toLocaleString()} / {activeJob.total_records.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block text-[10px] uppercase">Accepted</span>
                <span className="font-bold text-[var(--emerald-600)] text-sm">
                  {activeJob.records_imported.toLocaleString()}
                </span>
              </div>
              <div>
                <span className="text-[var(--text-muted)] block text-[10px] uppercase">Rejected</span>
                <span className="font-bold text-[var(--coral-600)] text-sm">
                  {activeJob.records_rejected.toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
            <div
              className="bg-gradient-to-r from-[var(--teal-500)] to-[var(--emerald-500)] h-2.5 rounded-full transition-all duration-300"
              style={{
                width: `${Math.min(100, Math.max(5, activeJob.progress_percent ?? (activeJob.total_records > 0 ? Math.round(((activeJob.processed_records || 0) / activeJob.total_records) * 100) : 5)))}%`
              }}
            />
          </div>
          <div className="mt-2 flex items-center justify-between text-[11px] text-[var(--text-muted)]">
            <span>
              {activeJob.status === 'PROCESSING' ? 'Processing chunked records asynchronously...' : 'Waiting for available worker to claim...'}
            </span>
            <span className="font-mono font-medium">
              {activeJob.progress_percent ?? (activeJob.total_records > 0 ? Math.round(((activeJob.processed_records || 0) / activeJob.total_records) * 100) : 0)}%
            </span>
          </div>
        </div>
      )}

      {/* 3. Ingestion Summary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-2 font-medium">
            <span>Total Ingestions</span>
            <FileSpreadsheet className="w-4 h-4 text-[var(--teal-600)]" />
          </div>
          <div className="text-2xl font-display font-bold text-[var(--text-primary)]">
            {total}
          </div>
          <span className="text-[11px] text-[var(--text-secondary)] mt-1 block">
            Across all reporting periods
          </span>
        </div>

        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-2 font-medium">
            <span>Clean Ingestions</span>
            <CheckCircle2 className="w-4 h-4 text-[var(--emerald-600)]" />
          </div>
          <div className="text-2xl font-display font-bold text-[var(--emerald-700)]">
            {completedCount}
          </div>
          <span className="text-[11px] text-[var(--text-secondary)] mt-1 block">
            Zero blocking validation issues
          </span>
        </div>

        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-2 font-medium">
            <span>With Warnings</span>
            <AlertTriangle className="w-4 h-4 text-[var(--amber-600)]" />
          </div>
          <div className="text-2xl font-display font-bold text-[var(--amber-700)]">
            {warningsCount}
          </div>
          <span className="text-[11px] text-[var(--text-secondary)] mt-1 block">
            Non-fatal quality anomalies
          </span>
        </div>

        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 sm:p-5 shadow-xs">
          <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-2 font-medium">
            <span>Failed Ingestions</span>
            <AlertOctagon className="w-4 h-4 text-[var(--coral-600)]" />
          </div>
          <div className="text-2xl font-display font-bold text-[var(--coral-700)]">
            {failedCount}
          </div>
          <span className="text-[11px] text-[var(--text-secondary)] mt-1 block">
            Rejected structure or format
          </span>
        </div>
      </div>

      {/* 4. Tab Navigation between Individual Jobs and Automated Batches */}
      <div className="flex items-center gap-3 border-b border-[var(--border-subtle)] pb-3">
        <button
          onClick={() => setActiveTab('individual')}
          data-testid="tab-individual-jobs"
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
            activeTab === 'individual'
              ? 'bg-[var(--teal-600)] text-white shadow-xs'
              : 'bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)] hover:bg-[var(--border-subtle)]'
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>Individual Ingestion Jobs ({total})</span>
        </button>

        <button
          onClick={() => setActiveTab('batches')}
          data-testid="tab-automated-batches"
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-colors cursor-pointer ${
            activeTab === 'batches'
              ? 'bg-[var(--teal-600)] text-white shadow-xs'
              : 'bg-[var(--bg-surface-subtle)] text-[var(--text-secondary)] hover:bg-[var(--border-subtle)]'
          }`}
        >
          <Layers className="w-4 h-4" />
          <span>Automated Batch Orchestration (Incoming Dir)</span>
        </button>
      </div>

      {activeTab === 'individual' ? (
        <ImportHistoryTable
          jobs={jobs}
          total={total}
          loading={loading}
          error={error}
          currentPage={currentPage}
          pageSize={pageSize}
          selectedStatus={selectedStatus}
          searchQuery={searchQuery}
          onPageChange={setCurrentPage}
          onStatusChange={(status) => {
            setSelectedStatus(status);
            setCurrentPage(1);
          }}
          onSearchChange={(query) => {
            setSearchQuery(query);
            setCurrentPage(1);
          }}
          onRefresh={fetchImports}
          onInspectQuality={(job) => setQualityJobCode(job.job_code)}
          onViewErrors={(job) => setErrorJobCode(job.job_code)}
          onRollback={(job) => setRollbackJob(job)}
          onRetry={handleRetry}
        />
      ) : (
        <BatchMonitoringPanel onRefreshParent={() => fetchImports(false)} />
      )}

      {/* 5. Modals for Quality, Errors, and Rollback */}
      <ImportQualityModal
        jobCode={qualityJobCode}
        isOpen={!!qualityJobCode}
        onClose={() => setQualityJobCode(null)}
      />

      <ImportErrorLogViewer
        jobCode={errorJobCode}
        isOpen={!!errorJobCode}
        onClose={() => setErrorJobCode(null)}
      />

      <ImportRollbackModal
        job={rollbackJob}
        isOpen={!!rollbackJob}
        onClose={() => setRollbackJob(null)}
        onSuccess={handleRollbackSuccess}
      />
    </PageTransition>
  );
};
