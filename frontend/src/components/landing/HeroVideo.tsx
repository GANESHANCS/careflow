import React, { useState, useEffect, useRef } from 'react';
import { useReducedMotion } from 'framer-motion';

export const HeroVideo: React.FC = () => {
  const [videoError, setVideoError] = useState(false);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    if (videoRef.current) {
      const playPromise = videoRef.current.play();
      if (playPromise !== undefined && typeof playPromise.then === 'function') {
        playPromise.then(() => {
          setVideoLoaded(true);
        }).catch(() => {
          setVideoError(true);
        });
      }
    }
  }, []);

  return (
    <div className="absolute inset-0 w-full h-full overflow-hidden bg-slate-950 select-none pointer-events-none">
      {/* Primary Production Video Asset */}
      {!videoError && (
        <video
          ref={videoRef}
          src="/media/careflow-hero-loop.mp4"
          autoPlay
          muted
          playsInline
          loop
          onLoadedData={() => setVideoLoaded(true)}
          onError={() => setVideoError(true)}
          className={`w-full h-full object-cover transition-opacity duration-1000 ${
            videoLoaded ? 'opacity-70' : 'opacity-0'
          }`}
        />
      )}

      {/* Lightweight Ambient Fallback Backdrop (Renders when MP4 is missing or loading) */}
      {(videoError || !videoLoaded) && (
        <div className="absolute inset-0 w-full h-full bg-gradient-to-b from-[#090D16] via-[#0D1527] to-[#0B0F19]">
          {/* Subtle Ambient Mesh Orbs */}
          {!shouldReduceMotion && (
            <>
              <div className="absolute top-1/4 left-1/3 w-96 h-96 rounded-full bg-[var(--teal-600)]/15 blur-3xl animate-pulse duration-[8000ms]" />
              <div className="absolute bottom-1/3 right-1/4 w-[30rem] h-[30rem] rounded-full bg-[var(--blue-600)]/10 blur-3xl animate-pulse duration-[10000ms]" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[40rem] h-[40rem] rounded-full bg-[var(--purple-600)]/05 blur-3xl" />
            </>
          )}

          {/* Grid pattern overlay */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:4rem_4rem]" />
        </div>
      )}

      {/* Subtle Vignette & Gradient Mask for Reading Legibility */}
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/60 via-slate-950/20 to-[#0B0F19]" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_40%,rgba(9,13,22,0.8)_100%)]" />
    </div>
  );
};
