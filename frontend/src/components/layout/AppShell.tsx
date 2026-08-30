import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { TopNav } from './TopNav';
import { SlimRail } from './SlimRail';
import { MobileNav } from './MobileNav';
import { ShieldCheck, Info } from 'lucide-react';

export const AppShell: React.FC = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-[var(--bg-app)] text-[var(--text-primary)] flex flex-col font-body selection:bg-[var(--teal-100)] selection:text-[var(--teal-700)]">
      {/* Top Application Header */}
      <TopNav
        isMobileMenuOpen={isMobileMenuOpen}
        onMobileMenuToggle={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
      />

      {/* Main Container with Sidebar + Content */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Slim Desktop Navigation Rail */}
        <SlimRail />

        {/* Responsive Mobile Drawer Menu */}
        <MobileNav
          isOpen={isMobileMenuOpen}
          onClose={() => setIsMobileMenuOpen(false)}
        />

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 min-w-0">
          <Outlet />
        </main>
      </div>

      {/* Editorial Platform Footer Status Bar */}
      <footer className="w-full bg-[var(--bg-surface)] border-t border-[var(--border-subtle)] py-3 px-4 sm:px-8 text-xs text-[var(--text-muted)] mt-auto">
        <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[var(--teal-500)]" />
            <span className="font-semibold text-[var(--text-secondary)]">CAREFlow Governance Framework</span>
            <span className="text-[var(--border-strong)]">|</span>
            <span>Monthly HMIS Time-Series Analytics & Forecasting Engine</span>
          </div>

          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-[var(--teal-600)]" />
              <span>Baseline Primacy Enforced</span>
            </span>
            <span className="flex items-center gap-1 text-[var(--amber-600)]">
              <Info className="w-3.5 h-3.5" />
              <span>Awaiting Raw HMIS Files</span>
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};
