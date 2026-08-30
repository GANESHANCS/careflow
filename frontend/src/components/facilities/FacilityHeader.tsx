import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowLeft, Building2, MapPin, Hash, ShieldCheck } from 'lucide-react';
import type { Facility } from '../../api/types';

interface FacilityHeaderProps {
  facility: Facility;
  reportingCompletenessPct?: number | null;
}

export const FacilityHeader: React.FC<FacilityHeaderProps> = ({
  facility,
  reportingCompletenessPct,
}) => {
  return (
    <header className="border-b border-[var(--border-subtle)] pb-6 mb-8">
      {/* Navigation & Breadcrumb */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <NavLink
          to="/facilities"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--teal-700)] hover:text-[var(--teal-600)] transition-colors focus-ring px-2.5 py-1 rounded-lg hover:bg-[var(--teal-50)]"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Facilities Directory</span>
        </NavLink>

        <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-widest text-[var(--teal-700)]">
          <span>CAREFLOW</span>
          <span className="text-[var(--text-subtle)]">/</span>
          <span>FACILITIES</span>
          <span className="text-[var(--text-subtle)]">/</span>
          <span className="text-[var(--text-primary)] truncate max-w-[150px] sm:max-w-xs font-bold">
            {facility.facility_name}
          </span>
        </div>
      </div>

      {/* Main Title Row */}
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
        <div>
          <div className="flex flex-wrap items-center gap-2.5 mb-2">
            <span className="inline-flex items-center px-3 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-[var(--teal-50)] text-[var(--teal-700)] border border-[var(--teal-100)]">
              <Building2 className="w-3 h-3 mr-1" />
              {facility.facility_type}
            </span>
            <span className="inline-flex items-center gap-1 text-xs font-mono text-[var(--text-muted)] bg-[var(--bg-surface-subtle)] px-2.5 py-0.5 rounded-md border border-[var(--border-subtle)]">
              <Hash className="w-3 h-3 text-[var(--text-muted)]" />
              <span>{facility.facility_code || facility.id}</span>
            </span>
          </div>

          <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-5xl text-[var(--text-primary)] tracking-tight leading-[1.15]">
            {facility.facility_name}
          </h1>

          <div className="flex flex-wrap items-center gap-3 mt-3 text-xs sm:text-sm text-[var(--text-secondary)] font-medium">
            <span className="flex items-center gap-1 text-[var(--text-primary)] font-semibold">
              <MapPin className="w-4 h-4 text-[var(--teal-600)] shrink-0" />
              <span>{facility.district}, {facility.state}</span>
            </span>
            {facility.sub_district && (
              <>
                <span className="text-[var(--text-subtle)]">•</span>
                <span>Sub-district: <strong>{facility.sub_district}</strong></span>
              </>
            )}
          </div>
        </div>

        {/* Reporting Quality Badge */}
        {typeof reportingCompletenessPct === 'number' && (
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] shadow-2xs self-start md:self-auto">
            <ShieldCheck className="w-4 h-4 text-[var(--teal-600)]" />
            <div>
              <div className="text-[10px] font-bold uppercase text-[var(--text-muted)] tracking-wider">
                Reporting Completeness
              </div>
              <div className="text-sm font-extrabold font-display text-[var(--text-primary)]">
                {reportingCompletenessPct.toFixed(1)}%
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
