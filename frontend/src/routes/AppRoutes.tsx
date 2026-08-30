import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
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
      {/* Public Landing Experience */}
      <Route path="/" element={<LandingPage />} />

      {/* Main Application Shell Layout */}
      <Route element={<AppShell />}>
        <Route path="overview" element={<OverviewPage />} />
        <Route path="facilities" element={<FacilitiesPage />} />
        <Route path="facilities/:id" element={<FacilityDetailPage />} />
        <Route path="regions" element={<RegionsPage />} />
        <Route path="forecast" element={<ForecastPage />} />
        <Route path="data-quality" element={<DataQualityPage />} />
      </Route>

      {/* Fallback Redirection */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};
