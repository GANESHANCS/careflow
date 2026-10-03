import React, { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { clsx } from 'clsx';
import { UploadCloud, FileSpreadsheet, AlertCircle, CheckCircle2, ShieldAlert, Loader2 } from 'lucide-react';
import { Button } from '../buttons/Button';
import { useAuth } from '../../auth/AuthContext';
import { api } from '../../api/client';
import type { ImportJob } from '../../api/types';

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50 MB
const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];

export interface FileUploadZoneProps {
  onUploadSuccess: (job: ImportJob) => void;
  className?: string;
}

export const FileUploadZone: React.FC<FileUploadZoneProps> = ({
  onUploadSuccess,
  className,
}) => {
  const { user } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<ImportJob | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  // RBAC permissions check
  const isViewer = user?.role === 'VIEWER';
  const canUpload = user?.role === 'ADMIN' || user?.role === 'ANALYST';

  const validateFile = (file: File): boolean => {
    setValidationError(null);
    setUploadError(null);
    setUploadSuccess(null);

    const lowerName = file.name.toLowerCase();
    const hasValidExt = ALLOWED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));

    if (!hasValidExt) {
      setValidationError('Unsupported file format. Please upload a .csv, .xlsx, or .xls file.');
      return false;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setValidationError(`File exceeds maximum allowed limit of 50 MB (selected file is ${sizeMB} MB).`);
      return false;
    }

    if (file.size === 0) {
      setValidationError('The selected file is empty (0 bytes). Please select a valid HMIS dataset.');
      return false;
    }

    return true;
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!canUpload || isUploading) return;
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (!canUpload || isUploading) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      } else {
        setSelectedFile(null);
      }
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      } else {
        setSelectedFile(null);
      }
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile || !canUpload || isUploading) return;

    setIsUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const job = await api.uploadImportFile(selectedFile);
      setUploadSuccess(job);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      onUploadSuccess(job);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Upload failed. Please try again.';
      setUploadError(message);
    } finally {
      setIsUploading(false);
    }
  };

  const handleClearSelection = () => {
    setSelectedFile(null);
    setValidationError(null);
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={clsx('w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 sm:p-8 shadow-xs', className)}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <h2 className="font-display font-bold text-lg text-[var(--text-primary)] flex items-center gap-2">
            <UploadCloud className="w-5 h-5 text-[var(--teal-600)]" />
            HMIS Spreadsheet Ingestion
          </h2>
          <p className="text-xs sm:text-sm text-[var(--text-secondary)] mt-0.5">
            Upload Ministry of Health & Family Welfare (MoHFW) standardized monthly healthcare reports.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] text-[var(--text-muted)]">
            Formats: CSV, XLSX, XLS (Max 50MB)
          </span>
        </div>
      </div>

      {/* VIEWER restricted banner */}
      {isViewer && (
        <div className="mb-6 p-4 rounded-xl bg-[var(--amber-50)] border border-[var(--amber-200)] text-[var(--amber-900)] flex items-start gap-3 text-xs sm:text-sm">
          <ShieldAlert className="w-5 h-5 text-[var(--amber-600)] shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block">Read-Only Access Restricted</span>
            Your account role (<code className="font-mono font-bold">VIEWER</code>) has permission to inspect historical imports, quality scorecards, and audit logs, but cannot upload new datasets. File ingestion requires <code className="font-mono font-bold">ANALYST</code> or <code className="font-mono font-bold">ADMIN</code> privileges.
          </div>
        </div>
      )}

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (canUpload && !isUploading && fileInputRef.current) {
            fileInputRef.current.click();
          }
        }}
        className={clsx(
          'relative border-2 border-dashed rounded-xl p-8 sm:p-12 text-center transition-all duration-200 flex flex-col items-center justify-center cursor-pointer select-none',
          canUpload && !isUploading
            ? isDragging
              ? 'border-[var(--teal-600)] bg-[var(--teal-50)]/50 scale-[1.005]'
              : 'border-[var(--border-default)] hover:border-[var(--teal-500)] hover:bg-[var(--bg-surface-subtle)]/70'
            : 'border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] cursor-not-allowed opacity-75'
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,text/csv,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          onChange={handleFileChange}
          disabled={!canUpload || isUploading}
          className="hidden"
          data-testid="hmis-file-input"
        />

        <div className="w-14 h-14 rounded-2xl bg-[var(--teal-50)] text-[var(--teal-600)] border border-[var(--teal-100)] flex items-center justify-center mb-4 shadow-xs">
          {isUploading ? (
            <Loader2 className="w-7 h-7 animate-spin text-[var(--teal-600)]" />
          ) : (
            <FileSpreadsheet className="w-7 h-7" />
          )}
        </div>

        <h3 className="font-display font-semibold text-base text-[var(--text-primary)] mb-1">
          {canUpload
            ? 'Drag & drop your HMIS file here, or click to browse'
            : 'File upload disabled for your role'}
        </h3>
        <p className="text-xs text-[var(--text-muted)] max-w-md mx-auto mb-4">
          Automated SHA-256 fingerprinting ensures idempotency. Zeros are safely preserved, missing values are never overwritten, and quality audits execute atomically.
        </p>

        {selectedFile && (
          <div
            onClick={(e) => e.stopPropagation()}
            className="mt-2 inline-flex items-center gap-3 px-4 py-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--teal-300)] shadow-xs text-xs sm:text-sm text-[var(--text-primary)]"
          >
            <FileSpreadsheet className="w-4 h-4 text-[var(--teal-600)]" />
            <span className="font-medium truncate max-w-xs">{selectedFile.name}</span>
            <span className="text-xs text-[var(--text-muted)]">
              ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
            </span>
            {!isUploading && (
              <button
                type="button"
                onClick={handleClearSelection}
                className="text-[var(--text-muted)] hover:text-[var(--coral-600)] ml-2 text-xs font-semibold focus-ring rounded"
              >
                Remove
              </button>
            )}
          </div>
        )}
      </div>

      {/* Validation or Error Message */}
      {validationError && (
        <div className="mt-4 p-3 rounded-lg bg-[var(--coral-50)] border border-[var(--coral-200)] text-[var(--coral-800)] flex items-center gap-2.5 text-xs sm:text-sm" role="alert">
          <AlertCircle className="w-4 h-4 text-[var(--coral-600)] shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Server Upload Error Message */}
      {uploadError && (
        <div className="mt-4 p-3 rounded-lg bg-[var(--coral-50)] border border-[var(--coral-200)] text-[var(--coral-800)] flex items-center gap-2.5 text-xs sm:text-sm" role="alert">
          <AlertCircle className="w-4 h-4 text-[var(--coral-600)] shrink-0" />
          <div className="flex-1">
            <span className="font-semibold block">Ingestion Failed</span>
            {uploadError}
          </div>
        </div>
      )}

      {/* Server Upload Success Feedback */}
      {uploadSuccess && (
        <div className="mt-4 p-4 rounded-lg bg-[var(--emerald-50)] border border-[var(--emerald-200)] text-[var(--emerald-900)] flex items-start gap-3 text-xs sm:text-sm" role="status">
          <CheckCircle2 className="w-5 h-5 text-[var(--emerald-600)] shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-bold">Ingestion Successful</span>
              <span className="font-mono text-xs px-2 py-0.5 rounded bg-white/80 border border-[var(--emerald-300)] text-[var(--emerald-800)]">
                {uploadSuccess.job_code}
              </span>
            </div>
            <p className="mt-1 text-xs text-[var(--emerald-800)]">
              Processed {uploadSuccess.records_imported} of {uploadSuccess.total_records} records with status <span className="font-semibold">{uploadSuccess.status}</span>.
              {uploadSuccess.quality_score !== null && ` Quality score: ${uploadSuccess.quality_score.toFixed(1)}%.`}
            </p>
          </div>
        </div>
      )}

      {/* Upload Action Button */}
      {canUpload && selectedFile && (
        <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-[var(--border-subtle)]">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClearSelection}
            disabled={isUploading}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="md"
            onClick={handleUploadSubmit}
            isLoading={isUploading}
            leftIcon={<UploadCloud className="w-4 h-4" />}
          >
            {isUploading ? 'Ingesting HMIS Data...' : 'Begin Ingestion'}
          </Button>
        </div>
      )}
    </div>
  );
};
