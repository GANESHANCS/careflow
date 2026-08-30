import React, { useEffect, useState } from 'react';
import { InteractiveHeading } from '../components/typography/InteractiveHeading';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { Button } from '../components/buttons/Button';
import { EmptyState } from '../components/feedback/EmptyState';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { api } from '../api/client';
import type { RegionalAnalyticsResponse } from '../api/types';
import { RefreshCw } from 'lucide-react';

export const RegionsPage: React.FC = () => {
  const [data, setData] = useState<RegionalAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [level, setLevel] = useState<'district' | 'state'>('district');

  const fetchRegionalData = () => {
    setLoading(true);
    setError(null);
    api.getRegionalAnalytics({ level })
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Unable to retrieve regional analytics.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchRegionalData();
  }, [level]);

  return (
    <div className="space-y-8">
      <ScrollReveal>
        <InteractiveHeading
          title="Regional Utilization Intelligence"
          subtitle="Compare healthcare demand aggregations across States and Districts"
          badge="Regions"
          badgeColor="teal"
        />
      </ScrollReveal>

      {/* Controls */}
      <ScrollReveal delay={0.1}>
        <div className="flex items-center justify-between gap-4 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-4 shadow-xs">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[var(--text-secondary)]">Aggregation Level:</span>
            <div className="inline-flex rounded-lg border border-[var(--border-subtle)] p-0.5 bg-[var(--bg-surface-subtle)]">
              <button
                onClick={() => setLevel('district')}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all cursor-pointer focus-ring ${level === 'district' ? 'bg-white text-[var(--teal-700)] shadow-xs font-semibold' : 'text-[var(--text-muted)]'}`}
              >
                District Level
              </button>
              <button
                onClick={() => setLevel('state')}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-all cursor-pointer focus-ring ${level === 'state' ? 'bg-white text-[var(--teal-700)] shadow-xs font-semibold' : 'text-[var(--text-muted)]'}`}
              >
                State Level
              </button>
            </div>
          </div>

          <Button variant="ghost" size="sm" onClick={fetchRegionalData} leftIcon={<RefreshCw className="w-3.5 h-3.5" />}>
            Refresh
          </Button>
        </div>
      </ScrollReveal>

      {/* Content */}
      <ScrollReveal delay={0.2}>
        {loading ? (
          <LoadingState type="table" />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchRegionalData} />
        ) : data && data.regions.length > 0 ? (
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6">
            <h3 className="font-display font-bold text-base mb-4">Regional Summary Table</h3>
            {/* Table visualization ready */}
          </div>
        ) : (
          <EmptyState
            title="NO REGIONAL OBSERVATIONS LOADED"
            description="Regional analytics aggregate state and district level healthcare utilization once raw HMIS observation datasets are ingested into the database."
            actionText="Retry Query"
            onAction={fetchRegionalData}
          />
        )}
      </ScrollReveal>
    </div>
  );
};
