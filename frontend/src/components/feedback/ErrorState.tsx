import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '../buttons/Button';

export interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  message = 'A connection error occurred while communicating with the CAREFlow backend API. Please verify the backend service is active.',
  onRetry,
}) => {
  return (
    <div className="w-full bg-[var(--coral-50)] border border-[var(--coral-100)] rounded-xl p-6 sm:p-8 text-center flex flex-col items-center justify-center my-4">
      <div className="w-10 h-10 rounded-full bg-white text-[var(--coral-600)] flex items-center justify-center mb-3 shadow-xs border border-[var(--coral-100)]">
        <AlertCircle className="w-5 h-5" />
      </div>

      <h4 className="font-display font-bold text-base text-[var(--coral-700)] mb-1">
        {title}
      </h4>

      <p className="text-xs sm:text-sm text-[var(--text-secondary)] max-w-lg mx-auto leading-relaxed mb-5">
        {message}
      </p>

      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
          Try Again
        </Button>
      )}
    </div>
  );
};
