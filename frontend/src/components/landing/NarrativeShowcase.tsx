import React from 'react';
import { ScrollReveal } from '../motion/ScrollReveal';
import { Database, Layers, TrendingUp, ShieldCheck } from 'lucide-react';

export const NarrativeShowcase: React.FC = () => {
  return (
    <section className="py-24 px-6 sm:px-12 lg:px-16 bg-[var(--bg-app)] text-[var(--text-primary)] relative z-10 max-w-7xl mx-auto border-t border-[var(--border-subtle)]">
      <ScrollReveal>
        <div className="text-center max-w-3xl mx-auto mb-16">
          <span className="text-xs font-semibold text-[var(--teal-600)] uppercase tracking-widest px-3 py-1 rounded-full bg-[var(--teal-50)] border border-[var(--teal-100)]">
            Intelligence Architecture
          </span>
          <h2 className="font-display font-extrabold text-3xl sm:text-5xl tracking-tight mt-4 text-[var(--text-primary)]">
            From historical HMIS patterns <br />
            <span className="text-[var(--teal-600)]">to actionable future demand.</span>
          </h2>
          <p className="mt-4 text-sm sm:text-base text-[var(--text-secondary)] leading-relaxed">
            CAREFlow connects raw district observations to baseline-validated machine learning forecasts through a four-stage pipeline.
          </p>
        </div>
      </ScrollReveal>

      {/* Abstract Process Visual Architecture Cards (No Fake Stats) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <ScrollReveal delay={0.1}>
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all duration-300 group h-full flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-[var(--blue-50)] text-[var(--blue-600)] flex items-center justify-center mb-6 group-hover:scale-105 transition-transform duration-200">
                <Database className="w-6 h-6" />
              </div>

              <h3 className="font-display font-bold text-xl text-[var(--text-primary)] mb-2">
                1. Data Governance & Audit
              </h3>

              <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
                Ingests monthly HMIS facility returns, auditing missing values, observed zeroes, and reporting completeness without data fabrication.
              </p>
            </div>

            {/* Abstract Visual Signal Motif */}
            <div className="h-20 bg-[var(--bg-surface-subtle)] rounded-xl border border-[var(--border-subtle)] p-3 flex items-center justify-around gap-1">
              {[40, 70, 30, 85, 60, 95, 50, 75].map((h, i) => (
                <div key={i} style={{ height: `${h}%` }} className="w-2 bg-[var(--blue-500)]/40 rounded-full group-hover:bg-[var(--blue-600)] transition-colors" />
              ))}
            </div>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={0.2}>
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all duration-300 group h-full flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-[var(--teal-50)] text-[var(--teal-600)] flex items-center justify-center mb-6 group-hover:scale-105 transition-transform duration-200">
                <Layers className="w-6 h-6" />
              </div>

              <h3 className="font-display font-bold text-xl text-[var(--text-primary)] mb-2">
                2. Regional Analytics Engine
              </h3>

              <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
                Aggregates time-series OPD attendance and admission metrics across state and district levels with safe MoM/YoY growth rate logic.
              </p>
            </div>

            {/* Abstract Layered Grid Motif */}
            <div className="h-20 bg-[var(--bg-surface-subtle)] rounded-xl border border-[var(--border-subtle)] p-3 flex flex-col justify-between">
              <div className="h-3 bg-[var(--teal-500)]/30 rounded-md w-full" />
              <div className="h-3 bg-[var(--teal-500)]/50 rounded-md w-4/5" />
              <div className="h-3 bg-[var(--teal-600)] rounded-md w-3/5" />
            </div>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={0.3}>
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs hover:shadow-md transition-all duration-300 group h-full flex flex-col justify-between">
            <div>
              <div className="w-12 h-12 rounded-xl bg-[var(--purple-50)] text-[var(--purple-600)] flex items-center justify-center mb-6 group-hover:scale-105 transition-transform duration-200">
                <TrendingUp className="w-6 h-6" />
              </div>

              <h3 className="font-display font-bold text-xl text-[var(--text-primary)] mb-2">
                3. Baseline Primacy ML Engine
              </h3>

              <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-6">
                Evaluates Naive, Holt-Winters, SARIMAX, and Gradient Boosting models. Candidate models are selected only when beating baseline metrics.
              </p>
            </div>

            {/* Abstract Projection Bounds Motif */}
            <div className="h-20 bg-[var(--purple-50)]/50 rounded-xl border border-[var(--purple-100)] p-3 flex items-center justify-between relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-[var(--purple-200)]/40 to-transparent" />
              <ShieldCheck className="w-6 h-6 text-[var(--purple-600)] relative z-10 mx-auto" />
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
};
