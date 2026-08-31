import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react';

export const ForecastMethodology: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const steps = [
    {
      title: '1. Data Integrity & Missingness Handling',
      content:
        'Observations are validated against HMIS quality rules. Missing monthly values remain missing and are never silently converted to zero. For model training, linear interpolation or historical median imputation is applied strictly within training windows.',
    },
    {
      title: '2. Eligibility Guardrails',
      content:
        'Series must satisfy strict eligibility criteria: at least 24 valid monthly observations for seasonal modeling, <30% total missingness, and ≤3 consecutive missing months. Ineligible series display diagnostic explanations rather than unreliable forecasts.',
    },
    {
      title: '3. Time-Series Feature Engineering',
      content:
        'Features are engineered using historical lags (lag_1, lag_2, lag_3, lag_12), rolling statistics (3-month rolling mean/std), and cyclical trigonometric month encodings (sin/cos of month). Supervised datasets prevent future observation leakage.',
    },
    {
      title: '4. Candidate Model Suite',
      content:
        'Evaluates 4 mandatory baselines (Naive, Seasonal Naive, Moving Average 3m, Holt-Winters) alongside 4 machine learning candidates (SARIMAX, Ridge Regression, Random Forest, Gradient Boosting).',
    },
    {
      title: '5. Chronological Validation Split',
      content:
        'Uses time-aware chronological validation splits without random shuffling. Models are trained on historical observations up to cutoff date t-N and validated on the holdout period t-N to t.',
    },
    {
      title: '6. Automated Model Selection & Baseline Primacy',
      content:
        'Selection is governed by Mean Absolute Error (MAE). Complex ML models win ONLY if they demonstrate statistically superior validation accuracy over the strongest mandatory baseline. A 1% tie-breaking rule favors simpler baselines.',
    },
    {
      title: '7. ~95% Prediction Interval Estimation',
      content:
        'Residual standard error (σ_val) from the validation split is scaled by multi-step horizon multipliers to calculate ~95% prediction intervals (lower_bound and upper_bound), with non-negative lower bound enforcement.',
    },
  ];

  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl p-6 shadow-xs mb-8">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between gap-4 cursor-pointer text-left focus-ring rounded-xl"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-[var(--purple-100)] text-[var(--purple-700)]">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-primary)]">
              Phase 5 Forecasting Architecture & ML Methodology
            </h3>
            <p className="text-xs text-[var(--text-muted)]">
              Click to {isOpen ? 'collapse' : 'expand'} detailed technical methodology, validation split rules, and model governance
            </p>
          </div>
        </div>

        <div className="p-2 rounded-xl bg-[var(--bg-surface-subtle)] text-[var(--text-muted)] border border-[var(--border-subtle)]">
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {isOpen && (
        <div className="mt-6 pt-5 border-t border-[var(--border-subtle)] space-y-4 text-xs">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {steps.map((step, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] space-y-1.5">
                <div className="flex items-center gap-1.5 font-bold text-[var(--purple-900)]">
                  <CheckCircle2 className="w-4 h-4 text-[var(--purple-600)] flex-shrink-0" />
                  <span>{step.title}</span>
                </div>
                <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{step.content}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
