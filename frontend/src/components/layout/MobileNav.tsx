import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { clsx } from 'clsx';
import { LayoutDashboard, Building2, Map, TrendingUp, ShieldCheck, X } from 'lucide-react';

export interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const shouldReduceMotion = useReducedMotion();

  const navLinks = [
    { label: 'Overview', path: '/overview', icon: LayoutDashboard },
    { label: 'Facilities', path: '/facilities', icon: Building2 },
    { label: 'Regions', path: '/regions', icon: Map },
    { label: 'Forecast', path: '/forecast', icon: TrendingUp },
    { label: 'Data Quality', path: '/data-quality', icon: ShieldCheck },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
          />

          {/* Drawer Menu */}
          <motion.div
            initial={{ x: '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: '-100%' }}
            transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
            className="relative w-4/5 max-w-xs bg-[var(--bg-surface)] h-full p-6 shadow-float flex flex-col justify-between z-10"
          >
            <div>
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4 mb-6">
                <span className="font-display font-bold text-lg text-[var(--text-primary)]">Navigation</span>
                <button
                  onClick={onClose}
                  className="p-1 rounded-full text-[var(--text-muted)] hover:text-[var(--text-primary)] focus-ring"
                  aria-label="Close navigation"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <nav className="flex flex-col gap-2">
                {navLinks.map((item, idx) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path || (item.path === '/overview' && location.pathname === '/');

                  return (
                    <motion.div
                      key={item.path}
                      initial={{ opacity: 0, x: -12 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: shouldReduceMotion ? 0 : 0.05 * idx + 0.1, duration: 0.3 }}
                    >
                      <NavLink
                        to={item.path}
                        onClick={onClose}
                        className={clsx(
                          'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors focus-ring',
                          isActive
                            ? 'bg-[var(--teal-50)] text-[var(--teal-700)] font-semibold'
                            : 'text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)]'
                        )}
                      >
                        <Icon className="w-5 h-5" />
                        <span>{item.label}</span>
                      </NavLink>
                    </motion.div>
                  );
                })}
              </nav>
            </div>

            <div className="border-t border-[var(--border-subtle)] pt-4 text-xs text-[var(--text-muted)]">
              CAREFlow India Healthcare Platform v0.1.0
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
