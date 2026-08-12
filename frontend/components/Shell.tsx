'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Flag, Gauge, LayoutGrid, Settings, Upload } from 'lucide-react';
import type { ReactNode } from 'react';
import { ConnectionStatus } from './ConnectionStatus';
import { ThemeToggle } from './ThemeToggle';
import { useApiBase } from '@/lib/useApiBase';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: LayoutGrid },
  { href: '/leads/', label: 'Leads', icon: Flag },
  { href: '/businesses/', label: 'Businesses', icon: Gauge },
  { href: '/import/', label: 'Import', icon: Upload },
  { href: '/settings/', label: 'Settings', icon: Settings },
] as const;

export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { apiBase, ready } = useApiBase();

  return (
    <div className="flex min-h-screen">
      <aside className="hidden md:flex w-56 shrink-0 flex-col border-r border-edge bg-surface-2">
        <div className="flex items-center gap-2 px-5 py-5">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-signal/15 text-signal">
            <Flag size={15} strokeWidth={2.5} />
          </span>
          <div>
            <div className="font-display font-semibold text-sm leading-none text-fg">SYJ LeadForge</div>
            <div className="eyebrow mt-1">Console</div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-2 space-y-0.5">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const isActive = href === '/' ? pathname === '/' : pathname?.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2.5 rounded px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-signal/10 text-signal font-medium'
                    : 'text-fg-muted hover:text-fg hover:bg-surface'
                }`}
              >
                <Icon size={16} strokeWidth={isActive ? 2.5 : 2} />
                {label}
              </Link>
            );
          })}
        </nav>

        <div className="px-3 py-4 border-t border-edge">
          <p className="text-[11px] leading-relaxed text-fg-faint px-3">
            Local-first. Your data stays in your own SQLite database unless you export it.
          </p>
        </div>
      </aside>

      <div className="flex flex-1 flex-col min-w-0">
        <header className="flex items-center justify-between gap-3 border-b border-edge bg-surface-2 px-4 md:px-6 py-3">
          <div className="md:hidden flex items-center gap-2">
            <span className="flex h-6 w-6 items-center justify-center rounded bg-signal/15 text-signal">
              <Flag size={13} strokeWidth={2.5} />
            </span>
            <span className="font-display font-semibold text-sm">LeadForge</span>
          </div>
          <div className="hidden md:block" />
          <div className="flex items-center gap-2">
            <ConnectionStatus apiBase={apiBase} ready={ready} />
            <ThemeToggle />
          </div>
        </header>

        <nav className="md:hidden flex overflow-x-auto border-b border-edge bg-surface-2 px-2">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const isActive = href === '/' ? pathname === '/' : pathname?.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-1.5 whitespace-nowrap px-3 py-2.5 text-xs border-b-2 ${
                  isActive ? 'border-signal text-signal' : 'border-transparent text-fg-muted'
                }`}
              >
                <Icon size={14} />
                {label}
              </Link>
            );
          })}
        </nav>

        <main className="flex-1 px-4 md:px-6 py-6 max-w-6xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
