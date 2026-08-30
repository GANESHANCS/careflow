import React from 'react';
import { LoadingState } from '../feedback/LoadingState';
import { EmptyState } from '../feedback/EmptyState';
import { ErrorState } from '../feedback/ErrorState';

export interface ChartContainerProps {
  title: string;
  subtitle?: string;
  badge?: string;
  status: 'loading' | 'empty' | 'error' | 'success';
  errorMessage?: string;
  onRetry?: () => void;
  action?: React.ReactNode;
  children: React.ReactNode;
}

export const ChartContainer: React.FC<ChartContainerProps> = ({
  title,
  subtitle,
  badge,
  status,
  errorMessage,
  onRetry,
  action,
  children,
}) => {
  return (
    <div className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 sm:p-6 shadow-sm hover:shadow-md transition-shadow duration-300">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-4 pb-3 border-b border-[var(--border-subtle)]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-display font-bold text-base text-[var(--text-primary)]">{title}</h3>
            {badge && (
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[var(--teal-50)] text-[var(--teal-700)] border border-[var(--teal-100)]">
                {badge}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-[var(--text-muted)] mt-0.5">{subtitle}</p>}
        </div>
        {action && <div>{action}</div>}
      </div>

      {status === 'loading' && <LoadingState type="chart" />}
      {status === 'error' && <ErrorState message={errorMessage} onRetry={onRetry} />}
      {status === 'empty' && <EmptyState title="NO DATA FOR CHART" description="No observational time-series points exist for this selected metric." />}
      {status === 'success' && children}
    </div>
  );
};
