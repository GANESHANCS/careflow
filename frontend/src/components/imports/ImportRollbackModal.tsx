import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  RotateCcw,
  AlertTriangle,
  AlertOctagon,
  FileSpreadsheet,
  Clock,
  Database,
} from 'lucide-react';
import { api } from '../../api/client';
import type { ImportJob, ImportRollbackResponse } from '../../api/types';
import { Button } from '../buttons/Button';

export interface ImportRollbackModalProps {
  job: ImportJob | null;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (result: ImportRollbackResponse) => void;
}

export const ImportRollbackModal: React.FC<ImportRollbackModalProps> = ({
  job,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isConflict, setIsConflict] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setReason('');
      setError(null);
      setIsConflict(false);
      setLoading(false);
    }
  }, [isOpen, job]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !loading) {
        onClose();
      }
    };
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, loading, onClose]);

  if (!isOpen || !job) return null;

  const handleRollback = async () => {
    if (loading) return;
    setLoading(true);
    setError(null);
    setIsConflict(false);

    try {
      const res = await api.rollbackImport(job.job_code, reason.trim() || undefined);
      setLoading(false);
      onSuccess(res);
      onClose();
    } catch (err: any) {
      setLoading(false);
      const msg = err.message || 'Failed to rollback import job.';
      setError(msg);
      if (err.status === 409 || msg.toLowerCase().includes('subsequent')) {
        setIsConflict(true);
      }
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={() => !loading && onClose()}
          className="absolute inset-0"
        />

        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 8 }}
          transition={{ duration: 0.2 }}
          className="relative w-full max-w-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl shadow-xl overflow-hidden flex flex-col z-10"
        >
          {/* Header */}
          <div className="p-6 border-b border-[var(--border-subtle)] flex items-center justify-between bg-[var(--bg-surface-subtle)]">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-[var(--coral-50)] text-[var(--coral-700)] border border-[var(--coral-200)] flex items-center justify-center shadow-xs">
                <RotateCcw className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-display font-bold text-base sm:text-lg text-[var(--text-primary)]">
                  Roll Back HMIS Import Dataset
                </h3>
                <p className="text-xs text-[var(--text-secondary)]">
                  Revert observations and provenance for job <span className="font-mono font-semibold">{job.job_code}</span>
                </p>
              </div>
            </div>
            <button
              onClick={() => !loading && onClose()}
              disabled={loading}
              className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition-colors disabled:opacity-50"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-5 max-h-[70vh] overflow-y-auto">
            {/* Warning Banner */}
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex gap-3 text-xs leading-relaxed">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <span className="font-bold text-amber-900 block">
                  Important: This operation modifies database records
                </span>
                <p className="text-amber-800">
                  Rolling back this import will restore the state of the database to prior to this job:
                </p>
                <ul className="list-disc list-inside space-y-0.5 text-amber-800 pt-1">
                  <li>Observations created by this import will be <strong>deleted</strong>.</li>
                  <li>Observations updated by this import will have their previous values and provenance <strong>restored</strong>.</li>
                  <li>Associated data quality evaluation records will be removed.</li>
                  <li>Original upload file and error logs will be retained for audit compliance.</li>
                </ul>
              </div>
            </div>

            {/* Target Job Summary */}
            <div className="p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)] flex items-center gap-1.5">
                  <FileSpreadsheet className="w-3.5 h-3.5 text-[var(--teal-600)]" />
                  Filename:
                </span>
                <span className="font-semibold text-[var(--text-primary)] truncate max-w-[240px]">
                  {job.original_filename}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)] flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-[var(--teal-600)]" />
                  Records Imported:
                </span>
                <span className="font-mono font-bold text-[var(--text-primary)]">
                  {job.records_imported.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-[var(--text-muted)] flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-[var(--teal-600)]" />
                  Current Status:
                </span>
                <span className="font-mono font-semibold text-xs px-2 py-0.5 rounded bg-[var(--emerald-50)] text-[var(--emerald-800)] border border-[var(--emerald-200)]">
                  {job.status}
                </span>
              </div>
            </div>

            {/* Reason input */}
            <div className="space-y-1.5">
              <label htmlFor="rollback-reason" className="block text-xs font-bold text-[var(--text-primary)]">
                Audit Reason / Justification <span className="text-[var(--text-muted)] font-normal">(Optional)</span>
              </label>
              <textarea
                id="rollback-reason"
                rows={2}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                disabled={loading}
                placeholder="e.g., Ingested incorrect facility reporting month, re-uploading corrected data."
                className="w-full text-xs px-3 py-2 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] focus-ring text-[var(--text-primary)] placeholder-[var(--text-muted)] resize-none"
              />
            </div>

            {/* Error / Conflict Feedback */}
            {error && (
              <div className={`p-4 rounded-xl border flex gap-3 text-xs leading-relaxed ${
                isConflict
                  ? 'bg-rose-500/10 border-rose-500/20 text-rose-800'
                  : 'bg-[var(--coral-50)] border-[var(--coral-200)] text-[var(--coral-800)]'
              }`}>
                <AlertOctagon className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold block">
                    {isConflict ? 'Cannot Roll Back: Dependent Imports Detected' : 'Rollback Request Rejected'}
                  </span>
                  <p>{error}</p>
                  {isConflict && (
                    <p className="text-[11px] text-rose-700 pt-1 font-medium">
                      To preserve continuous data provenance, roll back the newer dependent import job(s) first before attempting to roll back this dataset.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="p-4 sm:p-6 border-t border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] flex items-center justify-end gap-3">
            <Button
              variant="secondary"
              size="sm"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={handleRollback}
              isLoading={loading}
              disabled={loading}
              leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            >
              {loading ? 'Rolling Back...' : 'Confirm Rollback'}
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
