import React, { useState, useEffect, useCallback } from 'react';
import { PageTransition } from '../components/motion/PageTransition';
import { useAuth } from '../auth/AuthContext';
import { api } from '../api/client';
import type { ImportJob } from '../api/types';

import { FileUploadZone } from '../components/imports/FileUploadZone';
import { ImportHistoryTable } from '../components/imports/ImportHistoryTable';
import { ImportQualityModal } from '../components/imports/ImportQualityModal';
import { ImportErrorLogViewer } from '../components/imports/ImportErrorLogViewer';

import {
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Activity,
  Layers,
} from 'lucide-react';

export const ImportPage: React.FC = () => {
  const { user } = useAuth();

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

  const fetchImports = useCallback(() => {
    setLoading(true);
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
    fetchImports();
  }, [fetchImports]);

  const handleUploadSuccess = (_newJob: ImportJob) => {
    // Refresh history from page 1 to include latest upload
    if (currentPage === 1) {
      fetchImports();
    } else {
      setCurrentPage(1);
    }
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

      {/* 4. Import History & Audit Registry */}
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
      />

      {/* 5. Modals for Quality and Errors */}
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
    </PageTransition>
  );
};
