import React, { useState, useEffect } from 'react';
import { InteractiveHeading } from '../components/typography/InteractiveHeading';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { ChartContainer } from '../components/charts/ChartContainer';
import { EmptyState } from '../components/feedback/EmptyState';
import { api } from '../api/client';
import type { ModelMetrics } from '../api/types';
import { Cpu } from 'lucide-react';

export const ForecastPage: React.FC = () => {
  const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchModelMetrics = () => {
    setLoading(true);
    setError(null);
    api.getModelMetrics()
      .then((res) => {
        setMetrics(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Unable to query forecasting model metadata registry.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchModelMetrics();
  }, []);

  return (
    <div className="space-y-8">
      <ScrollReveal>
        <InteractiveHeading
          title="Time-Series Forecasting & ML Engine"
          subtitle="Monthly demand prediction with 95% approximate prediction bounds and baseline primacy validation"
          badge="ML Engine"
          badgeColor="purple"
        />
      </ScrollReveal>

      {/* Model Selection Governance Banner */}
      <ScrollReveal delay={0.1}>
        <div className="bg-[var(--purple-50)] border border-[var(--purple-100)] rounded-xl p-5 text-xs text-[var(--text-secondary)] leading-relaxed flex items-start gap-3">
          <Cpu className="w-5 h-5 text-[var(--purple-600)] shrink-0 mt-0.5" />
          <div>
            <span className="font-bold text-[var(--purple-700)] block mb-1 text-sm font-display">
              Baseline Primacy Governance
            </span>
            <p>
              The CAREFlow forecasting engine evaluates 4 mandatory baselines (Naive, Seasonal Naive, Moving Average, Holt-Winters) and 4 candidate ML models (SARIMAX, Ridge, Random Forest, Gradient Boosting). Candidate models are selected only when demonstrating relative validation improvement (&gt;1%) over the strongest baseline.
            </p>
          </div>
        </div>
      </ScrollReveal>

      {/* Registry Table or Empty State */}
      <ScrollReveal delay={0.2}>
        {loading ? (
          <LoadingState type="table" />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchModelMetrics} />
        ) : metrics.length > 0 ? (
          <ChartContainer title="Registered Forecasting Models" status="success">
            <div className="p-4 text-xs font-mono">
              {metrics.length} model(s) registered in SQLite model_metadata table.
            </div>
          </ChartContainer>
        ) : (
          <EmptyState
            title="NO FORECASTING MODELS persistED"
            description="Run 'python scripts/train_forecasting_models.py' after populating observation data to execute baseline comparison and generate persistent 12-month forecasts."
            actionText="Refresh Metadata Registry"
            onAction={fetchModelMetrics}
          />
        )}
      </ScrollReveal>
    </div>
  );
};
