import React from 'react';
import { ShieldCheck, MapPin, Calendar, Layers, AlertCircle, FileSpreadsheet, TrendingUp, BarChart3, Table } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';

export type DistrictTab = 'trends' | 'compare' | 'table' | 'quality';

interface DistrictHeaderProps {
  activeTab: DistrictTab;
  onTabChange: (tab: DistrictTab) => void;
  selectedDistrict: string;
  totalDistricts: number;
  totalIndicators: number;
}

export const DistrictHeader: React.FC<DistrictHeaderProps> = ({
  activeTab,
  onTabChange,
  selectedDistrict,
  totalDistricts,
  totalIndicators,
}) => {
  const shouldReduceMotion = useReducedMotion();

  const tabs: { id: DistrictTab; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: 'trends', label: 'Monthly Trends', icon: TrendingUp },
    { id: 'compare', label: 'District Comparison', icon: BarChart3 },
    { id: 'table', label: 'Observation Records', icon: Table },
    { id: 'quality', label: 'Quality & Provenance', icon: ShieldCheck, badge: 'Phase 11F' },
  ];

  return (
    <div className="space-y-6">
      {/* Primary Header Card */}
      <div className="relative overflow-hidden bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-6 sm:p-8 shadow-xs">
        {/* Background accent banner */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-teal-500/10 via-cyan-500/5 to-transparent rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-teal-50 text-teal-700 border border-teal-200">
                <FileSpreadsheet className="w-3.5 h-3.5" />
                <span>Official State HMIS Returns</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-200">
                <MapPin className="w-3.5 h-3.5" />
                <span>Jurisdiction: District</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200">
                <Calendar className="w-3.5 h-3.5" />
                <span>FY 2015–16 (12 Months)</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-700 border border-stone-200">
                <Layers className="w-3.5 h-3.5 text-stone-500" />
                <span>Segregated Data Stream</span>
              </span>
            </div>

            <div>
              <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[var(--text-primary)] font-display">
                District Healthcare Analytics & Provenance
              </h1>
              <p className="text-sm text-[var(--text-secondary)] mt-1.5 max-w-3xl leading-relaxed">
                Official district-level health administrative intelligence imported from Tamil Nadu HMIS return archives.
                These observations reflect district-wide consolidated reports and are maintained strictly independent from facility clinical logs.
              </p>
            </div>
          </div>

          {/* Quick Metrics Badge */}
          <div className="flex sm:flex-col items-center sm:items-end justify-between p-4 bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-2xl gap-3 sm:gap-1.5 shrink-0">
            <div className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider">Active Scope</div>
            <div className="text-lg font-mono font-extrabold text-[var(--teal-700)]">
              {selectedDistrict ? `${selectedDistrict} District` : `${totalDistricts} Districts`}
            </div>
            <div className="text-[11px] font-medium text-[var(--text-secondary)]">
              {totalIndicators > 0 ? `${totalIndicators} Health Indicators` : '175,872 Ingested Records'}
            </div>
          </div>
        </div>

        {/* Source Separation Disclaimer Callout */}
        <div className="mt-6 pt-4 border-t border-[var(--border-subtle)] flex items-start gap-3 text-xs text-[var(--text-secondary)] bg-amber-50/70 border-l-4 border-l-amber-500 p-3 rounded-r-xl">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-bold text-amber-900">Data Architecture Separation:</span> District observations represent wide-to-long transformed official monthly HMIS totals. In accordance with platform governance, district reports are never summed or merged with facility observations, preserving provenance, zero vs. missing states, and stock metric fidelity.
          </div>
        </div>
      </div>

      {/* Workspace Tab Navigation */}
      <div className="flex border-b border-[var(--border-subtle)] overflow-x-auto no-scrollbar gap-2 sm:gap-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`relative flex items-center gap-2 px-4 py-3 text-sm font-semibold whitespace-nowrap transition-all cursor-pointer focus-ring rounded-t-xl ${
                isActive
                  ? 'text-[var(--teal-700)] bg-[var(--teal-50)]/50 border-b-2 border-[var(--teal-600)]'
                  : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-subtle)]'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-[var(--teal-600)]' : 'text-[var(--text-muted)]'}`} />
              <span>{tab.label}</span>
              {tab.badge && (
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-teal-100 text-teal-800 border border-teal-200">
                  {tab.badge}
                </span>
              )}
              {isActive && (
                <motion.div
                  layoutId={shouldReduceMotion ? undefined : 'districtActiveTabIndicator'}
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--teal-600)]"
                  transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
