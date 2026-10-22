import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Info,
  Sparkles,
  TrendingUp,
  RefreshCw,
  FileText,
  UserCheck,
  MessageSquare,
  History,
  X,
} from 'lucide-react';
import { api } from '../../api/client';
import type {
  VerifiedIndicatorOverviewResponse,
  ForecastingReadinessResponse,
  DistrictAnomalyReportResponse,
  AnomalySignalItem,
  SourceRegistrySummary,
  CrossYearComparabilityReport,
  DistrictAnomalyReviewItem,
} from '../../api/types';
import { LoadingState } from '../feedback/LoadingState';
import { ErrorState } from '../feedback/ErrorState';

interface DistrictIntelligenceTabProps {
  district: string;
  sNo: string;
  subgroupType?: string;
  financialYear?: string;
  availableDistricts?: string[];
  availableIndicators?: { s_no: string; parameter_name: string; is_mapped: boolean }[];
  onSelectDistrict?: (district: string) => void;
  onSelectSNo?: (sNo: string) => void;
}

export const DistrictIntelligenceTab: React.FC<DistrictIntelligenceTabProps> = ({
  district,
  sNo,
  subgroupType,
  financialYear = '2015-16',
}) => {
  const [horizon, setHorizon] = useState<number>(3);

  // Data states
  const [overview, setOverview] = useState<VerifiedIndicatorOverviewResponse | null>(null);
  const [readiness, setReadiness] = useState<ForecastingReadinessResponse | null>(null);
  const [anomalies, setAnomalies] = useState<DistrictAnomalyReportResponse | null>(null);
  const [sourceRegistry, setSourceRegistry] = useState<SourceRegistrySummary | null>(null);
  const [comparability, setComparability] = useState<CrossYearComparabilityReport | null>(null);

  // Anomaly Review Modal state
  const [selectedSignal, setSelectedSignal] = useState<AnomalySignalItem | null>(null);
  const [activeReviewDetail, setActiveReviewDetail] = useState<DistrictAnomalyReviewItem | null>(null);
  const [reviewNote, setReviewNote] = useState<string>('');
  const [reviewActionLoading, setReviewActionLoading] = useState<boolean>(false);
  const [reviewActionError, setReviewActionError] = useState<string | null>(null);

  // Loading & error states
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIntelligenceData = useCallback(() => {
    if (!district || !sNo) return;
    setLoading(true);
    setError(null);

    Promise.all([
      api.getDistrictIntelligenceOverview({
        district,
        s_no: sNo,
        subgroup_type: subgroupType || undefined,
        financial_year: financialYear,
      }),
      api.getDistrictForecastingReadiness({
        district,
        s_no: sNo,
        horizon,
        subgroup_type: subgroupType || undefined,
        financial_year: financialYear,
      }),
      api.getDistrictAnomalies({
        district,
        s_no: sNo,
        subgroup_type: subgroupType || undefined,
        financial_year: financialYear,
      }),
      api.getDistrictSourceRegistry().catch(() => null),
      api.getCrossYearComparability().catch(() => null),
    ])
      .then(([ov, rd, an, src, comp]) => {
        setOverview(ov);
        setReadiness(rd);
        setAnomalies(an);
        if (src) setSourceRegistry(src);
        if (comp) setComparability(comp);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to load district intelligence analytics.');
        setLoading(false);
      });
  }, [district, sNo, subgroupType, financialYear, horizon]);

  useEffect(() => {
    fetchIntelligenceData();
  }, [fetchIntelligenceData]);

  // Handle opening the review modal and fetching its audit trail
  const handleOpenReviewModal = async (sig: AnomalySignalItem) => {
    setSelectedSignal(sig);
    setReviewNote('');
    setReviewActionError(null);
    try {
      const reviews = await api.getDistrictAnomalyReviews({
        district: sig.district,
        status: undefined,
      });
      const matching = reviews.find((r) => r.signal_id === sig.signal_id) || null;
      setActiveReviewDetail(matching);
    } catch {
      setActiveReviewDetail(null);
    }
  };

  const handleExecuteReviewAction = async (action: string) => {
    if (!selectedSignal) return;
    setReviewActionLoading(true);
    setReviewActionError(null);

    try {
      const updated = await api.postDistrictAnomalyReviewAction(selectedSignal.signal_id, {
        action,
        notes: reviewNote.trim() || undefined,
        district: selectedSignal.district,
        indicator_id: selectedSignal.s_no,
        reporting_month: selectedSignal.reporting_month,
        signal_type: selectedSignal.signal_type,
        trigger_reason: selectedSignal.rationale,
        metric_value: selectedSignal.observed_value ?? undefined,
        expected_range: selectedSignal.expected_baseline !== null ? String(selectedSignal.expected_baseline) : undefined,
      });
      setActiveReviewDetail(updated);
      setReviewNote('');

      // Refresh anomaly list to update status badge in-place
      const updatedAnomalies = await api.getDistrictAnomalies({
        district,
        s_no: sNo,
        subgroup_type: subgroupType || undefined,
        financial_year: financialYear,
      });
      setAnomalies(updatedAnomalies);
      setReviewActionLoading(false);
    } catch (err: any) {
      setReviewActionError(err.message || 'Failed to apply review action.');
      setReviewActionLoading(false);
    }
  };

  if (loading) {
    return <LoadingState type="chart" />;
  }

  if (error || !overview) {
    return (
      <ErrorState
        title="Intelligence Data Unavailable"
        message={error || 'Unable to compute intelligence analytics for the selected indicator.'}
        onRetry={fetchIntelligenceData}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* 1. Header & Verification Status Badge */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                VERIFIED Indicator
              </span>
              <span className="text-xs text-stone-500 font-mono">S.No. {overview.s_no}</span>
            </div>
            <h2 className="text-xl font-bold text-[var(--text-primary)]">{overview.parameter_name}</h2>
            <p className="text-xs text-stone-600 font-mono">
              Canonical: <span className="font-semibold">{overview.canonical_name}</span> ({overview.canonical_id})
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchIntelligenceData}
              className="px-3 py-1.5 rounded-lg border border-stone-200 text-xs font-semibold text-stone-700 bg-white hover:bg-stone-50 flex items-center gap-1.5 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Provenance and Data Completeness Ribbon */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-[var(--border-subtle)] text-xs">
          <div>
            <p className="text-stone-500 font-medium">Reporting District</p>
            <p className="text-sm font-bold text-stone-900">{overview.district}</p>
          </div>
          <div>
            <p className="text-stone-500 font-medium">Reporting Subgroup</p>
            <p className="text-sm font-bold text-stone-900">{overview.subgroup_type}</p>
          </div>
          <div>
            <p className="text-stone-500 font-medium">Reporting Completeness</p>
            <p className="text-sm font-bold text-emerald-700">
              {(overview.completeness_ratio * 100).toFixed(1)}% ({overview.reported_months_count}/{overview.total_expected_months} Months)
            </p>
          </div>
          <div>
            <p className="text-stone-500 font-medium">Data Provenance</p>
            <p className="text-sm font-bold text-stone-900 truncate" title={overview.provenance}>
              {overview.provenance}
            </p>
          </div>
        </div>
      </div>

      {/* 2. Phase 15A & 15C: Source Discovery & Cross-Year Comparability Overview */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-sky-50 text-sky-800 border border-sky-200">
                <FileText className="w-3.5 h-3.5" />
                Multi-Year HMIS Archive
              </span>
              <span className="text-xs text-stone-500 font-semibold">Phase 15A & 15C</span>
            </div>
            <h3 className="text-base font-bold text-[var(--text-primary)]">
              Source Discovery, Ingestion Readiness & Comparability
            </h3>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-stone-100 text-stone-700">
              State: Tamil Nadu
            </span>
          </div>
        </div>

        {/* Source Registry Table */}
        {sourceRegistry && (
          <div className="border border-stone-200 rounded-xl overflow-hidden text-xs">
            <table className="w-full text-left divide-y divide-stone-200">
              <thead className="bg-stone-50 text-stone-600 font-bold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="px-3.5 py-2.5">Financial Year</th>
                  <th className="px-3.5 py-2.5">Status</th>
                  <th className="px-3.5 py-2.5">Ingested Rows</th>
                  <th className="px-3.5 py-2.5">Source Authority</th>
                  <th className="px-3.5 py-2.5">Ingestion Capability</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 bg-white">
                {sourceRegistry.sources.map((src) => {
                  const isIngested = src.status === 'INGESTED';
                  return (
                    <tr key={src.financial_year} className="hover:bg-stone-50/50">
                      <td className="px-3.5 py-2.5 font-bold text-stone-900">{src.financial_year}</td>
                      <td className="px-3.5 py-2.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            isIngested
                              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                              : 'bg-amber-50 text-amber-800 border border-amber-200'
                          }`}
                        >
                          {src.status.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="px-3.5 py-2.5 font-mono">
                        {src.total_observations_ingested > 0 ? src.total_observations_ingested.toLocaleString() : '0'}
                      </td>
                      <td className="px-3.5 py-2.5 text-stone-700 max-w-xs truncate" title={src.source_portal}>
                        {src.source_portal}
                      </td>
                      <td className="px-3.5 py-2.5 text-stone-600 font-mono text-[11px]">
                        {src.ingestion_readiness}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Acquisition Blocker & Cross-Year Warning Notice */}
        {comparability && comparability.comparability_warnings.length > 0 && (
          <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200 text-amber-950 text-xs space-y-1.5">
            <div className="flex items-center gap-2 font-bold text-amber-900">
              <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>Cross-Year Comparability Notice</span>
            </div>
            <ul className="list-disc list-inside space-y-1 text-amber-900/90 pl-1">
              {comparability.comparability_warnings.map((w, idx) => (
                <li key={idx}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* 3. Monthly Trajectory & Zero vs Missing Breakdown */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-4">
        <h3 className="text-base font-bold text-[var(--text-primary)]">
          Chronological Trajectory ({overview.financial_year})
        </h3>

        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-2.5">
          {overview.points.map((pt) => {
            const isMissing = pt.is_missing;
            const isZero = pt.is_zero;
            return (
              <div
                key={pt.month}
                className={`p-3 rounded-xl border text-center transition ${
                  isMissing
                    ? 'bg-rose-50/60 border-rose-200 text-rose-800'
                    : isZero
                    ? 'bg-amber-50/60 border-amber-200 text-amber-800'
                    : 'bg-white border-stone-200 text-stone-900 shadow-2xs'
                }`}
              >
                <p className="text-[11px] font-bold text-stone-500 mb-0.5">{pt.month}</p>
                <p className="text-base font-extrabold">
                  {isMissing ? 'MISSING' : isZero ? '0' : pt.value !== null ? pt.value.toLocaleString() : 'N/A'}
                </p>
                <span
                  className={`inline-block mt-1 text-[9px] px-1.5 py-0.2 rounded font-bold uppercase tracking-wider ${
                    isMissing
                      ? 'bg-rose-200 text-rose-900'
                      : isZero
                      ? 'bg-amber-200 text-amber-900'
                      : 'bg-emerald-100 text-emerald-900'
                  }`}
                >
                  {pt.value_type}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Forecasting Readiness & Hold-Out Baseline Evaluation Section */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-violet-50 text-violet-800 border border-violet-200">
                <Sparkles className="w-3.5 h-3.5" />
                {readiness?.readiness_status ? readiness.readiness_status.replace(/_/g, ' ') : 'Forecasting Foundation'}
              </span>
              <span className="text-xs text-stone-500 font-semibold">Phase 14C & 15D</span>
            </div>
            <h3 className="text-lg font-bold text-[var(--text-primary)]">
              Chronological Hold-Out Evaluation & Baseline Projections
            </h3>
          </div>

          {/* Horizon Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-stone-600">Horizon:</span>
            {[1, 2, 3].map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                  horizon === h
                    ? 'bg-violet-600 text-white shadow-2xs'
                    : 'bg-stone-100 text-stone-700 hover:bg-stone-200'
                }`}
              >
                {h}M
              </button>
            ))}
          </div>
        </div>

        {/* Evaluation Context & Single-Year Disclosure */}
        <div className="p-3.5 rounded-xl bg-stone-100/80 border border-stone-200/80 text-stone-700 text-xs leading-relaxed space-y-1">
          <p>
            <strong className="text-stone-900">Single-Year Dataset Limitation:</strong>{' '}
            {readiness?.dataset_limitation}
          </p>
          <p className="text-stone-500 italic">
            Clinical Disclaimer: {readiness?.clinical_validation_disclaimer}
          </p>
        </div>

        {readiness && readiness.is_ready ? (
          <div className="space-y-6">
            {/* Split Information Ribbon */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="p-3.5 rounded-xl bg-violet-50/50 border border-violet-200/60">
                <p className="text-violet-900 font-bold mb-1">
                  Training Window (9 Months): {readiness.training_period?.start_month} –{' '}
                  {readiness.training_period?.end_month}
                </p>
                <p className="text-stone-600 text-[11px]">
                  Models fit exclusively on the initial 9 months. Zero future-data leakage into evaluation.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-emerald-50/50 border border-emerald-200/60">
                <p className="text-emerald-900 font-bold mb-1">
                  Evaluation Hold-Out ({readiness.requested_horizon} Months): {readiness.evaluation_period?.start_month}{' '}
                  – {readiness.evaluation_period?.end_month}
                </p>
                <p className="text-stone-600 text-[11px]">
                  Candidate forecasts tested strictly on unseen held-out historical observation points.
                </p>
              </div>
            </div>

            {/* Model Comparison Table */}
            <div>
              <h4 className="text-xs font-bold text-stone-700 uppercase tracking-wider mb-2">
                Candidate Baseline Evaluation
              </h4>
              <div className="border border-stone-200 rounded-xl overflow-hidden text-xs">
                <table className="w-full text-left divide-y divide-stone-200">
                  <thead className="bg-stone-50 text-stone-600 font-bold uppercase tracking-wider text-[11px]">
                    <tr>
                      <th className="px-3.5 py-2.5">Model</th>
                      <th className="px-3.5 py-2.5">Type</th>
                      <th className="px-3.5 py-2.5">MAE</th>
                      <th className="px-3.5 py-2.5">RMSE</th>
                      <th className="px-3.5 py-2.5">MAPE</th>
                      <th className="px-3.5 py-2.5">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100 bg-white">
                    {readiness.baseline_models_evaluated.map((mod) => {
                      const isSelected = mod.model_name === readiness.selected_baseline_model;
                      const m = mod.evaluation_metrics || (mod as any).metrics || { mae: 0, rmse: 0, mape: 0 };
                      return (
                        <tr key={mod.model_name} className={isSelected ? 'bg-violet-50/40 font-semibold' : ''}>
                          <td className="px-3.5 py-2.5 text-stone-900 flex items-center gap-1.5">
                            {isSelected && <Sparkles className="w-3.5 h-3.5 text-violet-600" />}
                            <span>{mod.model_name}</span>
                          </td>
                          <td className="px-3.5 py-2.5 text-stone-600 font-mono">{(mod as any).model_type || 'Baseline'}</td>
                          <td className="px-3.5 py-2.5 font-mono">{m.mae.toLocaleString()}</td>
                          <td className="px-3.5 py-2.5 font-mono">{m.rmse.toLocaleString()}</td>
                          <td className="px-3.5 py-2.5 font-mono">{m.mape}%</td>
                          <td className="px-3.5 py-2.5">
                            {isSelected ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-violet-100 text-violet-800">
                                Selected
                              </span>
                            ) : (
                              <span className="text-stone-400 text-[11px]">Candidate</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Forward Baseline Projections */}
            {readiness.baseline_forecast.length > 0 && (
              <div>
                <h4 className="text-xs font-bold text-stone-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Forward Baseline Estimates ({readiness.selected_baseline_model})</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {readiness.baseline_forecast.map((fc) => (
                    <div key={fc.month} className="p-3.5 rounded-xl bg-white border border-stone-200 shadow-2xs space-y-1">
                      <p className="text-xs font-bold text-stone-500">{fc.month}</p>
                      <p className="text-xl font-extrabold text-stone-900">{fc.predicted_value.toLocaleString()}</p>
                      <p className="text-[11px] text-stone-500 font-mono">
                        95% Bounds: [{fc.lower_bound.toLocaleString()} – {fc.upper_bound.toLocaleString()}]
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-4 rounded-xl bg-stone-50 border border-stone-200 text-xs text-stone-700 space-y-1">
            <p className="font-bold text-stone-900">Forecasting Deferred:</p>
            <p>{readiness?.readiness_reason}</p>
          </div>
        )}
      </div>

      {/* 5. Phase 15E: Conservative Anomaly & Operational Review Workflow */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-50 text-rose-800 border border-rose-200">
                <ShieldAlert className="w-3.5 h-3.5" />
                Early-Warning & Review
              </span>
              <span className="text-xs text-stone-500 font-semibold">Phase 14D & 15E</span>
            </div>
            <h3 className="text-lg font-bold text-[var(--text-primary)]">
              Statistical Anomaly & Operational Change Signals
            </h3>
          </div>
          <span className="text-xs font-bold px-3 py-1 rounded-full bg-stone-100 text-stone-700">
            {anomalies?.total_signals_detected || 0} Signal(s) Detected
          </span>
        </div>

        {/* Regulatory Governance Disclaimer */}
        <div className="p-3.5 rounded-xl bg-stone-100/80 border border-stone-200/80 text-stone-700 text-xs leading-relaxed flex items-start gap-2.5">
          <Info className="w-4 h-4 text-stone-500 shrink-0 mt-0.5" />
          <p>
            <strong className="text-stone-900">Governance & Usage Boundary:</strong> Statistical anomaly signals
            indicate data patterns requiring human clinical review. The administrative review workflow records
            acknowledgement, notes, and resolution actions in an immutable audit trail without modifying historical observations.
          </p>
        </div>

        {/* Anomaly Signals List */}
        {anomalies && anomalies.signals.length > 0 ? (
          <div className="space-y-3">
            {anomalies.signals.map((sig) => {
              const isElevated = sig.severity === 'ELEVATED';
              const isWarning = sig.severity === 'WARNING';
              const reviewStatus = sig.review_status || 'OPEN';

              return (
                <div
                  key={sig.signal_id}
                  className={`p-4 rounded-xl border text-xs space-y-3 transition ${
                    isElevated
                      ? 'bg-rose-50/50 border-rose-200/80'
                      : isWarning
                      ? 'bg-amber-50/50 border-amber-200/80'
                      : 'bg-stone-50 border-stone-200'
                  }`}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          isElevated
                            ? 'bg-rose-600 text-white'
                            : isWarning
                            ? 'bg-amber-600 text-white'
                            : 'bg-stone-600 text-white'
                        }`}
                      >
                        {sig.severity}
                      </span>
                      <span className="font-bold text-stone-800">
                        {sig.signal_type.replace(/_/g, ' ')}
                      </span>
                      <span className="text-stone-500 font-mono">
                        Period: {sig.reporting_month}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Review Status Badge */}
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                          reviewStatus === 'RESOLVED'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                            : reviewStatus === 'UNDER_REVIEW'
                            ? 'bg-purple-50 text-purple-800 border-purple-300'
                            : reviewStatus === 'ACKNOWLEDGED'
                            ? 'bg-amber-50 text-amber-800 border-amber-300'
                            : reviewStatus === 'REOPENED'
                            ? 'bg-rose-50 text-rose-800 border-rose-300'
                            : 'bg-stone-100 text-stone-700 border-stone-300'
                        }`}
                      >
                        Status: {reviewStatus}
                      </span>

                      {/* Review Action Trigger Button */}
                      <button
                        onClick={() => handleOpenReviewModal(sig)}
                        className="px-2.5 py-1 rounded bg-white hover:bg-stone-100 text-stone-800 border border-stone-300 text-[11px] font-semibold flex items-center gap-1 shadow-2xs transition"
                      >
                        <UserCheck className="w-3 h-3 text-stone-600" />
                        <span>Review & Audit</span>
                      </button>
                    </div>
                  </div>

                  <p className="text-stone-800 leading-relaxed font-medium">
                    {sig.rationale}
                  </p>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-stone-500 pt-1 border-t border-stone-200/60 font-mono">
                    <span>Method: {sig.statistical_method}</span>
                    <span>
                      Observed: {sig.observed_value !== null ? sig.observed_value.toLocaleString() : 'MISSING'} |
                      Baseline: {sig.expected_baseline !== null ? sig.expected_baseline?.toLocaleString() : 'N/A'}
                    </span>
                    {sig.last_reviewed_by_username && (
                      <span className="text-stone-600">
                        Last review: {sig.last_reviewed_by_username} (
                        {sig.last_reviewed_at ? sig.last_reviewed_at.split('T')[0] : ''})
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 text-center bg-stone-50 rounded-xl border border-stone-200">
            <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
            <p className="text-sm font-bold text-stone-800">No Statistical Anomalies Detected</p>
            <p className="text-xs text-stone-500 mt-1">
              Monthly values for {district} remain within documented 3.5x MAD tolerance and expected reporting thresholds.
            </p>
          </div>
        )}
      </div>

      {/* Review & Audit Modal (Phase 15E) */}
      {selectedSignal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
          <div className="bg-white border border-stone-200 rounded-2xl shadow-xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-stone-200">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                <h3 className="text-sm font-bold text-stone-900">
                  Anomaly Signal Review & Governance
                </h3>
              </div>
              <button
                onClick={() => setSelectedSignal(null)}
                className="text-stone-400 hover:text-stone-600 p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Signal Details Summary */}
            <div className="p-3.5 rounded-xl bg-stone-50 border border-stone-200 space-y-1.5 font-mono text-[11px]">
              <div className="flex justify-between">
                <span className="text-stone-500">Signal ID:</span>
                <span className="font-bold text-stone-900">{selectedSignal.signal_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-stone-500">District & Month:</span>
                <span className="font-bold text-stone-900">
                  {selectedSignal.district} ({selectedSignal.reporting_month})
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-stone-500">Current Status:</span>
                <span className="font-bold text-violet-700">
                  {activeReviewDetail?.current_status || selectedSignal.review_status || 'OPEN'}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="space-y-2">
              <p className="font-bold text-stone-700">Administrative Transition Action:</p>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                <button
                  disabled={reviewActionLoading}
                  onClick={() => handleExecuteReviewAction('ACKNOWLEDGE')}
                  className="px-2.5 py-1.5 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 font-bold transition disabled:opacity-50"
                >
                  Acknowledge
                </button>
                <button
                  disabled={reviewActionLoading}
                  onClick={() => handleExecuteReviewAction('SET_UNDER_REVIEW')}
                  className="px-2.5 py-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-900 border border-purple-300 font-bold transition disabled:opacity-50"
                >
                  Under Review
                </button>
                <button
                  disabled={reviewActionLoading}
                  onClick={() => handleExecuteReviewAction('RESOLVE')}
                  className="px-2.5 py-1.5 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-900 border border-emerald-300 font-bold transition disabled:opacity-50"
                >
                  Resolve
                </button>
                <button
                  disabled={reviewActionLoading}
                  onClick={() => handleExecuteReviewAction('REOPEN')}
                  className="px-2.5 py-1.5 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-900 border border-rose-300 font-bold transition disabled:opacity-50"
                >
                  Reopen
                </button>
              </div>
            </div>

            {/* Notes / Reason Textarea */}
            <div className="space-y-1">
              <label className="font-bold text-stone-700 flex items-center gap-1">
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Audit Note / Resolution Explanation:</span>
              </label>
              <textarea
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value)}
                placeholder="Enter field investigation findings, data-entry correction, or resolution rationale..."
                className="w-full h-20 p-2.5 rounded-lg border border-stone-200 text-xs focus:ring-1 focus:ring-violet-500 focus:outline-hidden"
              />
              <button
                disabled={reviewActionLoading || !reviewNote.trim()}
                onClick={() => handleExecuteReviewAction('ADD_NOTE')}
                className="px-3 py-1 rounded-md bg-stone-100 hover:bg-stone-200 text-stone-700 font-semibold border border-stone-300 transition text-[11px] disabled:opacity-40"
              >
                Add Note Only
              </button>
            </div>

            {reviewActionError && (
              <p className="text-rose-600 font-bold text-[11px]">{reviewActionError}</p>
            )}

            {/* Audit History Timeline */}
            <div className="pt-3 border-t border-stone-200 space-y-2">
              <h4 className="font-bold text-stone-800 flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-stone-500" />
                <span>Immutable Review Audit Trail</span>
              </h4>

              {activeReviewDetail && activeReviewDetail.actions.length > 0 ? (
                <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                  {activeReviewDetail.actions.map((act) => (
                    <div key={act.id} className="p-2 rounded-lg bg-stone-50 border border-stone-200 space-y-0.5">
                      <div className="flex justify-between items-center text-[10px]">
                        <span className="font-bold text-stone-900">{act.username}</span>
                        <span className="text-stone-400 font-mono">{act.created_at.split('.')[0]}</span>
                      </div>
                      <p className="text-[11px] font-semibold text-stone-700">
                        {act.action}: <span className="font-mono">{act.from_status}</span> &rarr;{' '}
                        <span className="font-mono">{act.to_status}</span>
                      </p>
                      {act.notes && <p className="text-[11px] text-stone-600 italic">"{act.notes}"</p>}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-stone-400 italic text-[11px]">No previous review actions logged.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
