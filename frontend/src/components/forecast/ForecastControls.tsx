import React, { useState } from 'react';
import { Search, Filter, Calendar, ArrowLeft, Building } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { Facility, Indicator } from '../../api/types';

interface ForecastControlsProps {
  facilities: Facility[];
  indicators: Indicator[];
  selectedFacilityId: string;
  onFacilityChange: (id: string) => void;
  selectedIndicatorCode: string;
  onIndicatorChange: (code: string) => void;
  horizon: number;
  onHorizonChange: (h: number) => void;
  isLoading?: boolean;
}

export const ForecastControls: React.FC<ForecastControlsProps> = ({
  facilities = [],
  indicators = [],
  selectedFacilityId,
  onFacilityChange,
  selectedIndicatorCode,
  onIndicatorChange,
  horizon,
  onHorizonChange,
  isLoading = false,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedState, setSelectedState] = useState('');

  const safeFacilities = Array.isArray(facilities) ? facilities : [];
  const safeIndicators = Array.isArray(indicators) ? indicators : [];

  // Extract unique states for filtering
  const statesList = Array.from(new Set(safeFacilities.map((f) => f.state).filter(Boolean))).sort();

  // Filter facilities by state and search term
  const filteredFacilities = safeFacilities.filter((fac) => {
    const matchSearch =
      !searchTerm ||
      fac.facility_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (fac.facility_code && fac.facility_code.toLowerCase().includes(searchTerm.toLowerCase())) ||
      fac.district.toLowerCase().includes(searchTerm.toLowerCase());
    const matchState = !selectedState || fac.state === selectedState;
    return matchSearch && matchState;
  });

  const selectedFacility = safeFacilities.find((f) => f.id === selectedFacilityId || f.facility_code === selectedFacilityId);

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-5 shadow-xs mb-8 space-y-4">
      {/* Top Header & Back link if facility preselected */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4">
        <div className="flex items-center gap-2 text-sm font-bold text-[var(--text-primary)]">
          <Filter className="w-4 h-4 text-[var(--purple-600)]" />
          <span>Forecast Model Parameters</span>
        </div>

        {selectedFacilityId && (
          <Link
            to={`/facilities/${selectedFacilityId}`}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--teal-700)] hover:text-[var(--teal-800)] hover:underline"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Facility Profile ({selectedFacility?.facility_name || selectedFacilityId})</span>
          </Link>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
        {/* Facility Selector */}
        <div className="md:col-span-6 space-y-1.5">
          <label htmlFor="facility-select" className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center justify-between">
            <span className="flex items-center gap-1">
              <Building className="w-3.5 h-3.5 text-[var(--teal-600)]" />
              Target Health Facility
            </span>
            {safeFacilities.length > 0 && <span className="text-[10px] font-normal text-[var(--text-muted)]">{filteredFacilities.length} available</span>}
          </label>

          <div className="flex flex-col sm:flex-row gap-2">
            {/* Optional State Pre-filter */}
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              className="bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-2.5 py-2 text-xs text-[var(--text-primary)] font-medium focus-ring cursor-pointer max-w-full sm:max-w-[130px]"
              aria-label="Filter facilities by state"
            >
              <option value="">All States</option>
              {statesList.map((st) => (
                <option key={st} value={st}>
                  {st}
                </option>
              ))}
            </select>

            {/* Quick Search Filter */}
            <div className="relative flex-grow min-w-[140px]">
              <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Filter by facility or district..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl pl-8 pr-3 py-1.5 text-xs text-[var(--text-primary)] font-medium focus-ring"
                aria-label="Search facilities by name or district"
              />
            </div>

            <div className="relative flex-grow">
              <select
                id="facility-select"
                value={selectedFacilityId}
                onChange={(e) => onFacilityChange(e.target.value)}
                className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3 py-2 text-xs text-[var(--text-primary)] font-bold focus-ring cursor-pointer pr-8"
                aria-label="Select facility for forecasting"
              >
                <option value="">-- Select a Health Facility --</option>
                {filteredFacilities.map((fac) => (
                  <option key={fac.id} value={fac.id}>
                    {fac.facility_name} ({fac.facility_type} • {fac.district}, {fac.state})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Indicator Selector */}
        <div className="md:col-span-3 space-y-1.5">
          <label htmlFor="indicator-select" className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">
            Health Indicator
          </label>
          <select
            id="indicator-select"
            value={selectedIndicatorCode}
            onChange={(e) => onIndicatorChange(e.target.value)}
            className="w-full bg-[var(--bg-surface-subtle)] border border-[var(--border-default)] rounded-xl px-3 py-2 text-xs text-[var(--text-primary)] font-bold focus-ring cursor-pointer"
            aria-label="Select healthcare indicator for forecasting"
          >
            {safeIndicators.length === 0 && <option value="opd_attendance">OPD Attendance (opd_attendance)</option>}
            {safeIndicators.map((ind) => (
              <option key={ind.code} value={ind.code}>
                {ind.name} ({ind.code})
              </option>
            ))}
          </select>
        </div>

        {/* Forecast Horizon Selector Buttons */}
        <div className="md:col-span-3 space-y-1.5">
          <label className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1">
            <Calendar className="w-3.5 h-3.5 text-[var(--purple-600)]" />
            Forecast Horizon
          </label>

          <div className="inline-flex rounded-xl border border-[var(--border-subtle)] p-1 bg-[var(--bg-surface-subtle)] w-full">
            {[3, 6, 12].map((h) => (
              <button
                key={h}
                onClick={() => onHorizonChange(h)}
                disabled={isLoading}
                className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all cursor-pointer focus-ring text-center ${
                  horizon === h
                    ? 'bg-[var(--purple-600)] text-white shadow-xs'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)]'
                } ${isLoading ? 'opacity-60 cursor-not-allowed' : ''}`}
                aria-label={`Select ${h} months forecast horizon`}
              >
                {h}M
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
