import React, { type ButtonHTMLAttributes } from 'react';
import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'icon' | 'destructive';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  isLoading = false,
  leftIcon,
  rightIcon,
  children,
  className,
  disabled,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus-ring cursor-pointer select-none active:scale-[0.98] disabled:opacity-60 disabled:pointer-events-none disabled:transform-none';

  const variantStyles: Record<ButtonVariant, string> = {
    primary: 'bg-[var(--teal-600)] text-white hover:bg-[var(--teal-700)] shadow-sm hover:shadow-md hover:-translate-y-0.5',
    secondary: 'bg-[var(--bg-surface-subtle)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:bg-[var(--bg-surface-hover)] hover:border-[var(--border-default)] shadow-xs hover:-translate-y-0.5',
    ghost: 'bg-transparent text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--text-primary)]',
    icon: 'bg-transparent text-[var(--text-secondary)] hover:bg-[var(--bg-surface-subtle)] hover:text-[var(--teal-600)] rounded-full p-2',
    destructive: 'bg-[var(--coral-600)] text-white hover:bg-[var(--coral-700)] shadow-sm hover:-translate-y-0.5',
  };

  const sizeStyles: Record<ButtonSize, string> = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2 gap-2',
    lg: 'text-base px-5 py-2.5 gap-2.5 font-semibold',
  };

  return (
    <button
      className={clsx(
        baseStyles,
        variantStyles[variant],
        variant !== 'icon' && sizeStyles[size],
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : (
        <>
          {leftIcon && <span className="inline-flex transition-transform duration-200 group-hover:-translate-x-0.5">{leftIcon}</span>}
          {children}
          {rightIcon && <span className="inline-flex transition-transform duration-200 group-hover:translate-x-0.5">{rightIcon}</span>}
        </>
      )}
    </button>
  );
};
