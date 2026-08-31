import React from 'react';
import { Calendar, Globe2, Layers } from 'lucide-react';

interface RegionalHeaderProps {
  reportingMonth?: string | null;
  level: 'state' | 'district';
  totalRegions: number;
}

export const RegionalHeader: React.FC<RegionalHeaderProps> = ({
  reportingMonth,
  level,
  totalRegions,
}) => {
  return (
    <header className="border-b border-[var(--border-subtle)] pb-6 mb-8">
      {/* Breadcrumb & Context */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-[var(--teal-700)]">
          <Globe2 className="w-4 h-4 text-[var(--teal-600)]" />
          <span>CAREFLOW</span>
          <span className="text-[var(--text-subtle)]">/</span>
          <span>REGIONAL INTELLIGENCE</span>
        </div>

        {reportingMonth && (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] text-xs text-[var(--text-secondary)] font-medium">
            <Calendar className="w-3.5 h-3.5 text-[var(--teal-600)]" />
            <span>Reporting Period: <strong className="font-mono font-bold text-[var(--text-primary)]">{reportingMonth}</strong></span>
          </div>
        )}
      </div>

      {/* Main Title Row */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-5xl text-[var(--text-primary)] tracking-tight leading-[1.15]">
            Geographic Intelligence & Spatial Comparison
          </h1>
          <p className="mt-2 text-sm sm:text-base text-[var(--text-secondary)] max-w-3xl font-normal leading-relaxed">
            Analyze healthcare service demand movement across National, State, and District jurisdictions to identify regional utilization shifts and reporting completeness.
          </p>
        </div>

        <div className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[var(--teal-50)] text-[var(--teal-700)] border border-[var(--teal-100)] text-xs font-bold shrink-0 self-start md:self-auto">
          <Layers className="w-4 h-4 text-[var(--teal-600)]" />
          <span>Analyzing {totalRegions} {level === 'state' ? 'State Jurisdictions' : 'District Jurisdictions'}</span>
        </div>
      </div>
    </header>
  );
};
