import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { motion, useReducedMotion } from 'framer-motion';
import { Activity, Search, Menu, X, User, Server } from 'lucide-react';
import { api } from '../../api/client';
import type { SystemHealth } from '../../api/types';

export interface TopNavProps {
  onMobileMenuToggle: () => void;
  isMobileMenuOpen: boolean;
}

export const TopNav: React.FC<TopNavProps> = ({ onMobileMenuToggle, isMobileMenuOpen }) => {
  const location = useLocation();
  const shouldReduceMotion = useReducedMotion();
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isHealthLoading, setIsHealthLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;
    api.getHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setIsHealthLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealth(null);
          setIsHealthLoading(false);
        }
      });
    return () => { isMounted = false; };
  }, []);

  const navLinks = [
    { label: 'Overview', path: '/overview' },
    { label: 'Facilities', path: '/facilities' },
    { label: 'Regions', path: '/regions' },
    { label: 'Forecast', path: '/forecast' },
    { label: 'Data Quality', path: '/data-quality' },
  ];

  return (
    <header className="sticky top-0 z-30 w-full bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] shadow-xs transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo & Tag */}
        <div className="flex items-center gap-6">
          <NavLink to="/overview" className="flex items-center gap-2.5 group focus-ring rounded-lg p-1">
            <motion.div
              whileHover={shouldReduceMotion ? undefined : { scale: 1.06, rotate: 3 }}
              whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
              className="w-9 h-9 rounded-lg bg-gradient-to-br from-[var(--teal-600)] to-[var(--teal-700)] text-white flex items-center justify-center shadow-xs"
            >
              <Activity className="w-5 h-5" />
            </motion.div>
            <div className="flex flex-col">
              <span className="font-display font-extrabold text-lg tracking-tight text-[var(--text-primary)] leading-none group-hover:text-[var(--teal-600)] transition-colors">
                CAREFlow
              </span>
              <span className="text-[10px] font-bold tracking-widest text-[var(--text-muted)] uppercase mt-0.5">
                India Platform
              </span>
            </div>
          </NavLink>

          {/* Primary Navigation Links (Desktop) */}
          <nav className="hidden md:flex items-center gap-1 ml-4" aria-label="Primary Navigation">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path || (link.path === '/overview' && location.pathname === '/');
              return (
                <NavLink
                  key={link.path}
                  to={link.path}
                  className={clsx(
                    'relative px-3.5 py-2 text-sm font-medium rounded-md transition-all duration-200 focus-ring cursor-pointer',
                    isActive
                      ? 'text-[var(--teal-700)] font-semibold bg-[var(--teal-50)]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-subtle)]'
                  )}
                >
                  {link.label}
                  {isActive && (
                    <motion.span
                      layoutId={shouldReduceMotion ? undefined : 'topNavActiveIndicator'}
                      className="absolute bottom-0 left-2 right-2 h-0.5 bg-[var(--teal-600)] rounded-full"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Right Section: API Health Indicator, Search, Profile */}
        <div className="flex items-center gap-3">
          {/* Backend API Health Status Indicator */}
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)]">
            <span className={clsx('w-2 h-2 rounded-full animate-pulse', health?.status === 'healthy' ? 'bg-[var(--green-500)]' : 'bg-[var(--amber-500)]')} />
            <Server className="w-3.5 h-3.5 text-[var(--text-muted)]" />
            <span className="text-[var(--text-secondary)]">
              {isHealthLoading ? 'Pinging API...' : health?.status === 'healthy' ? 'API Connected' : 'Demo Mode'}
            </span>
          </div>

          {/* Search Input Bar (Preview) */}
          <div className="hidden lg:flex items-center relative">
            <Search className="w-4 h-4 text-[var(--text-muted)] absolute left-3 pointer-events-none" />
            <input
              type="text"
              placeholder="Search facility or region..."
              className="pl-9 pr-4 py-1.5 text-xs bg-[var(--bg-surface-subtle)] border border-[var(--border-subtle)] rounded-full w-48 focus:w-64 focus:bg-[var(--bg-surface)] focus:border-[var(--teal-600)] text-[var(--text-primary)] transition-all duration-300 focus-ring"
            />
          </div>

          {/* User / Profile Avatar Button */}
          <motion.button
            whileHover={shouldReduceMotion ? undefined : { scale: 1.05 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
            className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-subtle)] rounded-full transition-colors cursor-pointer focus-ring"
            title="User Profile"
          >
            <User className="w-4 h-4" />
          </motion.button>

          {/* Mobile Menu Toggle Button */}
          <motion.button
            whileTap={shouldReduceMotion ? undefined : { scale: 0.95 }}
            onClick={onMobileMenuToggle}
            className="md:hidden p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-subtle)] rounded-lg transition-colors cursor-pointer focus-ring"
            aria-label="Toggle mobile menu"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </motion.button>
        </div>
      </div>
    </header>
  );
};
