import React, { useState, useEffect } from 'react';
import { InteractiveHeading } from '../components/typography/InteractiveHeading';
import { ScrollReveal } from '../components/motion/ScrollReveal';
import { LoadingState } from '../components/feedback/LoadingState';
import { ErrorState } from '../components/feedback/ErrorState';
import { EmptyState } from '../components/feedback/EmptyState';
import { api } from '../api/client';
import type { DataQualityAnalyticsResponse } from '../api/types';
import { ShieldCheck, AlertTriangle, CheckCircle, Database } from 'lucide-react';

export const DataQualityPage: React.FC = () => {
  const [data, setData] = useState<DataQualityAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQualityData = () => {
    setLoading(true);
    setError(null);
    api.getDataQualityAnalytics()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || 'Unable to retrieve data quality audit log.');
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchQualityData();
  }, []);

  return (
    <div className="space-y-8">
      <ScrollReveal>
        <InteractiveHeading
          title="Data Quality & Integrity Governance"
          subtitle="Audit missingness, observed zero values, invalid counts, and reporting completeness across the database"
          badge="Quality Audit"
          badgeColor="amber"
        />
      </ScrollReveal>

      {/* Audit Stats Header */}
      <ScrollReveal delay={0.1}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-1">
              <span>Overall Quality Score</span>
              <ShieldCheck className="w-4 h-4 text-[var(--green-600)]" />
            </div>
            <div className="text-3xl font-extrabold font-display text-[var(--text-primary)]">
              {loading ? '...' : `${data?.overall_quality_score ?? 100}%`}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1">
              Validation Pass Rate
            </div>
          </div>

          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-1">
              <span>Valid Observations</span>
              <CheckCircle className="w-4 h-4 text-[var(--teal-600)]" />
            </div>
            <div className="text-3xl font-extrabold font-display text-[var(--text-primary)]">
              {loading ? '...' : data?.valid_count ?? 0}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1">
              Verified Numeric Records
            </div>
          </div>

          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-1">
              <span>Observed Zeroes</span>
              <Database className="w-4 h-4 text-[var(--blue-600)]" />
            </div>
            <div className="text-3xl font-extrabold font-display text-[var(--text-primary)]">
              {loading ? '...' : data?.zero_count ?? 0}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1">
              Preserved Operational Zeroes
            </div>
          </div>

          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-5 shadow-xs">
            <div className="flex items-center justify-between text-xs text-[var(--text-muted)] mb-1">
              <span>Missing Values</span>
              <AlertTriangle className="w-4 h-4 text-[var(--coral-600)]" />
            </div>
            <div className="text-3xl font-extrabold font-display text-[var(--text-primary)]">
              {loading ? '...' : data?.missing_count ?? 0}
            </div>
            <div className="text-xs text-[var(--text-muted)] mt-1">
              Preserved Missing Months
            </div>
          </div>
        </div>
      </ScrollReveal>

      {/* Detailed Quality Log or Empty State */}
      <ScrollReveal delay={0.2}>
        {loading ? (
          <LoadingState type="table" />
        ) : error ? (
          <ErrorState message={error} onRetry={fetchQualityData} />
        ) : data && data.total_observations > 0 ? (
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6">
            <h3 className="font-display font-bold text-base mb-4">Data Quality Breakdown</h3>
            {/* Table visualization ready */}
          </div>
        ) : (
          <EmptyState
            title="NO DATA QUALITY ISSUES LOGGED"
            description="The database currently contains no raw observation anomalies. Quality checks execute automatically during Phase 2 ingestion."
            actionText="Refresh Quality Log"
            onAction={fetchQualityData}
          />
        )}
      </ScrollReveal>
    </div>
  );
};
