import React, { useState, useEffect } from 'react';
import { useParams, NavLink } from 'react-router-dom';
import { InteractiveHeading } from '../components/typography/InteractiveHeading';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { EmptyState } from '../components/feedback/EmptyState';
import { api } from '../api/client';
import type { Facility, FacilityAnalyticsResponse } from '../api/types';
import { ArrowLeft, Building2, MapPin, ShieldCheck } from 'lucide-react';

export const FacilityDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [facility, setFacility] = useState<Facility | null>(null);
  const [analytics, setAnalytics] = useState<FacilityAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    setError(null);

    Promise.all([
      api.getFacilityById(id).catch(() => null),
      api.getFacilityAnalytics(id).catch(() => null)
    ]).then(([facData, analyticsData]) => {
      if (facData) setFacility(facData);
      if (analyticsData) setAnalytics(analyticsData);
      if (!facData && !analyticsData) {
        setError(`Facility with ID '${id}' was not found in the database.`);
      }
      setLoading(false);
    });
  }, [id]);

  if (loading) return <LoadingState type="detail" />;
  if (error || !facility) return <ErrorState title="Facility Not Found" message={error || undefined} />;

  return (
    <div className="space-y-8">
      <ScrollReveal>
        <div className="mb-4">
          <NavLink to="/facilities" className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--teal-600)] hover:text-[var(--teal-700)] transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Facilities Directory</span>
          </NavLink>
        </div>

        <InteractiveHeading
          title={facility.facility_name}
          subtitle={`${facility.facility_type} located in ${facility.district}, ${facility.state}`}
          badge={facility.facility_type}
          badgeColor="blue"
        />
      </ScrollReveal>

      {/* Metadata Panel */}
      <ScrollReveal delay={0.1}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-[var(--blue-50)] text-[var(--blue-600)]">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-[var(--text-muted)]">District / State</div>
              <div className="text-sm font-bold text-[var(--text-primary)]">{facility.district}, {facility.state}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-[var(--teal-50)] text-[var(--teal-600)]">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-[var(--text-muted)]">Facility Code</div>
              <div className="text-sm font-bold text-[var(--text-primary)] font-mono">{facility.facility_code || facility.id}</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-[var(--purple-50)] text-[var(--purple-600)]">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs text-[var(--text-muted)] font-medium">Reporting Completeness</div>
              <div className="text-sm font-bold text-[var(--text-primary)]">
                {analytics && typeof analytics.reporting_completeness_pct === 'number' ? `${analytics.reporting_completeness_pct}%` : 'N/A'}
              </div>
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Observation Trends or Empty State */}
      <ScrollReveal delay={0.2}>
        <EmptyState
          title="NO OBSERVATIONS LOADED FOR THIS FACILITY"
          description="Facility metadata is registered. Ingest HMIS Excel files to populate historical monthly OPD attendance, IPD admissions, and institutional delivery trends."
        />
      </ScrollReveal>
    </div>
  );
};
