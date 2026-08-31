import React from 'react';
import { clsx } from 'clsx';
import { ChevronRight } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';

export interface InteractiveHeadingProps {
  title: string;
  subtitle?: string;
  badge?: string;
  badgeColor?: 'teal' | 'blue' | 'purple' | 'green' | 'amber' | 'coral';
  level?: 1 | 2 | 3;
  actionText?: string;
  onActionClick?: () => void;
  className?: string;
}

export const InteractiveHeading: React.FC<InteractiveHeadingProps> = ({
  title,
  subtitle,
  badge,
  badgeColor = 'teal',
  level = 1,
  actionText,
  onActionClick,
  className,
}) => {
  const shouldReduceMotion = useReducedMotion();

  const badgeColors: Record<string, string> = {
    teal: 'bg-[var(--teal-50)] text-[var(--teal-700)] border-[var(--teal-100)]',
    blue: 'bg-[var(--blue-50)] text-[var(--blue-700)] border-[var(--blue-100)]',
    purple: 'bg-[var(--purple-50)] text-[var(--purple-700)] border-[var(--purple-100)]',
    green: 'bg-[var(--green-50)] text-[var(--green-700)] border-[var(--green-100)]',
    amber: 'bg-[var(--amber-50)] text-[var(--amber-700)] border-[var(--amber-100)]',
    coral: 'bg-[var(--coral-50)] text-[var(--coral-700)] border-[var(--coral-100)]',
  };

  const accentColors: Record<string, string> = {
    teal: 'bg-[var(--teal-600)]',
    blue: 'bg-[var(--blue-600)]',
    purple: 'bg-[var(--purple-600)]',
    green: 'bg-[var(--green-600)]',
    amber: 'bg-[var(--amber-600)]',
    coral: 'bg-[var(--coral-600)]',
  };

  const HeadingTag = level === 1 ? 'h1' : level === 2 ? 'h2' : 'h3';

  const sizeClasses = {
    1: 'text-2xl sm:text-3xl font-extrabold tracking-tight',
    2: 'text-xl sm:text-2xl font-bold tracking-tight',
    3: 'text-lg sm:text-xl font-semibold tracking-tight',
  };

  return (
    <div className={clsx('group relative py-1 mb-4 border-b border-[var(--border-subtle)] pb-4 transition-colors duration-300 hover:border-[var(--border-default)]', className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          {badge && (
            <span className={clsx('inline-flex items-center text-xs font-semibold px-2.5 py-0.5 rounded-full border shadow-xs transition-transform duration-300 group-hover:scale-105 group-hover:shadow-sm', badgeColors[badgeColor])}>
              {badge}
            </span>
          )}
          <HeadingTag className={clsx(sizeClasses[level], 'font-display text-[var(--text-primary)] transition-all duration-300 group-hover:tracking-normal group-hover:translate-x-1')}>
            {title}
          </HeadingTag>
        </div>

        {actionText && (
          <motion.button
            whileHover={shouldReduceMotion ? undefined : { x: 2 }}
            whileTap={shouldReduceMotion ? undefined : { scale: 0.98 }}
            onClick={onActionClick}
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[var(--teal-600)] hover:text-[var(--teal-700)] transition-all duration-200 cursor-pointer focus-ring rounded-md px-2 py-1 hover:bg-[var(--teal-50)]"
          >
            <span>{actionText}</span>
            <ChevronRight className="w-3.5 h-3.5 transition-transform duration-200 group-hover:translate-x-1" />
          </motion.button>
        )}
      </div>

      {subtitle && (
        <p className="mt-1.5 text-sm text-[var(--text-secondary)] font-normal leading-relaxed max-w-3xl">
          {subtitle}
        </p>
      )}

      {/* Expanding contextual accent underline on hover */}
      <span className={clsx('absolute bottom-0 left-0 h-[2.5px] w-0 rounded-full transition-all duration-300 ease-out group-hover:w-28', accentColors[badgeColor])} />
    </div>
  );
};
