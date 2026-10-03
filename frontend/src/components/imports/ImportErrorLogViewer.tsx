import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertOctagon, AlertTriangle, AlertCircle, Info, ChevronLeft, ChevronRight, Loader2, CheckCircle2 } from 'lucide-react';
import { api } from '../../api/client';
import type { ImportErrorLogListResponse, ImportErrorLog } from '../../api/types';
import { Button } from '../buttons/Button';

export interface ImportErrorLogViewerProps {
  jobCode: string | null;
  isOpen: boolean;
  onClose: () => void;
}

export const ImportErrorLogViewer: React.FC<ImportErrorLogViewerProps> = ({
  jobCode,
  isOpen,
  onClose,
}) => {
  const [data, setData] = useState<ImportErrorLogListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    if (!isOpen || !jobCode) {
      setData(null);
      setError(null);
      setCurrentPage(1);
      return;
    }

    setLoading(true);
    setError(null);

    const skip = (currentPage - 1) * pageSize;
    api.getImportErrors(jobCode, { skip, limit: pageSize })
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to retrieve diagnostic error logs.');
        setLoading(false);
      });
  }, [isOpen, jobCode, currentPage]);

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

  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-[var(--coral-100)] text-[var(--coral-800)] border border-[var(--coral-300)]">
            <AlertOctagon className="w-3 h-3 text-[var(--coral-700)]" />
            CRITICAL
          </span>
        );
      case 'ERROR':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-[var(--coral-50)] text-[var(--coral-700)] border border-[var(--coral-200)]">
            <AlertCircle className="w-3 h-3 text-[var(--coral-600)]" />
            ERROR
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-[var(--amber-50)] text-[var(--amber-800)] border border-[var(--amber-200)]">
            <AlertTriangle className="w-3 h-3 text-[var(--amber-600)]" />
            WARNING
          </span>
        );
      case 'INFO':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-[var(--teal-50)] text-[var(--teal-800)] border border-[var(--teal-200)]">
            <Info className="w-3 h-3 text-[var(--teal-600)]" />
            INFO
          </span>
        );
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 8 }}
          transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
          className="w-full max-w-4xl bg-[var(--bg-surface-elevated)] border border-[var(--border-subtle)] rounded-2xl shadow-float max-h-[90vh] flex flex-col overflow-hidden text-[var(--text-primary)]"
          role="dialog"
          aria-modal="true"
          aria-labelledby="error-modal-title"
        >
          {/* Modal Header */}
          <div className="px-6 py-4 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-surface)]">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[var(--amber-50)] text-[var(--amber-700)] border border-[var(--amber-200)] flex items-center justify-center shadow-xs">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 id="error-modal-title" className="font-display font-bold text-base text-[var(--text-primary)]">
                  Import Diagnostic & Audit Error Logs
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

          {/* Modal Content */}
          <div className="p-6 overflow-y-auto flex-1">
            {loading && (
              <div className="py-20 flex flex-col items-center justify-center gap-3 text-[var(--text-muted)]">
                <Loader2 className="w-8 h-8 animate-spin text-[var(--teal-600)]" />
                <span className="text-sm">Loading diagnostic logs...</span>
              </div>
            )}

            {error && (
              <div className="p-4 rounded-xl bg-[var(--coral-50)] border border-[var(--coral-200)] text-[var(--coral-800)] flex items-start gap-3 text-sm">
                <AlertCircle className="w-5 h-5 text-[var(--coral-600)] shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Audit Logs Unavailable</span>
                  {error}
                </div>
              </div>
            )}

            {!loading && !error && data && (
              <>
                {data.items.length === 0 ? (
                  <div className="py-12 px-6 rounded-2xl bg-[var(--emerald-50)] border border-[var(--emerald-200)] text-center flex flex-col items-center justify-center">
                    <div className="w-12 h-12 rounded-full bg-white text-[var(--emerald-600)] border border-[var(--emerald-200)] flex items-center justify-center mb-3 shadow-xs">
                      <CheckCircle2 className="w-6 h-6" />
                    </div>
                    <h4 className="font-display font-bold text-base text-[var(--emerald-900)] mb-1">
                      Clean Dataset Ingestion
                    </h4>
                    <p className="text-xs sm:text-sm text-[var(--emerald-800)] max-w-md mx-auto">
                      No structural errors, row validation failures, or diagnostic warnings were logged during execution for this job.
                    </p>
                  </div>
                ) : (
                  <div className="border border-[var(--border-subtle)] rounded-xl overflow-hidden shadow-xs">
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="bg-[var(--bg-surface-subtle)] border-b border-[var(--border-subtle)] text-[var(--text-muted)] font-bold uppercase tracking-wider text-[11px]">
                            <th className="py-3 px-3 w-16">Row</th>
                            <th className="py-3 px-3 w-28">Sheet</th>
                            <th className="py-3 px-3 w-28">Severity</th>
                            <th className="py-3 px-4 w-40">Error Code</th>
                            <th className="py-3 px-4">Message / Diagnostic Finding</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--border-subtle)]">
                          {data.items.map((log: ImportErrorLog) => (
                            <tr
                              key={log.id}
                              className="hover:bg-[var(--bg-surface-subtle)]/60 transition-colors"
                            >
                              <td className="py-3 px-3 font-mono text-[var(--text-secondary)] font-medium">
                                {log.source_row !== null && log.source_row !== undefined ? log.source_row : '—'}
                              </td>
                              <td className="py-3 px-3 font-mono text-[var(--text-secondary)] truncate max-w-[120px]">
                                {log.source_sheet || '—'}
                              </td>
                              <td className="py-3 px-3 whitespace-nowrap">
                                {getSeverityBadge(log.severity)}
                              </td>
                              <td className="py-3 px-4 font-mono font-semibold text-[var(--text-primary)]">
                                {log.error_code}
                              </td>
                              <td className="py-3 px-4 text-[var(--text-secondary)] leading-relaxed">
                                {log.message}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer with Pagination */}
          <div className="px-6 py-3.5 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
            <span className="text-[var(--text-muted)]">
              {data && data.total > 0
                ? `Showing ${(currentPage - 1) * pageSize + 1}–${Math.min(currentPage * pageSize, data.total)} of ${data.total} logged findings`
                : '0 audit logs'}
            </span>

            <div className="flex items-center gap-2">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage <= 1 || loading}
                leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
              >
                Previous
              </Button>
              <span className="px-2 font-mono text-[var(--text-secondary)]">
                {currentPage} / {totalPages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage >= totalPages || loading}
                rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
              >
                Next
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
