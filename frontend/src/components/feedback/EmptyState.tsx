import React from 'react';
import { Database, FileQuestion, RefreshCw } from 'lucide-react';
import { Button } from '../buttons/Button';

export interface EmptyStateProps {
  title?: string;
  description?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: 'database' | 'search';
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'NO HMIS OBSERVATIONS AVAILABLE',
  description = 'No operational government healthcare observations are currently loaded in the database for this target selection.',
  actionText,
  onAction,
  icon = 'database',
}) => {
  return (
    <div className="w-full bg-[var(--bg-surface-subtle)] border border-dashed border-[var(--border-default)] rounded-xl p-8 sm:p-12 text-center flex flex-col items-center justify-center my-4">
      <div className="w-12 h-12 rounded-full bg-[var(--teal-50)] text-[var(--teal-600)] flex items-center justify-center mb-4 shadow-xs border border-[var(--teal-100)]">
        {icon === 'database' ? <Database className="w-6 h-6" /> : <FileQuestion className="w-6 h-6" />}
      </div>

      <h3 className="font-display font-bold text-base sm:text-lg text-[var(--text-primary)] tracking-wide mb-2">
        {title}
      </h3>

      <p className="text-sm text-[var(--text-secondary)] max-w-md mx-auto leading-relaxed mb-6">
        {description}
      </p>

      {actionText && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
          {actionText}
        </Button>
      )}

      <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] text-xs text-[var(--text-muted)] flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-[var(--amber-500)]" />
        <span>Awaiting government HMIS file ingestion under <code className="bg-[var(--bg-surface)] px-1.5 py-0.5 rounded font-mono text-[var(--text-primary)]">data/raw/</code></span>
      </div>
    </div>
  );
};
