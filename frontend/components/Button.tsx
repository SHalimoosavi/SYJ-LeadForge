'use client';

import { Loader2 } from 'lucide-react';
import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  loading?: boolean;
  icon?: ReactNode;
}

export function Button({
  variant = 'secondary',
  loading = false,
  icon,
  children,
  className = '',
  disabled,
  ...rest
}: ButtonProps) {
  const base =
    'inline-flex items-center justify-center gap-2 rounded px-3.5 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
  const variants: Record<string, string> = {
    primary: 'bg-signal text-ink-950 hover:bg-signal-bright',
    secondary: 'bg-surface-2 border border-edge text-fg hover:border-signal/40 hover:text-signal',
    ghost: 'text-fg-muted hover:text-fg hover:bg-surface-2',
  };

  return (
    <button
      type="button"
      className={`${base} ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading ? <Loader2 size={15} className="animate-spin" /> : icon}
      {children}
    </button>
  );
}
