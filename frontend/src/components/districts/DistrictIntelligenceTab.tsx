import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Info,
  Calendar,
  Sparkles,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';
import { api } from '../../api/client';
import type {
  VerifiedIndicatorOverviewResponse,
  ForecastingReadinessResponse,
  DistrictAnomalyReportResponse,
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
    ])
      .then(([ov, rd, an]) => {
        setOverview(ov);
        setReadiness(rd);
        setAnomalies(an);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Error fetching healthcare intelligence data.');
        setLoading(false);
      });
  }, [district, sNo, subgroupType, financialYear, horizon]);

  useEffect(() => {
    fetchIntelligenceData();
  }, [fetchIntelligenceData]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="p-4 rounded-xl bg-stone-50 border border-stone-200 text-xs text-stone-600 flex items-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-stone-500" />
          <span>Evaluating verified indicator coverage, forecasting readiness, and conservative early-warning signals...</span>
        </div>
        <LoadingState type="chart" />
      </div>
    );
  }

  if (error) {
    return (
      <ErrorState
        title="Healthcare Intelligence Unavailable"
        message={error}
        onRetry={fetchIntelligenceData}
      />
    );
  }

  if (!overview) {
    return (
      <div className="p-8 text-center bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl">
        <Info className="w-8 h-8 mx-auto text-stone-400 mb-2" />
        <p className="text-stone-600 font-medium">Please select a verified clinical indicator to view healthcare intelligence.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 1. Header Provenance & Indicator Banner */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-800 border border-teal-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                VERIFIED Indicator
              </span>
              <span className="text-xs font-semibold text-stone-500">
                MoHFW Item {overview.s_no}
              </span>
              <span className="text-xs px-2 py-0.5 rounded-md bg-stone-100 text-stone-700">
                {overview.category}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-bold text-[var(--text-primary)]">
              {overview.canonical_name}
            </h2>
            <p className="text-xs text-stone-500 font-mono">
              Raw Label: {overview.parameter_name} ({overview.unit})
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchIntelligenceData}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-700 transition"
              title="Refresh intelligence metrics"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Clinical Rationale & Non-Additive Stock Notice */}
        <div className="text-xs text-stone-600 bg-stone-50 p-3.5 rounded-xl border border-stone-200/60 leading-relaxed">
          <p className="font-semibold text-stone-800 mb-1">Clinical Provenance & Mapping Rationale:</p>
          <p>{overview.rationale}</p>
          {overview.stock_warning && (
            <div className="mt-2.5 flex items-center gap-2 p-2 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 font-medium">
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600" />
              <span>{overview.stock_warning}</span>
            </div>
          )}
        </div>
      </div>

      {/* 2. Coverage & Completeness Ribbon */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider">Reporting Completeness</p>
          <p className="text-2xl font-extrabold text-[var(--text-primary)] mt-1">
            {(overview.completeness_ratio * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-stone-500 mt-1">
            {overview.reported_months_count} of {overview.total_expected_months} expected months
          </p>
        </div>

        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider">Valid / Zero Returns</p>
          <p className="text-2xl font-extrabold text-emerald-700 mt-1">
            {overview.valid_months_count} / {overview.zero_months_count}
          </p>
          <p className="text-xs text-stone-500 mt-1">
            {overview.zero_months_count} confirmed zero events
          </p>
        </div>

        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider">Missing Months</p>
          <p className="text-2xl font-extrabold text-rose-600 mt-1">
            {overview.missing_months_count}
          </p>
          <p className="text-xs text-stone-500 mt-1">
            {overview.missing_months_count === 0 ? 'Zero missing returns' : 'Unreported periods'}
          </p>
        </div>

        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 shadow-xs">
          <p className="text-xs font-semibold text-stone-500 uppercase tracking-wider">12-Month Median</p>
          <p className="text-2xl font-extrabold text-indigo-700 mt-1">
            {overview.median_value !== null ? overview.median_value.toLocaleString() : 'N/A'}
          </p>
          <p className="text-xs text-stone-500 mt-1">
            Mean: {overview.mean_value !== null ? overview.mean_value.toLocaleString() : 'N/A'} {overview.unit}
          </p>
        </div>
      </div>

      {/* 3. Monthly Trajectory Sequence */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-3">
        <h3 className="text-sm font-bold text-stone-800 uppercase tracking-wider flex items-center gap-2">
          <Calendar className="w-4 h-4 text-stone-500" />
          <span>Chronological Fiscal Trajectory (FY {overview.financial_year})</span>
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-2 pt-2">
          {overview.points.map((pt) => {
            const isZero = pt.is_zero;
            const isMiss = pt.is_missing;
            return (
              <div
                key={pt.month}
                className={`p-3 rounded-xl border text-center transition ${
                  isMiss
                    ? 'bg-rose-50/70 border-rose-200 text-rose-900'
                    : isZero
                    ? 'bg-amber-50/70 border-amber-200 text-amber-900'
                    : 'bg-emerald-50/60 border-emerald-200 text-emerald-900'
                }`}
              >
                <p className="text-xs font-bold text-stone-600">{pt.month}</p>
                <p className="text-base font-extrabold mt-1">
                  {isMiss ? 'MISSING' : isZero ? '0' : pt.value?.toLocaleString()}
                </p>
                <span
                  className={`inline-block mt-1 text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${
                    isMiss
                      ? 'bg-rose-200/60 text-rose-800'
                      : isZero
                      ? 'bg-amber-200/60 text-amber-800'
                      : 'bg-emerald-200/60 text-emerald-800'
                  }`}
                >
                  {pt.value_type}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. Forecasting Readiness & Baseline Models Section */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                  readiness?.is_ready
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border border-amber-200'
                }`}
              >
                {readiness?.is_ready ? (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Eligible for Baseline Evaluation
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-3.5 h-3.5" />
                    {readiness?.readiness_status || 'Insufficient History'}
                  </>
                )}
              </span>
              <span className="text-xs text-stone-500 font-semibold">Phase 14C Evaluation</span>
            </div>
            <h3 className="text-lg font-bold text-[var(--text-primary)]">
              Forecasting Readiness & Chronological Baseline Evaluation
            </h3>
          </div>

          {/* Horizon Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-stone-600">Horizon:</span>
            {[1, 2, 3, 6, 12].map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`px-2.5 py-1 text-xs font-bold rounded-lg border transition ${
                  horizon === h
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                    : 'bg-stone-50 text-stone-700 border-stone-200 hover:bg-stone-100'
                }`}
              >
                {h}M
              </button>
            ))}
          </div>
        </div>

        {/* Dataset Limitation Disclosure */}
        <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200/80 text-amber-900 text-xs space-y-2 leading-relaxed">
          <div className="flex items-center gap-2 font-bold text-amber-950">
            <Info className="w-4 h-4 text-amber-700 shrink-0" />
            <span>Single-Year Dataset Limitation & Evaluation Governance:</span>
          </div>
          <p>{readiness?.dataset_limitation}</p>
          <p className="font-medium text-stone-600">{readiness?.clinical_validation_disclaimer}</p>
        </div>

        {readiness?.is_ready ? (
          <div className="space-y-6">
            {/* Split Breakdown */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-stone-50 border border-stone-200 text-xs space-y-1">
                <span className="font-bold text-stone-700 uppercase tracking-wider">Training Period (Zero Leakage)</span>
                <p className="text-base font-extrabold text-stone-900">
                  {readiness.training_period?.start_month} to {readiness.training_period?.end_month}
                </p>
                <p className="text-stone-500">{readiness.training_period?.months_count} historical training months</p>
              </div>
              <div className="p-4 rounded-xl bg-indigo-50/60 border border-indigo-200 text-xs space-y-1">
                <span className="font-bold text-indigo-900 uppercase tracking-wider">Hold-Out Evaluation Period</span>
                <p className="text-base font-extrabold text-indigo-950">
                  {readiness.evaluation_period?.start_month} to {readiness.evaluation_period?.end_month}
                </p>
                <p className="text-indigo-700">{readiness.evaluation_period?.months_count} unseen test months</p>
              </div>
            </div>

            {/* Model Comparison Table */}
            <div>
              <h4 className="text-xs font-bold text-stone-700 uppercase tracking-wider mb-2">
                Candidate Baseline Models (Hold-Out Split Validation)
              </h4>
              <div className="overflow-x-auto rounded-xl border border-stone-200">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-stone-100 text-stone-700 font-bold">
                    <tr>
                      <th className="p-3">Baseline Model</th>
                      <th className="p-3">Hold-Out MAE</th>
                      <th className="p-3">Hold-Out RMSE</th>
                      <th className="p-3">Hold-Out sMAPE</th>
                      <th className="p-3">Hold-Out WAPE</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-200 bg-white">
                    {readiness.baseline_models_evaluated.map((m) => {
                      const isSelected = m.model_name === readiness.selected_baseline_model;
                      return (
                        <tr key={m.model_name} className={isSelected ? 'bg-indigo-50/40 font-semibold' : ''}>
                          <td className="p-3 text-stone-900 flex items-center gap-2">
                            {isSelected && <Sparkles className="w-3.5 h-3.5 text-indigo-600" />}
                            <span>{m.model_name}</span>
                          </td>
                          <td className="p-3 font-mono">{m.evaluation_metrics.mae.toFixed(2)}</td>
                          <td className="p-3 font-mono">{m.evaluation_metrics.rmse.toFixed(2)}</td>
                          <td className="p-3 font-mono">{m.evaluation_metrics.smape.toFixed(2)}%</td>
                          <td className="p-3 font-mono">{m.evaluation_metrics.wape.toFixed(2)}%</td>
                          <td className="p-3">
                            {isSelected ? (
                              <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-100 text-indigo-800">
                                SELECTED BEST
                              </span>
                            ) : (
                              <span className="text-stone-400">Baseline</span>
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

      {/* 5. Conservative Anomaly & Change Detection Section */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-rose-50 text-rose-800 border border-rose-200">
                <ShieldAlert className="w-3.5 h-3.5" />
                Conservative Early-Warning
              </span>
              <span className="text-xs text-stone-500 font-semibold">Phase 14D</span>
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
            represent mathematical dispersion (Median Absolute Deviation & Volatility Threshing). They indicate data
            patterns requiring human review by HMIS officers and do <em>not</em> constitute clinical diagnoses, disease
            outbreaks, or evidence of reporting fraud.
          </p>
        </div>

        {/* Anomaly Signals List */}
        {anomalies && anomalies.signals.length > 0 ? (
          <div className="space-y-3">
            {anomalies.signals.map((sig) => {
              const isElevated = sig.severity === 'ELEVATED';
              const isWarning = sig.severity === 'WARNING';
              return (
                <div
                  key={sig.signal_id}
                  className={`p-4 rounded-xl border text-xs space-y-2 transition ${
                    isElevated
                      ? 'bg-rose-50/60 border-rose-200/80 text-rose-950'
                      : isWarning
                      ? 'bg-amber-50/60 border-amber-200/80 text-amber-950'
                      : 'bg-stone-50 border-stone-200 text-stone-900'
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

                    <div className="font-mono font-bold text-stone-700">
                      Score: {sig.deviation_score}x
                    </div>
                  </div>

                  <p className="text-stone-800 leading-relaxed font-medium">
                    {sig.rationale}
                  </p>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-[11px] text-stone-500 pt-1 border-t border-stone-200/60 font-mono">
                    <span>Method: {sig.statistical_method}</span>
                    <span>Observed: {sig.observed_value !== null ? sig.observed_value.toLocaleString() : 'MISSING'} | Baseline: {sig.expected_baseline !== null ? sig.expected_baseline?.toLocaleString() : 'N/A'}</span>
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
    </div>
  );
};
