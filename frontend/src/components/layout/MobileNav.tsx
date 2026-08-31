import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { clsx } from 'clsx';
import { LayoutDashboard, Building2, Map, TrendingUp, ShieldCheck, X, LogOut, LogIn } from 'lucide-react';
import { useAuth } from '../../auth/AuthContext';

export interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({ isOpen, onClose }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const shouldReduceMotion = useReducedMotion();
  const { user, isAuthenticated, logout } = useAuth();

  const handleLogout = async () => {
    onClose();
    await logout();
    navigate('/login');
  };

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

              {isAuthenticated && user && (
                <div className="mb-6 p-3 bg-stone-100/80 rounded-xl border border-stone-200/80 flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-[#0F4C81] text-white flex items-center justify-center font-bold text-xs">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-semibold text-stone-900">{user.username}</span>
                    <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider">{user.role}</span>
                  </div>
                </div>
              )}

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

            <div className="border-t border-[var(--border-subtle)] pt-4 flex flex-col gap-3">
              {isAuthenticated ? (
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold text-red-700 bg-red-50 border border-red-200 hover:bg-red-100 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              ) : (
                <NavLink
                  to="/login"
                  onClick={onClose}
                  className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold text-white bg-[#0F4C81] hover:bg-[#0A3459] transition-colors"
                >
                  <LogIn className="w-4 h-4" />
                  <span>Terminal Login</span>
                </NavLink>
              )}
              <div className="text-[11px] text-[var(--text-muted)] text-center">
                CAREFlow India Healthcare Platform v0.1.0
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
