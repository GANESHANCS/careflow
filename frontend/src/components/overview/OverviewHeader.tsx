import React from 'react';
import { ShieldCheck, Database, Calendar } from 'lucide-react';

interface OverviewHeaderProps {
  latestPeriod: string | null;
  totalFacilities: number;
  reportingCompletenessPct?: number;
  onMethodologyClick?: () => void;
}

export const OverviewHeader: React.FC<OverviewHeaderProps> = ({
  latestPeriod,
  totalFacilities,
  onMethodologyClick,
}) => {
  const isDataPresent = latestPeriod !== null && totalFacilities > 0;

  return (
    <header className="border-b border-[var(--border-subtle)] pb-6 mb-8">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          {/* Breadcrumb Label */}
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-[var(--teal-700)] mb-2">
            <span className="w-2 h-2 rounded-full bg-[var(--teal-500)] animate-pulse" />
            <span>CAREFLOW</span>
            <span className="text-[var(--text-subtle)]">/</span>
            <span>OVERVIEW</span>
          </div>

          {/* Editorial Title */}
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-5xl text-[var(--text-primary)] tracking-tight leading-[1.15]">
            Understand what is happening <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-[var(--teal-700)] to-[var(--blue-600)]">
              across the health system.
            </span>
          </h1>

          <p className="mt-2 text-sm sm:text-base text-[var(--text-secondary)] max-w-2xl font-normal leading-relaxed">
            Consolidated operational attendance indicators, regional utilization signals, time-series trends, and HMIS reporting audit controls.
          </p>
        </div>

        {/* Right Action / System Status Badge */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] text-xs font-medium text-[var(--text-secondary)] shadow-2xs">
            <Database className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            {isDataPresent ? (
              <span className="flex items-center gap-1.5">
                <span className="font-semibold text-[var(--text-primary)]">SYSTEM ONLINE</span>
                <span className="text-[var(--text-subtle)]">•</span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-[var(--text-muted)]" />
                  <span>Latest Period: <strong>{latestPeriod}</strong></span>
                </span>
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-[var(--amber-700)]">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--amber-500)]" />
                <span className="font-semibold">AWAITING HMIS INGESTION</span>
              </span>
            )}
          </div>

          {onMethodologyClick && (
            <button
              onClick={onMethodologyClick}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-[var(--teal-700)] hover:text-[var(--teal-600)] transition-colors focus-ring rounded-md"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Governance & Audit</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
