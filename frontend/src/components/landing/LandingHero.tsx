import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Activity, ArrowRight, ShieldCheck } from 'lucide-react';
import { Button } from '../buttons/Button';

export interface LandingHeroProps {
  onExploreClick: () => void;
}

export const LandingHero: React.FC<LandingHeroProps> = ({ onExploreClick }) => {
  const shouldReduceMotion = useReducedMotion();

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 20 },
    show: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.6, ease: 'easeOut' as const },
    },
  };

  return (
    <div className="relative min-h-[90vh] flex flex-col justify-between px-6 sm:px-12 lg:px-16 pt-24 pb-12 z-10 max-w-7xl mx-auto text-white">
      {/* Top Header Brand Row */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--teal-600)] text-white flex items-center justify-center shadow-lg shadow-teal-900/30">
            <Activity className="w-5 h-5" />
          </div>
          <span className="font-display font-extrabold text-xl tracking-tight">CAREFlow</span>
          <span className="text-[10px] font-bold tracking-widest text-teal-300 uppercase px-2 py-0.5 rounded-full bg-teal-950/60 border border-teal-500/30">
            India Platform
          </span>
        </div>

        <button
          onClick={onExploreClick}
          className="text-xs font-semibold text-slate-300 hover:text-white transition-colors focus-ring px-3 py-1.5 rounded-lg border border-slate-700/60 hover:border-slate-500 bg-slate-900/40 backdrop-blur-xs cursor-pointer"
        >
          Enter Platform →
        </button>
      </motion.div>

      {/* Main Editorial Hero Composition */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="my-auto py-16 max-w-4xl"
      >
        {/* 1. Brand Tag */}
        <motion.div variants={itemVariants} className="mb-4">
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/20 backdrop-blur-xs">
            <ShieldCheck className="w-3.5 h-3.5" />
            Operational Healthcare Intelligence
          </span>
        </motion.div>

        {/* 2. Main Headline */}
        <motion.h1
          variants={itemVariants}
          className="font-display font-extrabold text-4xl sm:text-6xl lg:text-7xl tracking-tight leading-[1.08] mb-6 text-slate-50"
        >
          Healthcare intelligence, <br />
          <span className="bg-gradient-to-r from-teal-200 via-emerald-300 to-teal-400 bg-clip-text text-transparent">
            made visible.
          </span>
        </motion.h1>

        {/* 3. Subtitle */}
        <motion.p
          variants={itemVariants}
          className="text-base sm:text-xl text-slate-300 font-normal leading-relaxed max-w-2xl mb-8"
        >
          Understand monthly OPD and inpatient attendance patterns across India’s health system. Anticipate future demand with baseline-validated time-series forecasts.
        </motion.p>

        {/* 4. Primary CTA */}
        <motion.div variants={itemVariants} className="flex flex-wrap items-center gap-4">
          <Button
            variant="primary"
            size="lg"
            onClick={onExploreClick}
            rightIcon={<ArrowRight className="w-4 h-4" />}
            className="shadow-xl shadow-teal-900/30"
          >
            Explore CAREFlow Platform
          </Button>

          <span className="text-xs text-slate-400 font-medium">
            Baseline Primacy • Zero Synthetic Data Policy
          </span>
        </motion.div>
      </motion.div>

      {/* Scroll Down Indicator */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1, duration: 0.6 }}
        className="flex flex-col items-center gap-2 text-xs text-slate-400 font-medium tracking-wide uppercase"
      >
        <span>Scroll to explore narrative</span>
        <div className="w-5 h-8 rounded-full border border-slate-700 flex justify-center pt-1.5">
          <span className="w-1 h-2 rounded-full bg-teal-400 animate-bounce" />
        </div>
      </motion.div>
    </div>
  );
};
