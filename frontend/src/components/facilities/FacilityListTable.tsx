import React from 'react';
import { NavLink } from 'react-router-dom';
import { ArrowRight, Building2, MapPin, Activity } from 'lucide-react';
import type { Facility } from '../../api/types';

interface FacilityListTableProps {
  facilities: Facility[];
}

export const FacilityListTable: React.FC<FacilityListTableProps> = ({ facilities }) => {
  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-xs overflow-hidden">
      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-[var(--border-subtle)] bg-[var(--bg-surface-subtle)] text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)]">
              <th scope="col" className="py-3.5 px-6">Facility / Identity</th>
              <th scope="col" className="py-3.5 px-4">Location</th>
              <th scope="col" className="py-3.5 px-4">Facility Type</th>
              <th scope="col" className="py-3.5 px-4">Telemetry Status</th>
              <th scope="col" className="py-3.5 px-6 text-right">Operational Profile</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-subtle)] text-xs text-[var(--text-secondary)]">
            {facilities.map((fac) => (
              <tr
                key={fac.id}
                className="group hover:bg-[var(--bg-surface-hover)] transition-all duration-150 relative cursor-pointer"
              >
                {/* Facility Identity Column */}
                <td className="py-4 px-6 font-medium text-[var(--text-primary)]">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-[var(--teal-50)] text-[var(--teal-700)] border border-[var(--teal-100)] flex items-center justify-center shrink-0">
                      <Building2 className="w-4 h-4" />
                    </div>
                    <div>
                      <NavLink
                        to={`/facilities/${fac.id}`}
                        className="font-display font-bold text-sm text-[var(--text-primary)] group-hover:text-[var(--teal-700)] transition-colors focus-ring rounded"
                      >
                        {fac.facility_name}
                      </NavLink>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] font-mono text-[var(--text-muted)] bg-[var(--bg-surface-subtle)] px-1.5 py-0.5 rounded border border-[var(--border-subtle)]">
                          {fac.facility_code || fac.id}
                        </span>
                        {fac.sub_district && (
                          <span className="text-[10px] text-[var(--text-muted)]">
                            Sub-district: {fac.sub_district}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </td>

                {/* Location Column */}
                <td className="py-4 px-4">
                  <div className="flex items-center gap-1.5 text-xs text-[var(--text-primary)] font-medium">
                    <MapPin className="w-3.5 h-3.5 text-[var(--text-muted)] shrink-0" />
                    <span>{fac.district}, <strong className="font-semibold text-[var(--text-secondary)]">{fac.state}</strong></span>
                  </div>
                </td>

                {/* Facility Type Column */}
                <td className="py-4 px-4">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[var(--teal-50)] text-[var(--teal-700)] border border-[var(--teal-100)]">
                    {fac.facility_type}
                  </span>
                </td>

                {/* Telemetry Column */}
                <td className="py-4 px-4">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-[var(--green-50)] text-[var(--green-700)] border border-[var(--green-100)]">
                    <span className="w-1.5 h-1.5 rounded-full bg-[var(--green-500)] animate-pulse" />
                    <span>Active Telemetry</span>
                  </span>
                </td>

                {/* Action Link Column */}
                <td className="py-4 px-6 text-right">
                  <NavLink
                    to={`/facilities/${fac.id}`}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--teal-700)] group-hover:text-[var(--teal-600)] transition-colors focus-ring px-3 py-1.5 rounded-lg group-hover:bg-[var(--teal-50)]"
                    aria-label={`Inspect profile for ${fac.facility_name}`}
                  >
                    <span>Inspect Profile</span>
                    <ArrowRight className="w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-1" />
                  </NavLink>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Stacked Card View */}
      <div className="block md:hidden divide-y divide-[var(--border-subtle)]">
        {facilities.map((fac) => (
          <div key={fac.id} className="p-4 space-y-3 hover:bg-[var(--bg-surface-hover)] transition-colors">
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-[var(--teal-50)] text-[var(--teal-700)] border border-[var(--teal-100)] mb-1">
                  {fac.facility_type}
                </span>
                <NavLink
                  to={`/facilities/${fac.id}`}
                  className="font-display font-bold text-base text-[var(--text-primary)] block hover:text-[var(--teal-700)]"
                >
                  {fac.facility_name}
                </NavLink>
                <div className="text-xs text-[var(--text-secondary)] mt-0.5">
                  {fac.district}, {fac.state}
                </div>
              </div>

              <span className="text-[10px] font-mono text-[var(--text-muted)] bg-[var(--bg-surface-subtle)] px-2 py-0.5 rounded border border-[var(--border-subtle)] shrink-0">
                {fac.facility_code || fac.id}
              </span>
            </div>

            <div className="flex items-center justify-between pt-2 text-xs border-t border-[var(--border-subtle)]">
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[var(--green-700)]">
                <Activity className="w-3 h-3 text-[var(--green-600)]" />
                Active Telemetry
              </span>
              <NavLink
                to={`/facilities/${fac.id}`}
                className="inline-flex items-center gap-1 font-semibold text-[var(--teal-700)] text-xs"
              >
                <span>Inspect Profile</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </NavLink>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
