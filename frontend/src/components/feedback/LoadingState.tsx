import React from 'react';
import { clsx } from 'clsx';

export interface LoadingStateProps {
  type?: 'card' | 'table' | 'chart' | 'detail';
  count?: number;
  className?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  type = 'card',
  count = 3,
  className,
}) => {
  if (type === 'chart') {
    return (
      <div className={clsx('w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-xl p-6 animate-pulse', className)}>
        <div className="flex items-center justify-between mb-6">
          <div className="h-5 bg-[var(--bg-surface-hover)] rounded-md w-48" />
          <div className="h-4 bg-[var(--bg-surface-hover)] rounded-md w-24" />
        </div>
        <div className="h-56 bg-[var(--bg-surface-hover)] rounded-lg w-full flex items-end justify-between p-4 gap-3">
          {[40, 65, 30, 85, 55, 90, 70, 45, 60, 80, 50, 75].map((h, i) => (
            <div key={i} style={{ height: `${h}%` }} className="flex-1 bg-[var(--border-subtle)] rounded-t-sm" />
          ))}
        </div>
      </div>
    );
  }

  if (type === 'table') {
    return (
      <div className={clsx('w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden animate-pulse', className)}>
        <div className="h-12 bg-[var(--bg-surface-subtle)] border-b border-[var(--border-subtle)] px-4 flex items-center justify-between">
          <div className="h-4 bg-[var(--bg-surface-hover)] rounded w-32" />
          <div className="h-4 bg-[var(--bg-surface-hover)] rounded w-20" />
        </div>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-14 border-b border-[var(--border-subtle)] px-4 flex items-center gap-4">
            <div className="h-4 bg-[var(--bg-surface-subtle)] rounded flex-1" />
            <div className="h-4 bg-[var(--bg-surface-subtle)] rounded w-24" />
            <div className="h-4 bg-[var(--bg-surface-subtle)] rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={clsx('grid grid-cols-1 md:grid-cols-3 gap-4', className)}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 animate-pulse">
          <div className="h-4 bg-[var(--bg-surface-subtle)] rounded w-2/3 mb-4" />
          <div className="h-8 bg-[var(--bg-surface-subtle)] rounded w-1/2 mb-3" />
          <div className="h-3 bg-[var(--bg-surface-subtle)] rounded w-full" />
        </div>
      ))}
    </div>
  );
};
