import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ShieldCheck, AlertTriangle, AlertCircle, Info, Loader2, CheckCircle2 } from 'lucide-react';
import { api } from '../../api/client';
import type { ImportJobQualityResponse } from '../../api/types';
import { Button } from '../buttons/Button';

export interface ImportQualityModalProps {
  jobCode: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ImportQualityModal: React.FC<ImportQualityModalProps> = ({
  jobCode,
  isOpen,
  onClose,
}) => {
  const [quality, setQuality] = useState<ImportJobQualityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !jobCode) {
      setQuality(null);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    api.getImportQuality(jobCode)
      .then((res) => {
        setQuality(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to retrieve quality audit report.');
        setLoading(false);
      });
  }, [isOpen, jobCode]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 8 }}
          transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-2xl bg-[var(--bg-surface-elevated)] border border-[var(--border-subtle)] rounded-2xl shadow-float max-h-[90vh] flex flex-col overflow-hidden text-[var(--text-primary)]"
          role="dialog"
          aria-modal="true"
          aria-labelledby="quality-modal-title"
        >
          {/* Header */}
          <div className="px-6 py-4 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-surface)]">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[var(--teal-50)] text-[var(--teal-600)] border border-[var(--teal-100)] flex items-center justify-center shadow-xs">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <h3 id="quality-modal-title" className="font-display font-bold text-base text-[var(--text-primary)]">
                  Data Quality Audit Report
                </h3>
                <span className="font-mono text-xs text-[var(--text-muted)]">
                  Job Code: {jobCode}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-subtle)] rounded-lg transition-colors focus-ring"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Modal Body */}
          <div className="p-6 overflow-y-auto space-y-6 flex-1">
            {loading && (
              <div className="py-16 flex flex-col items-center justify-center gap-3 text-[var(--text-muted)]">
                <Loader2 className="w-8 h-8 animate-spin text-[var(--teal-600)]" />
                <span className="text-sm">Retrieving dataset quality audit scores...</span>
              </div>
            )}

            {error && (
              <div className="p-4 rounded-xl bg-[var(--coral-50)] border border-[var(--coral-200)] text-[var(--coral-800)] flex items-start gap-3 text-sm">
                <AlertCircle className="w-5 h-5 text-[var(--coral-600)] shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Quality Audit Unavailable</span>
                  {error}
                </div>
              </div>
            )}

            {!loading && !error && quality && (
              <>
                {/* Overall Score & Severity Strip */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="sm:col-span-1 p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col items-center justify-center text-center">
                    <span className="text-xs uppercase font-bold tracking-wider text-[var(--text-muted)]">
                      Overall Quality Score
                    </span>
                    <div className="mt-2 text-4xl font-display font-extrabold text-[var(--teal-600)]">
                      {quality.overall_quality_score.toFixed(1)}%
                    </div>
                    <span className="mt-1 text-xs text-[var(--text-secondary)]">
                      {quality.overall_quality_score >= 90
                        ? 'High Confidence Dataset'
                        : quality.overall_quality_score >= 75
                        ? 'Acceptable with Warnings'
                        : 'Action Required'}
                    </span>
                  </div>

                  <div className="sm:col-span-2 p-5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] flex flex-col justify-between">
                    <div>
                      <span className="text-xs uppercase font-bold tracking-wider text-[var(--text-muted)] block mb-3">
                        Quality Audit Findings Distribution
                      </span>
                      <div className="grid grid-cols-4 gap-2">
                        <div className="p-2.5 rounded-lg bg-[var(--coral-50)] border border-[var(--coral-100)] text-center">
                          <span className="text-[10px] font-bold text-[var(--coral-700)] block">CRITICAL</span>
                          <span className="text-lg font-bold text-[var(--coral-700)]">
                            {quality.severity_counts?.CRITICAL ?? 0}
                          </span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-[var(--coral-50)]/70 border border-[var(--coral-100)] text-center">
                          <span className="text-[10px] font-bold text-[var(--coral-600)] block">ERROR</span>
                          <span className="text-lg font-bold text-[var(--coral-600)]">
                            {quality.severity_counts?.ERROR ?? 0}
                          </span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-[var(--amber-50)] border border-[var(--amber-100)] text-center">
                          <span className="text-[10px] font-bold text-[var(--amber-700)] block">WARNING</span>
                          <span className="text-lg font-bold text-[var(--amber-700)]">
                            {quality.severity_counts?.WARNING ?? 0}
                          </span>
                        </div>
                        <div className="p-2.5 rounded-lg bg-[var(--teal-50)] border border-[var(--teal-100)] text-center">
                          <span className="text-[10px] font-bold text-[var(--teal-700)] block">INFO</span>
                          <span className="text-lg font-bold text-[var(--teal-700)]">
                            {quality.severity_counts?.INFO ?? 0}
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="mt-3 text-xs text-[var(--text-muted)]">
                      Total anomalies audited: <span className="font-semibold text-[var(--text-primary)]">{quality.total_issues}</span>
                    </div>
                  </div>
                </div>

                {/* Category Scores */}
                {quality.category_scores && Object.keys(quality.category_scores).length > 0 && (
                  <div>
                    <h4 className="font-display font-semibold text-sm text-[var(--text-primary)] mb-3">
                      Data Quality Dimension Scores
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {Object.entries(quality.category_scores).map(([category, score]) => (
                        <div key={category} className="p-3.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                          <div className="flex items-center justify-between text-xs font-medium mb-1.5">
                            <span className="capitalize text-[var(--text-primary)]">{category}</span>
                            <span className="font-mono font-bold text-[var(--teal-700)]">{score.toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-[var(--bg-surface-subtle)] h-1.5 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-[var(--teal-600)] rounded-full transition-all duration-300"
                              style={{ width: `${Math.max(0, Math.min(100, score))}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Specific Findings List */}
                <div>
                  <h4 className="font-display font-semibold text-sm text-[var(--text-primary)] mb-3">
                    Diagnostic Quality Findings ({quality.findings?.length ?? 0})
                  </h4>
                  {quality.findings && quality.findings.length > 0 ? (
                    <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                      {quality.findings.map((finding, idx) => (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs flex items-start gap-2.5"
                        >
                          {finding.severity === 'CRITICAL' || finding.severity === 'ERROR' ? (
                            <AlertCircle className="w-4 h-4 text-[var(--coral-600)] shrink-0 mt-0.5" />
                          ) : finding.severity === 'WARNING' ? (
                            <AlertTriangle className="w-4 h-4 text-[var(--amber-600)] shrink-0 mt-0.5" />
                          ) : (
                            <Info className="w-4 h-4 text-[var(--teal-600)] shrink-0 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-semibold text-[var(--text-primary)]">{finding.code}</span>
                              <span className="font-mono px-1.5 py-0.2 rounded text-[10px] bg-[var(--bg-surface-subtle)] text-[var(--text-muted)] border border-[var(--border-subtle)]">
                                {finding.sheet ? `Sheet: ${finding.sheet}` : ''}
                                {finding.row !== null && finding.row !== undefined ? ` • Row: ${finding.row}` : ''}
                              </span>
                            </div>
                            <p className="mt-1 text-[var(--text-secondary)] leading-relaxed">
                              {finding.message}
                            </p>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 rounded-xl bg-[var(--emerald-50)] border border-[var(--emerald-200)] text-[var(--emerald-800)] text-xs flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-[var(--emerald-600)] shrink-0" />
                      <span>No quality discrepancies or anomaly flags recorded. Dataset passed all structural validations cleanly.</span>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-3.5 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] flex justify-end">
            <Button variant="secondary" size="sm" onClick={onClose}>
              Dismiss
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
