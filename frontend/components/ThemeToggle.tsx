'use client';

import { Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';

const STORAGE_KEY = 'leadforge.theme';

function applyTheme(theme: 'dark' | 'light') {
  document.documentElement.classList.remove('dark', 'light');
  document.documentElement.classList.add(theme);
}

export function ThemeToggle() {
  // Mirrors whatever the inline anti-flash script in layout.tsx already
  // applied to <html> before this component mounts.
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  useEffect(() => {
    // document is unavailable during the static prerender (build time),
    // so this has to run client-side, after mount — reading whatever
    // class the anti-flash script already set, rather than assuming.
    const current = document.documentElement.classList.contains('light') ? 'light' : 'dark';
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(current);
  }, []);

  function toggle() {
    const next = theme === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // Ignore write failures; the visual toggle still applies for this session.
    }
    setTheme(next);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      className="flex h-8 w-8 items-center justify-center rounded border border-edge bg-surface-2 text-fg-muted hover:text-signal hover:border-signal/40 transition-colors"
    >
      {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
    </button>
  );
}
