import React from 'react';
import { ShieldCheck, Database, CheckCircle2, AlertTriangle, Clock, FileCheck, Layers, FileSpreadsheet } from 'lucide-react';
import type { DistrictDataQualitySummaryResponse } from '../../api/types';

interface DistrictQualityTabProps {
  qualityData: DistrictDataQualitySummaryResponse | null;
  loading: boolean;
}

export const DistrictQualityTab: React.FC<DistrictQualityTabProps> = ({
  qualityData,
  loading,
}) => {
  if (loading) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs animate-pulse space-y-4">
        <div className="h-6 w-72 bg-[var(--bg-surface-active)] rounded" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="h-24 bg-[var(--bg-surface-active)] rounded-xl" />
          <div className="h-24 bg-[var(--bg-surface-active)] rounded-xl" />
          <div className="h-24 bg-[var(--bg-surface-active)] rounded-xl" />
          <div className="h-24 bg-[var(--bg-surface-active)] rounded-xl" />
        </div>
        <div className="h-64 bg-[var(--bg-surface-active)] rounded-xl" />
      </div>
    );
  }

  if (!qualityData) {
    return (
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-8 shadow-xs text-center space-y-3">
        <ShieldCheck className="w-12 h-12 text-slate-400 mx-auto" />
        <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
          District Quality Audit Data Unavailable
        </h3>
        <p className="text-xs text-[var(--text-secondary)] max-w-md mx-auto">
          Unable to retrieve the data quality audit log from the district analytics service.
        </p>
      </div>
    );
  }

  const validCount = qualityData.value_counts?.['VALID'] ?? 0;
  const zeroCount = qualityData.value_counts?.['ZERO'] ?? 0;
  const missingCount = qualityData.value_counts?.['MISSING'] ?? 0;
  const total = qualityData.total_records || 1;

  const validPct = ((validCount / total) * 100).toFixed(1);
  const zeroPct = ((zeroCount / total) * 100).toFixed(1);
  const missingPct = ((missingCount / total) * 100).toFixed(1);

  return (
    <div className="space-y-6">
      {/* 1. Observation Quality Breakdown KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Total Ingested */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 shadow-xs">
          <div className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-indigo-600" />
            <span>Total Ingested Records</span>
          </div>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-[var(--text-primary)] mt-1">
            {qualityData.total_records.toLocaleString()}
          </div>
          <div className="text-[11px] text-[var(--text-secondary)] mt-1">
            Across {qualityData.districts_count} Districts (12 Months)
          </div>
        </div>

        {/* Valid Observations */}
        <div className="bg-[var(--bg-surface)] border border-emerald-200/80 rounded-2xl p-4 shadow-xs bg-emerald-50/20">
          <div className="text-[10px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Valid Non-Zero Values</span>
          </div>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-700 mt-1">
            {validCount.toLocaleString()}
          </div>
          <div className="text-[11px] text-emerald-800/80 mt-1">
            {validPct}% of all observations
          </div>
        </div>

        {/* Explicit Zero Observations */}
        <div className="bg-[var(--bg-surface)] border border-slate-300 rounded-2xl p-4 shadow-xs bg-slate-50/60">
          <div className="text-[10px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
            <span>Explicit Zeroes (0)</span>
          </div>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-slate-800 mt-1">
            {zeroCount.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-600 mt-1">
            {zeroPct}% verified zero activity
          </div>
        </div>

        {/* Missing / Null Observations */}
        <div className="bg-[var(--bg-surface)] border border-amber-200 rounded-2xl p-4 shadow-xs bg-amber-50/30">
          <div className="text-[10px] font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Missing / Null Entries</span>
          </div>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-amber-700 mt-1">
            {missingCount.toLocaleString()}
          </div>
          <div className="text-[11px] text-amber-800 mt-1">
            {missingPct}% preserved as null (never 0)
          </div>
        </div>
      </div>

      {/* 2. Import Job Traceability & Provenance */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-7 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-4 h-4 text-[var(--teal-600)]" />
            <h3 className="font-display font-bold text-base text-[var(--text-primary)]">
              Import Pipeline Execution Traceability
            </h3>
          </div>
          <span className="text-[11px] font-mono text-[var(--text-muted)]">
            Adapter: {qualityData.import_job?.schema_profile || 'district_monthly_tabular_v1'}
          </span>
        </div>

        {!qualityData.import_job ? (
          <div className="text-center py-6 text-xs text-[var(--text-muted)]">
            No registered district import execution record found.
          </div>
        ) : (
          <div className="p-4 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl space-y-3 text-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-2">
              <div className="flex items-center gap-2 font-mono font-bold text-[var(--text-primary)]">
                <Clock className="w-3.5 h-3.5 text-teal-600" />
                <span>Job Code: {qualityData.import_job.job_code}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-emerald-100 text-emerald-800 border border-emerald-200">
                  {qualityData.import_job.status}
                </span>
                <span className="text-[11px] text-[var(--text-muted)] font-mono">
                  {qualityData.import_job.completed_at || 'Completed'}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[11px]">
              <div>
                <span className="text-[var(--text-muted)] font-medium">Source Filename:</span>
                <div className="font-mono font-bold text-[var(--text-primary)] truncate" title={qualityData.import_job.original_filename}>
                  {qualityData.import_job.original_filename}
                </div>
              </div>
              <div>
                <span className="text-[var(--text-muted)] font-medium">Schema Profile:</span>
                <div className="font-mono text-[var(--text-secondary)]">
                  {qualityData.import_job.schema_profile}
                </div>
              </div>
              <div>
                <span className="text-[var(--text-muted)] font-medium">Processed Rows / Imported:</span>
                <div className="font-mono font-bold text-[var(--text-primary)]">
                  {qualityData.import_job.records_imported.toLocaleString()} Wide Records ({qualityData.total_records.toLocaleString()} Observations)
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 3. Subgroup Aggregation Safeguards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Structural Subgroup Breakdown */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-2">
            <Layers className="w-4 h-4 text-indigo-600" />
            <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
              Subgroup Slice & Stock Metric Classification
            </h4>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between p-2 bg-[var(--bg-surface-subtle)] rounded-lg">
              <span className="text-[var(--text-secondary)]">Distinct HMIS Parameters:</span>
              <span className="font-mono font-bold text-[var(--text-primary)]">{qualityData.parameters_count}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-emerald-50/50 rounded-lg text-emerald-900 border border-emerald-100">
              <span className="font-medium">Subgroup Total Records (Non-Additive with Slices):</span>
              <span className="font-mono font-bold">{qualityData.subgroup_totals_count.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-slate-100/70 rounded-lg text-slate-800">
              <span className="font-medium">Subgroup Slice Records (e.g. Rural, Urban):</span>
              <span className="font-mono font-bold">{qualityData.subgroup_slices_count.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-amber-50/50 rounded-lg text-amber-900 border border-amber-100">
              <span className="font-medium">Non-Additive Stock/Capacity Observations:</span>
              <span className="font-mono font-bold">{qualityData.non_additive_stock_rows.toLocaleString()}</span>
            </div>
          </div>
          <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">
            The analytics service prevents double counting by filtering subgroup totals from slice records and prohibiting temporal sums of stock indicators.
          </p>
        </div>

        {/* Quality Audit Rules & Non-Destructive Ingestion */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-2">
            <FileCheck className="w-4 h-4 text-emerald-600" />
            <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
              Quality Rules & Ingestion Safeguards
            </h4>
          </div>
          <div className="space-y-2 text-xs">
            <div className="p-2 bg-[var(--bg-surface-subtle)] rounded-lg space-y-0.5">
              <div className="font-bold text-[var(--text-primary)] flex items-center justify-between">
                <span>Zero State Integrity</span>
                <span className="text-[10px] font-mono text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded">Enforced</span>
              </div>
              <div className="text-[11px] text-[var(--text-secondary)]">Zero values represent confirmed zero events, never conflated with missing or absent returns.</div>
            </div>
            <div className="p-2 bg-[var(--bg-surface-subtle)] rounded-lg space-y-0.5">
              <div className="font-bold text-[var(--text-primary)] flex items-center justify-between">
                <span>Facility Data Segregation</span>
                <span className="text-[10px] font-mono text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded">Enforced</span>
              </div>
              <div className="text-[11px] text-[var(--text-secondary)]">District records are isolated in district_observations table and never merged with facility logs.</div>
            </div>
            <div className="p-2 bg-[var(--bg-surface-subtle)] rounded-lg space-y-0.5">
              <div className="font-bold text-[var(--text-primary)] flex items-center justify-between">
                <span>Reversible Transformation</span>
                <span className="text-[10px] font-mono text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded">Enforced</span>
              </div>
              <div className="text-[11px] text-[var(--text-secondary)]">Source row indices and reported annual totals are preserved for complete audit traceability.</div>
            </div>
          </div>
        </div>
      </div>

      {/* 4. District Coverage Matrix */}
      {qualityData.district_coverage && qualityData.district_coverage.length > 0 && (
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-7 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
            <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
              District Data Completeness & Reporting Coverage ({qualityData.district_coverage.length} Districts)
            </h4>
            <span className="text-[11px] text-[var(--text-muted)] font-mono">
              Audit Timestamp: {qualityData.audit_timestamp}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 max-h-72 overflow-y-auto pr-2 no-scrollbar">
            {qualityData.district_coverage.map((cov) => (
              <div
                key={cov.district}
                className="p-3 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl space-y-1.5 text-xs"
              >
                <div className="font-bold text-[var(--text-primary)] truncate" title={cov.district}>
                  {cov.district}
                </div>
                <div className="flex items-center justify-between text-[11px] text-[var(--text-muted)]">
                  <span>Completeness:</span>
                  <span className="font-mono font-bold text-emerald-700">{cov.completeness_pct}%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    style={{ width: `${cov.completeness_pct}%` }}
                    className="h-full bg-emerald-600 rounded-full"
                  />
                </div>
                <div className="text-[10px] text-[var(--text-secondary)] flex justify-between pt-0.5">
                  <span>Valid: {cov.valid_records.toLocaleString()}</span>
                  <span>Missing: {cov.missing_records.toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
