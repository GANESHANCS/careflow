import React from 'react';
import { ScrollReveal } from '../motion/ScrollReveal';
import { Button } from '../buttons/Button';
import { Activity, ArrowRight, ShieldCheck } from 'lucide-react';

export interface LandingCTAProps {
  onEnterClick: () => void;
}

export const LandingCTA: React.FC<LandingCTAProps> = ({ onEnterClick }) => {
  return (
    <section className="py-24 px-6 sm:px-12 lg:px-16 bg-[var(--bg-surface)] border-t border-[var(--border-subtle)] relative z-10 text-[var(--text-primary)]">
      <div className="max-w-4xl mx-auto text-center">
        <ScrollReveal>
          <div className="w-14 h-14 rounded-2xl bg-[var(--teal-50)] text-[var(--teal-600)] flex items-center justify-center mx-auto mb-6 shadow-xs border border-[var(--teal-100)]">
            <Activity className="w-7 h-7" />
          </div>

          <h2 className="font-display font-extrabold text-3xl sm:text-5xl tracking-tight text-[var(--text-primary)] mb-4">
            Ready to explore healthcare intelligence?
          </h2>

          <p className="text-base sm:text-lg text-[var(--text-secondary)] leading-relaxed max-w-xl mx-auto mb-8">
            Access operational facility directories, regional demand comparisons, forecasting models, and data quality audits.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Button
              variant="primary"
              size="lg"
              onClick={onEnterClick}
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Enter Operational Platform
            </Button>
          </div>

          <div className="mt-8 text-xs text-[var(--text-muted)] flex items-center justify-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[var(--teal-600)]" />
            <span>CAREFlow India Governance Framework • Baseline Primacy Enforced</span>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
