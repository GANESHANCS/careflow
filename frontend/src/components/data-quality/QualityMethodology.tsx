import React, { useState } from 'react';
import { ChevronDown, ChevronUp, BookOpen, ShieldCheck, Calculator } from 'lucide-react';

export const QualityMethodology: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const checks = [
    { num: 1, name: 'Missing Values Audit', severity: 'WARNING / ERROR', desc: 'Cell missingness percentage (>15% triggers ERROR).' },
    { num: 2, name: 'Duplicate Record Check', severity: 'WARNING / ERROR', desc: 'Composite key duplicates (facility_id + indicator + month).' },
    { num: 3, name: 'Invalid Reporting Dates', severity: 'ERROR', desc: 'Unparseable or malformed YYYY-MM period strings.' },
    { num: 4, name: 'Invalid Numeric Formatting', severity: 'ERROR', desc: 'Non-numeric string noise in count metric columns.' },
    { num: 5, name: 'Negative Count Inspection', severity: 'CRITICAL', desc: 'Impossible negative values (e.g. -50 admissions).' },
    { num: 6, name: 'Extreme Outlier Detection', severity: 'WARNING', desc: 'Outliers exceeding conservative 5x IQR distance.' },
    { num: 7, name: 'Missing Reporting Periods', severity: 'WARNING', desc: 'Temporal gaps in monthly facility timeseries.' },
    { num: 8, name: 'Facility ID Consistency', severity: 'INFO', desc: 'Facilities lacking official HMIS codes (composite hash assigned).' },
    { num: 9, name: 'Regional Name Alignment', severity: 'WARNING', desc: 'Unrecognized or inconsistent state/district names.' },
    { num: 10, name: 'Indicator Catalog Mapping', severity: 'WARNING', desc: 'Raw headers unmapped to standard HMIS catalog.' },
    { num: 11, name: 'Reporting Completeness Yield', severity: 'WARNING / ERROR', desc: 'Percentage of expected monthly reports present per facility.' },
    { num: 12, name: 'Temporal Continuity Audit', severity: 'WARNING', desc: 'Consecutive missing reporting months in facility series.' },
    { num: 13, name: 'Source File Integrity', severity: 'CRITICAL', desc: 'File corruption or 0-row empty dataset flags.' },
  ];

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs mb-8">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left cursor-pointer focus-ring rounded-2xl p-2 hover:bg-[var(--bg-surface-subtle)] transition-colors"
        aria-expanded={isOpen}
        aria-label="Toggle 13-point data quality methodology details"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-[var(--teal-50)] border border-[var(--teal-200)] flex items-center justify-center shrink-0">
            <BookOpen className="w-5 h-5 text-[var(--teal-600)]" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[var(--text-primary)] tracking-tight font-display">
              13-Point HMIS Quality Audit Framework & Scoring Formula
            </h3>
            <p className="text-xs text-[var(--text-muted)] mt-0.5">
              Click to inspect technical quality audit checks, sub-score weights, and data governance rules.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-bold text-[var(--teal-700)]">
          <span>{isOpen ? 'Collapse Methodology' : 'Expand Methodology'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="mt-6 border-t border-[var(--border-subtle)] pt-6 space-y-8 animate-fadeIn">
          {/* Mathematical Scoring Formula */}
          <div className="bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-2xl p-5 space-y-3">
            <div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-wider text-[var(--purple-700)]">
              <Calculator className="w-4 h-4 text-[var(--purple-600)]" />
              Weighted Quality Score Formula (0 – 100)
            </div>

            <div className="p-4 rounded-xl bg-white border border-[var(--border-subtle)] font-mono text-xs sm:text-sm text-gray-900 font-bold overflow-x-auto">
              Overall Quality Score = 0.30 × Completeness + 0.25 × Validity + 0.15 × Uniqueness + 0.15 × Consistency + 0.15 × Continuity
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 text-xs text-[var(--text-muted)] pt-2">
              <div>
                <strong className="text-[var(--text-primary)]">Completeness (30%):</strong> 100 − (% missing × 1.5)
              </div>
              <div>
                <strong className="text-[var(--text-primary)]">Validity (25%):</strong> 100 − (% invalid × 3.0 + % negative × 5.0)
              </div>
              <div>
                <strong className="text-[var(--text-primary)]">Uniqueness (15%):</strong> 100 − (% duplicates × 2.0)
              </div>
              <div>
                <strong className="text-[var(--text-primary)]">Consistency (15%):</strong> 100 − (% invalid dates × 3.0)
              </div>
              <div>
                <strong className="text-[var(--text-primary)]">Continuity (15%):</strong> 100 − (% outliers × 2.0)
              </div>
            </div>
          </div>

          {/* 13-Point Audit Checks Table */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-3 flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-[var(--teal-600)]" />
              13 Continuous Automated Pipeline Audit Checks
            </h4>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] uppercase tracking-wider text-[10px] font-bold bg-[var(--bg-surface-subtle)]">
                    <th className="py-2.5 px-3 rounded-l-xl">Check #</th>
                    <th className="py-2.5 px-3">Audit Check Name</th>
                    <th className="py-2.5 px-3">Severity Threshold</th>
                    <th className="py-2.5 px-3 rounded-r-xl">Governance Rule Description</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[var(--border-subtle)]">
                  {checks.map((chk) => (
                    <tr key={chk.num} className="hover:bg-[var(--bg-surface-subtle)] transition-colors">
                      <td className="py-2.5 px-3 font-mono font-bold text-[var(--teal-700)]">#{chk.num}</td>
                      <td className="py-2.5 px-3 font-bold text-[var(--text-primary)]">{chk.name}</td>
                      <td className="py-2.5 px-3 font-mono font-bold text-[10px] text-[var(--purple-700)]">{chk.severity}</td>
                      <td className="py-2.5 px-3 text-[var(--text-muted)]">{chk.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
