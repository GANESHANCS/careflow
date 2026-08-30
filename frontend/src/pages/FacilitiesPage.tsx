import React, { useEffect, useState, useMemo } from 'react';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { EmptyState } from '../components/feedback/EmptyState';
import { api } from '../api/client';
import type { Facility, FacilityListResponse } from '../api/types';
import { FacilityFilters } from '../components/facilities/FacilityFilters';
import { FacilityListTable } from '../components/facilities/FacilityListTable';

export const FacilitiesPage: React.FC = () => {
  const [facilities, setFacilities] = useState<Facility[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedState, setSelectedState] = useState<string>('');
  const [selectedDistrict, setSelectedDistrict] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');

  const fetchFacilities = () => {
    setLoading(true);
    setError(null);

    const params = {
      state: selectedState || undefined,
      district: selectedDistrict || undefined,
      facility_type: selectedType || undefined,
      limit: 100,
    };

    api.getFacilities(params)
      .then((res: FacilityListResponse | Facility[]) => {
        if (Array.isArray(res)) {
          setFacilities(res);
        } else if (res && Array.isArray(res.items)) {
          setFacilities(res.items);
        } else {
          setFacilities([]);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to retrieve facilities list.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchFacilities();
  }, [selectedState, selectedDistrict, selectedType]);

  // Client-side text search on fetched list
  const filteredFacilities = useMemo(() => {
    return facilities.filter((fac) => {
      const query = searchQuery.toLowerCase();
      const nameMatch = (fac.facility_name || '').toLowerCase().includes(query);
      const codeMatch = (fac.facility_code || fac.id || '').toLowerCase().includes(query);
      const distMatch = (fac.district || '').toLowerCase().includes(query);
      return nameMatch || codeMatch || distMatch;
    });
  }, [facilities, searchQuery]);

  // Derive dynamic filter lists from actual data
  const statesList = useMemo(() => {
    return Array.from(new Set(facilities.map((f) => f.state).filter(Boolean))).sort();
  }, [facilities]);

  const districtsList = useMemo(() => {
    return Array.from(new Set(facilities.map((f) => f.district).filter(Boolean))).sort();
  }, [facilities]);

  const typesList = useMemo(() => {
    return Array.from(new Set(facilities.map((f) => f.facility_type).filter(Boolean))).sort();
  }, [facilities]);

  const handleReset = () => {
    setSearchQuery('');
    setSelectedState('');
    setSelectedDistrict('');
    setSelectedType('');
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Editorial Header */}
      <ScrollReveal>
        <header className="border-b border-[var(--border-subtle)] pb-6 mb-2">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-widest text-[var(--teal-700)] mb-2">
            <span className="w-2 h-2 rounded-full bg-[var(--teal-500)] animate-pulse" />
            <span>CAREFLOW</span>
            <span className="text-[var(--text-subtle)]">/</span>
            <span>FACILITIES</span>
          </div>

          <h1 className="font-display font-extrabold text-3xl sm:text-4xl lg:text-5xl text-[var(--text-primary)] tracking-tight leading-[1.15]">
            Facility Intelligence Directory
          </h1>

          <p className="mt-2 text-sm sm:text-base text-[var(--text-secondary)] max-w-2xl font-normal leading-relaxed">
            Search, filter, and inspect operational telemetry, monthly reporting completeness, and predictive readiness across healthcare facilities.
          </p>
        </header>
      </ScrollReveal>

      {/* Filter Controls Bar */}
      <ScrollReveal delay={0.05}>
        <FacilityFilters
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedState={selectedState}
          onStateChange={setSelectedState}
          selectedDistrict={selectedDistrict}
          onDistrictChange={setSelectedDistrict}
          selectedType={selectedType}
          onTypeChange={setSelectedType}
          onReset={handleReset}
          statesList={statesList}
          districtsList={districtsList}
          typesList={typesList}
        />
      </ScrollReveal>

      {/* Content Section */}
      <ScrollReveal delay={0.1}>
        {loading ? (
          <LoadingState type="table" />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchFacilities} />
        ) : filteredFacilities.length === 0 ? (
          <EmptyState
            title={facilities.length > 0 ? 'NO MATCHING FACILITIES FOUND' : 'NO VERIFIED HMIS FACILITIES LOADED'}
            description={
              facilities.length > 0
                ? 'No healthcare facilities matched your active search query or filter parameters.'
                : 'Healthcare facility observations have not been loaded into the database yet.'
            }
            actionText={facilities.length > 0 ? 'Reset Search Filters' : undefined}
            onAction={facilities.length > 0 ? handleReset : undefined}
            icon="search"
          />
        ) : (
          <FacilityListTable facilities={filteredFacilities} />
        )}
      </ScrollReveal>
    </div>
  );
};
