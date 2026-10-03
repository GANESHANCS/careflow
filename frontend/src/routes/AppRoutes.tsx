import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from '../auth/ProtectedRoute';
import { AppShell } from '../components/layout/AppShell';

// Route-level code-splitting with React.lazy
const LandingPage = lazy(() => import('../pages/LandingPage').then(m => ({ default: m.LandingPage })));
const LoginPage = lazy(() => import('../pages/LoginPage').then(m => ({ default: m.LoginPage })));
const OverviewPage = lazy(() => import('../pages/OverviewPage').then(m => ({ default: m.OverviewPage })));
const FacilitiesPage = lazy(() => import('../pages/FacilitiesPage').then(m => ({ default: m.FacilitiesPage })));
const FacilityDetailPage = lazy(() => import('../pages/FacilityDetailPage').then(m => ({ default: m.FacilityDetailPage })));
const RegionsPage = lazy(() => import('../pages/RegionsPage').then(m => ({ default: m.RegionsPage })));
const ForecastPage = lazy(() => import('../pages/ForecastPage').then(m => ({ default: m.ForecastPage })));
const DataQualityPage = lazy(() => import('../pages/DataQualityPage').then(m => ({ default: m.DataQualityPage })));
const ImportPage = lazy(() => import('../pages/ImportPage').then(m => ({ default: m.ImportPage })));

const PageFallback: React.FC = () => (
  <div className="max-w-7xl mx-auto p-6 sm:p-8 animate-pulse space-y-6">
    <div className="h-8 bg-[var(--bg-surface-subtle)] rounded-lg w-1/4" />
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="h-28 bg-[var(--bg-surface-subtle)] rounded-xl" />
      <div className="h-28 bg-[var(--bg-surface-subtle)] rounded-xl" />
      <div className="h-28 bg-[var(--bg-surface-subtle)] rounded-xl" />
    </div>
    <div className="h-64 bg-[var(--bg-surface-subtle)] rounded-xl" />
  </div>
);

export const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />

        {/* Main Application Shell Layout with Protected Workspaces */}
        <Route element={<AppShell />}>
          <Route
            path="overview"
            element={
              <ProtectedRoute>
                <OverviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="facilities"
            element={
              <ProtectedRoute>
                <FacilitiesPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="facilities/:id"
            element={
              <ProtectedRoute>
                <FacilityDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="regions"
            element={
              <ProtectedRoute>
                <RegionsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="forecast"
            element={
              <ProtectedRoute>
                <ForecastPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="data-quality"
            element={
              <ProtectedRoute>
                <DataQualityPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="imports"
            element={
              <ProtectedRoute>
                <ImportPage />
              </ProtectedRoute>
            }
          />
        </Route>

        {/* Fallback Redirection */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
};
