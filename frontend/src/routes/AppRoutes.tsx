import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { LoginPage } from '../pages/LoginPage';
import { ProtectedRoute } from '../auth/ProtectedRoute';
import { AppShell } from '../components/layout/AppShell';
import { OverviewPage } from '../pages/OverviewPage';
import { FacilitiesPage } from '../pages/FacilitiesPage';
import { FacilityDetailPage } from '../pages/FacilityDetailPage';
import { RegionsPage } from '../pages/RegionsPage';
import { ForecastPage } from '../pages/ForecastPage';
import { DataQualityPage } from '../pages/DataQualityPage';

export const AppRoutes: React.FC = () => {
  return (
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
      </Route>

      {/* Fallback Redirection */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
