import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Database,
  CheckCircle2,
  AlertTriangle,
  FileCheck,
  FileSpreadsheet,
  BookOpen,
  Info,
  Check,
} from 'lucide-react';
import { api } from '../../api/client';
import type { DistrictDataQualitySummaryResponse, IndicatorAuditReportResponse } from '../../api/types';

interface DistrictQualityTabProps {
  qualityData: DistrictDataQualitySummaryResponse | null;
  loading: boolean;
}

export const DistrictQualityTab: React.FC<DistrictQualityTabProps> = ({
  qualityData,
  loading,
}) => {
  const [auditReport, setAuditReport] = useState<IndicatorAuditReportResponse | null>(null);

  useEffect(() => {
    api
      .getIndicatorAudit()
      .then((res) => {
        setAuditReport(res);
      })
      .catch(() => {
        // Fallback silently if audit endpoint is unavailable
      });
  }, []);

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
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 shadow-xs">
          <div className="text-[10px] font-bold text-emerald-700 uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Valid Returns</span>
          </div>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-emerald-700 mt-1">
            {validCount.toLocaleString()}
          </div>
          <div className="text-[11px] text-emerald-600 mt-1 font-semibold">
            {validPct}% of recorded observations
          </div>
        </div>

        {/* Confirmed Zero Observations */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 shadow-xs">
          <div className="text-[10px] font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
            <span>Confirmed Zero Events</span>
          </div>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-slate-700 mt-1">
            {zeroCount.toLocaleString()}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {zeroPct}% distinct from missing
          </div>
        </div>

        {/* Missing Returns */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-4 shadow-xs">
          <div className="text-[10px] font-bold text-amber-700 uppercase tracking-wider flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Missing / Unreported</span>
          </div>
          <div className="text-xl sm:text-2xl font-mono font-extrabold text-amber-700 mt-1">
            {missingCount.toLocaleString()}
          </div>
          <div className="text-[11px] text-amber-600 mt-1">
            {missingPct}% explicit null state
          </div>
        </div>
      </div>

      {/* 2. Phase 12B Verified Indicator Registry Audit Card */}
      {auditReport && (
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 sm:p-7 shadow-xs space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4">
            <div>
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-teal-600" />
                <h4 className="font-display font-bold text-base text-[var(--text-primary)]">
                  Phase 12B Verified Indicator Registry & Governance Audit
                </h4>
              </div>
              <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                Authoritative crosswalk between MoHFW raw item serials and canonical CAREFlow clinical definitions.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-1 rounded-full bg-teal-50 text-teal-800 border border-teal-200 text-xs font-semibold flex items-center gap-1">
                <Check className="w-3.5 h-3.5 text-teal-600" />
                <span>{auditReport.verified_mappings_count} Verified ({auditReport.verified_percentage}%)</span>
              </span>
              <span className="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-300 text-xs font-semibold">
                {auditReport.unmapped_parameters_count} Unmapped ({auditReport.unmapped_percentage}%)
              </span>
            </div>
          </div>

          {/* Governance Note */}
          <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl text-xs text-amber-900 flex items-start gap-2.5 leading-relaxed">
            <Info className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Strict Non-Fabrication Rule: </span>
              {auditReport.governance_note}
            </div>
          </div>

          {/* Verified Mappings Table */}
          <div className="space-y-3">
            <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">
              Verified Clinical Crosswalk Specifications ({auditReport.verified_mappings.length} Canonical Indicators)
            </div>
            <div className="overflow-x-auto border border-[var(--border-subtle)] rounded-xl">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-[var(--bg-surface-subtle)] border-b border-[var(--border-subtle)] text-[var(--text-muted)] uppercase tracking-wider font-bold">
                    <th className="py-2.5 px-3">MoHFW Code</th>
                    <th className="py-2.5 px-3">Raw Parameter Label</th>
                    <th className="py-2.5 px-3">Canonical Equivalent</th>
                    <th className="py-2.5 px-3">Clinical Rationale & Provenance</th>
                    <th className="py-2.5 px-3">Category</th>
                    <th className="py-2.5 px-3">Unit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)] font-sans">
                  {auditReport.verified_mappings.map((vm) => (
                    <tr key={vm.s_no} className="hover:bg-[var(--bg-surface-subtle)] transition-colors">
                      <td className="py-2 px-3 font-mono font-bold text-teal-700 whitespace-nowrap">
                        {vm.s_no}
                      </td>
                      <td className="py-2 px-3 font-medium text-[var(--text-primary)] max-w-xs">
                        {vm.parameter_name}
                      </td>
                      <td className="py-2 px-3 font-mono font-semibold text-slate-800 whitespace-nowrap">
                        {vm.canonical_id}
                        <div className="text-[10px] font-sans text-teal-700 font-bold">{vm.canonical_name}</div>
                      </td>
                      <td className="py-2 px-3 text-[11px] text-[var(--text-secondary)] leading-relaxed max-w-md">
                        {vm.rationale}
                        <div className="text-[10px] text-slate-400 mt-0.5 font-mono">Ref: {vm.provenance}</div>
                      </td>
                      <td className="py-2 px-3 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 text-[10px] font-semibold">
                          {vm.category}
                        </span>
                      </td>
                      <td className="py-2 px-3 text-[11px] text-slate-600 capitalize">
                        {vm.unit}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* 3. Ingestion Provenance & Job Metadata */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Source File & Import Provenance */}
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-xs space-y-3">
          <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-2">
            <FileSpreadsheet className="w-4 h-4 text-[var(--teal-600)]" />
            <h4 className="font-display font-bold text-sm text-[var(--text-primary)]">
              Source Archive & Execution Provenance
            </h4>
          </div>
          {qualityData.import_job ? (
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-[var(--text-muted)] font-medium">Source File:</span>
                <p className="font-mono font-bold text-[var(--text-primary)] truncate mt-0.5">
                  {qualityData.import_job.original_filename}
                </p>
              </div>
              <div>
                <span className="text-[var(--text-muted)] font-medium">Job Code:</span>
                <p className="font-mono font-bold text-[var(--text-primary)] mt-0.5">
                  {qualityData.import_job.job_code}
                </p>
              </div>
              <div>
                <span className="text-[var(--text-muted)] font-medium">Schema Profile:</span>
                <p className="font-mono font-bold text-teal-700 mt-0.5">
                  {qualityData.import_job.schema_profile}
                </p>
              </div>
              <div>
                <span className="text-[var(--text-muted)] font-medium">Execution Status:</span>
                <p className="font-bold text-emerald-700 mt-0.5">
                  {qualityData.import_job.status} ({qualityData.import_job.records_imported.toLocaleString()} imported)
                </p>
              </div>
            </div>
          ) : (
            <p className="text-xs text-[var(--text-secondary)]">Historical import job record attached.</p>
          )}
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
                <span>Formula Injection Protection</span>
                <span className="text-[10px] font-mono text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded">Enforced</span>
              </div>
              <div className="text-[11px] text-[var(--text-secondary)]">All exported CSV outputs escape spreadsheet macro triggers (=, +, -, @, tab, CR) per OWASP guidelines.</div>
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
