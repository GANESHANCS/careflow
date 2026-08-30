import React, { useRef } from 'react';
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion';

export const TextTransformSection: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  });

  // Full-bleed background color shift: Dark (#0B0F19) -> Warm Ivory (#FAF9F6)
  // Background stays solid dark through Stage 1 & 2, morphs during Stage 3 (0.40 - 0.60), stays warm ivory through Stage 4 & 5
  const bgColor = useTransform(
    scrollYProgress,
    [0.0, 0.40, 0.60, 1.0],
    ['#0B0F19', '#0B0F19', '#FAF9F6', '#FAF9F6']
  );

  // --- STAGE MAPPINGS (Exact 20% scroll windows, clean contrast) --- //

  // Non-overlapping display rules guarantee exactly one stage renders at any scroll offset
  const stage1Display = useTransform(scrollYProgress, (v) => (v < 0.20 ? 'flex' : 'none'));
  const stage2Display = useTransform(scrollYProgress, (v) => (v >= 0.20 && v < 0.40 ? 'flex' : 'none'));
  const stage3Display = useTransform(scrollYProgress, (v) => (v >= 0.40 && v < 0.60 ? 'flex' : 'none'));
  const stage4Display = useTransform(scrollYProgress, (v) => (v >= 0.60 && v < 0.80 ? 'flex' : 'none'));
  const stage5Display = useTransform(scrollYProgress, (v) => (v >= 0.80 ? 'flex' : 'none'));

  // Stage 1: Operational Dynamics (0.00 - 0.20) [Dark Theme]
  const stage1Opacity = useTransform(scrollYProgress, [0.0, 0.16, 0.20], [1, 1, 0]);
  const stage1Y = useTransform(scrollYProgress, [0.0, 0.16, 0.20], [0, 0, shouldReduceMotion ? 0 : -20]);

  // Stage 2: Step 01 — Observation (0.20 - 0.40) [Dark Theme]
  const stage2Opacity = useTransform(scrollYProgress, [0.20, 0.24, 0.36, 0.40], [0, 1, 1, 0]);
  const stage2Y = useTransform(
    scrollYProgress,
    [0.20, 0.24, 0.36, 0.40],
    [shouldReduceMotion ? 0 : 20, 0, 0, shouldReduceMotion ? 0 : -20]
  );

  // Stage 3: Step 02 — Analytics (0.40 - 0.60) [Transition Theme]
  const stage3Opacity = useTransform(scrollYProgress, [0.40, 0.44, 0.56, 0.60], [0, 1, 1, 0]);
  const stage3Y = useTransform(
    scrollYProgress,
    [0.40, 0.44, 0.56, 0.60],
    [shouldReduceMotion ? 0 : 20, 0, 0, shouldReduceMotion ? 0 : -20]
  );

  // Stage 4: Step 03 — Forecasting (0.60 - 0.80) [Light Theme]
  const stage4Opacity = useTransform(scrollYProgress, [0.60, 0.64, 0.76, 0.80], [0, 1, 1, 0]);
  const stage4Y = useTransform(
    scrollYProgress,
    [0.60, 0.64, 0.76, 0.80],
    [shouldReduceMotion ? 0 : 20, 0, 0, shouldReduceMotion ? 0 : -20]
  );

  // Stage 5: Step 04 — Decision Governance (0.80 - 1.00) [Light Theme]
  const stage5Opacity = useTransform(scrollYProgress, [0.80, 0.84, 1.0], [0, 1, 1]);
  const stage5Y = useTransform(
    scrollYProgress,
    [0.80, 0.84, 1.0],
    [shouldReduceMotion ? 0 : 20, 0, 0]
  );

  // Dynamic text color transform for Stage 3 during background morph
  const stage3HeadingColor = useTransform(
    scrollYProgress,
    [0.40, 0.50, 0.60],
    ['#FFFFFF', '#1E1B4B', '#0F172A']
  );
  const stage3BodyColor = useTransform(
    scrollYProgress,
    [0.40, 0.50, 0.60],
    ['#CBD5E1', '#334155', '#1E293B']
  );

  // Side Progress Bar indicator
  const progressHeight = useTransform(scrollYProgress, [0, 1], ['0%', '100%']);

  return (
    <motion.div
      ref={containerRef}
      style={{ backgroundColor: bgColor }}
      className="relative h-[350vh] w-full transition-colors duration-300"
    >
      <div className="sticky top-0 h-screen w-full flex flex-col justify-center items-center px-6 text-center overflow-hidden">
        {/* Subtle Right-side Narrative Step Rail Indicator */}
        <div className="absolute right-6 sm:right-12 top-1/2 -translate-y-1/2 h-40 w-1 bg-slate-700/30 rounded-full overflow-hidden hidden md:block z-20">
          <motion.div
            style={{ height: progressHeight }}
            className="w-full bg-[var(--teal-500)] rounded-full"
          />
        </div>

        {/* Stage 1: Healthcare systems are constantly moving */}
        <motion.div
          style={{ opacity: stage1Opacity, y: stage1Y, display: stage1Display }}
          className="absolute inset-0 flex flex-col items-center justify-center max-w-4xl mx-auto px-6 pointer-events-none z-10"
        >
          <span className="text-xs font-bold uppercase tracking-widest text-teal-300 mb-4 px-3.5 py-1 rounded-full bg-teal-950/80 border border-teal-500/40 backdrop-blur-md shadow-lg shadow-teal-950/50">
            Operational Dynamics
          </span>
          <h2 className="font-display font-extrabold text-3xl sm:text-5xl lg:text-6xl tracking-tight leading-[1.15] text-slate-50">
            Healthcare systems are <br />
            <span className="bg-gradient-to-r from-teal-200 via-emerald-300 to-teal-400 bg-clip-text text-transparent">
              constantly moving.
            </span>
          </h2>
          <p className="mt-6 text-base sm:text-lg max-w-xl mx-auto text-slate-300 font-normal leading-relaxed">
            Patient attendance flows continuously across District Hospitals, CHCs, and PHCs across all 36 States and Union Territories.
          </p>
        </motion.div>

        {/* Stage 2: UNDERSTAND HEALTHCARE DEMAND */}
        <motion.div
          style={{ opacity: stage2Opacity, y: stage2Y, display: stage2Display }}
          className="absolute inset-0 flex flex-col items-center justify-center max-w-4xl mx-auto px-6 pointer-events-none z-10"
        >
          <span className="text-xs font-bold uppercase tracking-widest text-sky-300 mb-4 px-3.5 py-1 rounded-full bg-sky-950/80 border border-sky-500/40 backdrop-blur-md shadow-lg shadow-sky-950/50">
            Step 01 — Observation
          </span>
          <h2 className="font-display font-extrabold text-4xl sm:text-6xl lg:text-7xl tracking-tight leading-none text-slate-50">
            UNDERSTAND <br />
            <span className="bg-gradient-to-r from-sky-300 via-blue-400 to-indigo-300 bg-clip-text text-transparent">
              HEALTHCARE DEMAND
            </span>
          </h2>
          <p className="mt-6 text-base sm:text-lg max-w-xl mx-auto text-slate-300 font-normal leading-relaxed">
            Transform monthly HMIS records into structured, audit-ready observations across outpatient and inpatient indicators.
          </p>
        </motion.div>

        {/* Stage 3: ANALYZE PATTERNS */}
        <motion.div
          style={{ opacity: stage3Opacity, y: stage3Y, display: stage3Display }}
          className="absolute inset-0 flex flex-col items-center justify-center max-w-4xl mx-auto px-6 pointer-events-none z-10"
        >
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-800 mb-4 px-3.5 py-1 rounded-full bg-indigo-100 border border-indigo-300 backdrop-blur-md shadow-sm">
            Step 02 — Analytics
          </span>
          <motion.h2
            style={{ color: stage3HeadingColor }}
            className="font-display font-extrabold text-4xl sm:text-6xl lg:text-7xl tracking-tight leading-none"
          >
            ANALYZE <br />
            <span className="text-indigo-600">PATTERNS</span>
          </motion.h2>
          <motion.p
            style={{ color: stage3BodyColor }}
            className="mt-6 text-base sm:text-lg max-w-xl mx-auto font-normal leading-relaxed"
          >
            Evaluate Month-over-Month growth rates, Year-over-Year trends, and facility reporting completeness.
          </motion.p>
        </motion.div>

        {/* Stage 4: ANTICIPATE WHAT'S NEXT */}
        <motion.div
          style={{ opacity: stage4Opacity, y: stage4Y, display: stage4Display }}
          className="absolute inset-0 flex flex-col items-center justify-center max-w-4xl mx-auto px-6 pointer-events-none z-10"
        >
          <span className="text-xs font-bold uppercase tracking-widest text-teal-800 mb-4 px-3.5 py-1 rounded-full bg-teal-100 border border-teal-300 shadow-sm">
            Step 03 — Forecasting
          </span>
          <h2 className="font-display font-extrabold text-4xl sm:text-6xl lg:text-7xl tracking-tight leading-none text-slate-900">
            ANTICIPATE <br />
            <span className="bg-gradient-to-r from-teal-700 to-emerald-600 bg-clip-text text-transparent">
              WHAT’S NEXT
            </span>
          </h2>
          <p className="mt-6 text-base sm:text-lg max-w-xl mx-auto text-slate-700 font-normal leading-relaxed">
            Project 12-month demand horizons backed by strict baseline primacy model selection protocols.
          </p>
        </motion.div>

        {/* Stage 5: ACT WITH PRECISION */}
        <motion.div
          style={{ opacity: stage5Opacity, y: stage5Y, display: stage5Display }}
          className="absolute inset-0 flex flex-col items-center justify-center max-w-4xl mx-auto px-6 pointer-events-none z-10"
        >
          <span className="text-xs font-bold uppercase tracking-widest text-emerald-800 mb-4 px-3.5 py-1 rounded-full bg-emerald-100 border border-emerald-300 shadow-sm">
            Step 04 — Decision Governance
          </span>
          <h2 className="font-display font-extrabold text-4xl sm:text-6xl lg:text-7xl tracking-tight leading-none text-slate-900">
            ACT WITH <br />
            <span className="bg-gradient-to-r from-emerald-600 to-teal-700 bg-clip-text text-transparent">
              PRECISION
            </span>
          </h2>
          <p className="mt-6 text-base sm:text-lg max-w-xl mx-auto text-slate-700 font-normal leading-relaxed">
            Equip health administrators with transparent, audit-ready operational insights and reproducible analytics.
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
};

