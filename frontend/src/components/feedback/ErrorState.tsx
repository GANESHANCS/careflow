import React, { useState } from 'react';
import { AlertCircle, RefreshCw, Copy, Check } from 'lucide-react';
import { Button } from '../buttons/Button';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  requestId?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  message = 'A connection error occurred while communicating with the CAREFlow backend API. Please verify the backend service is active.',
  requestId,
  onRetry,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopyRequestId = () => {
    if (requestId) {
      navigator.clipboard.writeText(requestId).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  };

  return (
    <div className="w-full bg-[var(--coral-50)] border border-[var(--coral-100)] rounded-xl p-6 sm:p-8 text-center flex flex-col items-center justify-center my-4">
      <div className="w-10 h-10 rounded-full bg-white text-[var(--coral-600)] flex items-center justify-center mb-3 shadow-xs border border-[var(--coral-100)]">
        <AlertCircle className="w-5 h-5" />
      </div>

      <h4 className="font-display font-bold text-base text-[var(--coral-700)] mb-1">
        {title}
      </h4>

      <p className="text-xs sm:text-sm text-[var(--text-secondary)] max-w-lg mx-auto leading-relaxed mb-4">
        {message}
      </p>

      {requestId && (
        <div className="flex items-center gap-2 mb-5 px-3 py-1.5 bg-white/80 border border-[var(--coral-100)] rounded-lg text-xs font-mono text-[var(--text-secondary)] shadow-2xs">
          <span className="text-[var(--text-muted)]">Ref:</span>
          <span className="font-semibold text-[var(--text-primary)]">{requestId}</span>
          <button
            type="button"
            onClick={handleCopyRequestId}
            title="Copy Incident ID"
            aria-label="Copy Incident ID"
            className="ml-1 p-1 rounded hover:bg-[var(--coral-100)] text-[var(--coral-600)] transition-colors focus:outline-none"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      )}

      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
          Try Again
        </Button>
      )}
    </div>
  );
};
