import React from 'react';
import { Building2, ArrowRight, AlertTriangle, CheckCircle2, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import type { IncompleteFacilityItem } from '../../api/types';

interface IncompleteFacilitiesProps {
  facilities: IncompleteFacilityItem[];
}

export const IncompleteFacilities: React.FC<IncompleteFacilitiesProps> = ({ facilities = [] }) => {
  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs mb-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[var(--border-subtle)] pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)] tracking-tight flex items-center gap-2 font-display">
            <Building2 className="w-5 h-5 text-[var(--amber-600)]" />
            Facilities with Incomplete Monthly Reporting Returns
          </h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Facilities failing 100% expected monthly returns during the audited evaluation window.
          </p>
        </div>

        <div className="px-3 py-1 rounded-xl bg-[var(--amber-50)] border border-[var(--amber-200)] text-xs font-bold text-[var(--amber-800)] self-start sm:self-auto font-mono">
          {facilities.length} Facility Flags
        </div>
      </div>

      {facilities.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] uppercase tracking-wider text-[10px] font-bold bg-[var(--bg-surface-subtle)]">
                <th className="py-3 px-4 rounded-l-xl">Facility Name</th>
                <th className="py-3 px-4">Administrative Region</th>
                <th className="py-3 px-4 text-center">Reported / Expected</th>
                <th className="py-3 px-4 text-center">Completeness %</th>
                <th className="py-3 px-4 text-right rounded-r-xl">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border-subtle)]">
              {facilities.map((fac) => (
                <tr key={fac.facility_id} className="hover:bg-[var(--amber-50)]/30 transition-colors">
                  <td className="py-3.5 px-4">
                    <span className="font-bold text-[var(--text-primary)] block">{fac.facility_name}</span>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">ID: {fac.facility_id}</span>
                  </td>

                  <td className="py-3.5 px-4 text-[var(--text-muted)] whitespace-nowrap">
                    <div className="flex items-center gap-1">
                      <MapPin className="w-3 h-3 text-[var(--teal-600)]" />
                      <span>{fac.district}, {fac.state}</span>
                    </div>
                  </td>

                  <td className="py-3.5 px-4 text-center font-mono font-bold text-[var(--text-primary)] whitespace-nowrap">
                    <span className="text-[var(--teal-700)]">{fac.reported_months}</span> /{' '}
                    <span className="text-[var(--text-muted)]">{fac.expected_months}</span> months
                  </td>

                  <td className="py-3.5 px-4 text-center whitespace-nowrap">
                    <div className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[var(--amber-100)] text-[var(--amber-900)] border border-[var(--amber-300)] font-mono font-bold text-[11px]">
                      <AlertTriangle className="w-3 h-3 text-[var(--amber-700)]" />
                      <span>{fac.completeness_pct.toFixed(1)}%</span>
                    </div>
                  </td>

                  <td className="py-3.5 px-4 text-right whitespace-nowrap">
                    <Link
                      to={`/facilities/${fac.facility_id}`}
                      className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-[var(--bg-surface-subtle)] hover:bg-[var(--purple-100)] border border-[var(--border-subtle)] hover:border-[var(--purple-300)] text-xs font-bold text-[var(--purple-800)] transition-all cursor-pointer focus-ring"
                      aria-label={`Inspect facility profile for ${fac.facility_name}`}
                    >
                      <span>Inspect Facility</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center py-10 bg-[var(--teal-50)] border border-[var(--teal-200)] rounded-2xl p-6">
          <CheckCircle2 className="w-8 h-8 text-[var(--teal-600)] mx-auto mb-2" />
          <h4 className="text-sm font-bold text-[var(--teal-950)]">100% Facility Reporting Completeness</h4>
          <p className="text-xs text-[var(--teal-800)] mt-1 max-w-md mx-auto">
            All registered facilities in the healthcare network submitted complete monthly returns across the audited timeframe.
          </p>
        </div>
      )}
    </div>
  );
};
