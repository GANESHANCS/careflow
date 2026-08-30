import React from 'react';
import { useNavigate } from 'react-router-dom';
import { HeroVideo } from '../components/landing/HeroVideo';
import { LandingHero } from '../components/landing/LandingHero';
import { TextTransformSection } from '../components/landing/TextTransformSection';
import { NarrativeShowcase } from '../components/landing/NarrativeShowcase';
import { LandingCTA } from '../components/landing/LandingCTA';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  const handleEnterPlatform = () => {
    // Navigate smoothly to overview page
    navigate('/overview');
  };

  return (
    <div className="relative min-h-screen bg-[#0B0F19] text-[var(--text-primary)] selection:bg-[var(--teal-100)] selection:text-[var(--teal-700)] font-body">
      {/* Hero Viewport Section with Background Video */}
      <section className="relative min-h-screen w-full flex flex-col justify-between overflow-hidden">
        <HeroVideo />
        <LandingHero onExploreClick={handleEnterPlatform} />
      </section>

      {/* Guided Scroll-Driven Text Transformation & Dark-to-Light Background Shift */}
      <TextTransformSection />

      {/* Visual Process Narrative Architecture */}
      <NarrativeShowcase />

      {/* Final Call to Action */}
      <LandingCTA onEnterClick={handleEnterPlatform} />

      {/* Minimal Landing Footer */}
      <footer className="w-full bg-[var(--bg-surface)] border-t border-[var(--border-subtle)] py-6 px-6 sm:px-12 text-center text-xs text-[var(--text-muted)]">
        CAREFlow India Healthcare Platform &copy; 2026 — Time-Series Analytics & Capacity Intelligence
      </footer>
    </div>
  );
};
