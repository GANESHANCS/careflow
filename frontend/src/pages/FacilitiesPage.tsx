import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import { InteractiveHeading } from '../components/typography/InteractiveHeading';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { Button } from '../components/buttons/Button';
import { EmptyState } from '../components/feedback/EmptyState';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { api } from '../api/client';
import type { Facility } from '../api/types';
import { Search, ArrowRight, Filter } from 'lucide-react';

export const FacilitiesPage: React.FC = () => {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchFacilities = () => {
    setLoading(true);
    setError(null);
    api.getFacilities({ limit: 50 })
      .then((data) => {
        setFacilities(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Failed to retrieve facilities list.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchFacilities();
  }, []);

  const safeFacilities = Array.isArray(facilities) ? facilities : [];
  const filteredFacilities = safeFacilities.filter(f =>
    (f?.facility_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (f?.district || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (f?.facility_type || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8">
      <ScrollReveal>
        <InteractiveHeading
          title="Facility Intelligence Directory"
          subtitle="Explore District Hospitals, CHCs, PHCs, and Sub-Centers tracked under CAREFlow"
          badge="Facilities"
          badgeColor="blue"
        />
      </ScrollReveal>

      {/* Filter / Search Bar */}
      <ScrollReveal delay={0.1}>
        <div className="flex flex-wrap items-center justify-between gap-4 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 shadow-xs">
          <div className="flex items-center relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3 pointer-events-none" />
            <input
              type="text"
              placeholder="Search by facility name, district, or type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 text-sm bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-lg text-[var(--text-primary)] focus:border-[var(--blue-600)] transition-colors focus-ring"
            />
          </div>

          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" leftIcon={<Filter className="w-3.5 h-3.5" />}>
              Filter Type
            </Button>
          </div>
        </div>
      </ScrollReveal>

      {/* Content Section */}
      <ScrollReveal delay={0.2}>
        {loading ? (
          <LoadingState type="table" />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchFacilities} />
        ) : filteredFacilities.length === 0 ? (
          <EmptyState
            title="NO FACILITIES FOUND"
            description="No healthcare facilities matched your current search parameters or database query."
            actionText="Clear Search"
            onAction={() => setSearchQuery('')}
            icon="search"
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredFacilities.map((facility) => (
              <div
                key={facility.id}
                className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs hover:shadow-md hover:border-[var(--blue-500)] transition-all duration-200 group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-[var(--blue-50)] text-[var(--blue-700)] border border-[var(--blue-100)] uppercase">
                      {facility.facility_type}
                    </span>
                    <span className="text-xs text-[var(--text-muted)] font-mono">
                      {facility.facility_code || facility.id}
                    </span>
                  </div>

                  <h3 className="font-display font-bold text-base text-[var(--text-primary)] group-hover:text-[var(--blue-600)] transition-colors mb-1">
                    {facility.facility_name}
                  </h3>

                  <p className="text-xs text-[var(--text-secondary)] mb-4">
                    {facility.district}, {facility.state}
                  </p>
                </div>

                <div className="pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs text-[var(--text-muted)]">
                  <span>View Details</span>
                  <NavLink
                    to={`/facilities/${facility.id}`}
                    className="p-1.5 rounded-lg bg-[var(--bg-surface-subtle)] group-hover:bg-[var(--blue-600)] group-hover:text-white transition-colors focus-ring"
                    aria-label={`View details for ${facility.facility_name}`}
                  >
                    <ArrowRight className="w-3.5 h-3.5" />
                  </NavLink>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollReveal>
    </div>
  );
};
