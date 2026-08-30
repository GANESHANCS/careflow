import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { LayoutDashboard, Building2, Map, TrendingUp, ShieldCheck, HelpCircle } from 'lucide-react';
import { Tooltip } from '../overlays/Tooltip';

export const SlimRail: React.FC = () => {
  const location = useLocation();

  const railItems = [
    { label: 'Overview', path: '/overview', icon: LayoutDashboard },
    { label: 'Facilities', path: '/facilities', icon: Building2 },
    { label: 'Regions', path: '/regions', icon: Map },
    { label: 'Forecast', path: '/forecast', icon: TrendingUp },
    { label: 'Data Quality', path: '/data-quality', icon: ShieldCheck },
  ];

  return (
    <aside className="hidden md:flex flex-col items-center py-6 w-16 bg-[var(--bg-surface)] border-r border-[var(--border-subtle)] h-[calc(100vh-4rem)] sticky top-16 z-20 select-none">
      <div className="flex-1 flex flex-col items-center gap-4">
        {railItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || (item.path === '/overview' && location.pathname === '/');

          return (
            <Tooltip key={item.path} content={item.label} position="right">
              <NavLink
                to={item.path}
                className={clsx(
                  'relative group p-3 rounded-xl transition-all duration-200 focus-ring cursor-pointer flex items-center justify-center',
                  isActive
                    ? 'bg-[var(--teal-50)] text-[var(--teal-600)] shadow-xs'
                    : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-subtle)]'
                )}
                aria-label={item.label}
              >
                <Icon className={clsx('w-5 h-5 transition-transform duration-200 group-hover:scale-110', isActive && 'text-[var(--teal-600)]')} />
                {isActive && (
                  <span className="absolute left-0 top-2 bottom-2 w-1 bg-[var(--teal-600)] rounded-r-full" />
                )}
              </NavLink>
            </Tooltip>
          );
        })}
      </div>

      <div className="mt-auto">
        <Tooltip content="Documentation & API Specs" position="right">
          <a
            href="/api/docs"
            target="_blank"
            rel="noreferrer"
            className="p-3 text-[var(--text-muted)] hover:text-[var(--teal-600)] hover:bg-[var(--bg-surface-subtle)] rounded-xl transition-colors inline-block focus-ring"
            aria-label="Documentation"
          >
            <HelpCircle className="w-5 h-5" />
          </a>
        </Tooltip>
      </div>
    </aside>
  );
};
