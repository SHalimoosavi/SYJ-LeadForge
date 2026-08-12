'use client';

import { useEffect, useState } from 'react';
import { checkHealth } from '@/lib/api';

type Status = 'checking' | 'connected' | 'unreachable';

export function ConnectionStatus({ apiBase, ready }: { apiBase: string; ready: boolean }) {
  const [status, setStatus] = useState<Status>('checking');
  const [version, setVersion] = useState<string | null>(null);

  useEffect(() => {
    if (!ready) return;
    let cancelled = false;

    async function poll() {
      try {
        const health = await checkHealth(apiBase);
        if (!cancelled) {
          setStatus('connected');
          setVersion(health.version);
        }
      } catch {
        if (!cancelled) setStatus('unreachable');
      }
    }

    poll();
    const interval = setInterval(poll, 15000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [apiBase, ready]);

  const dotColor =
    status === 'connected' ? 'bg-circuit' : status === 'unreachable' ? 'bg-alert' : 'bg-fg-faint';
  const label =
    status === 'connected'
      ? `Connected${version ? ` · v${version}` : ''}`
      : status === 'unreachable'
        ? 'Unreachable'
        : 'Checking…';

  return (
    <div
      className="flex items-center gap-2 rounded border border-edge bg-surface-2 px-2.5 py-1.5"
      title={apiBase}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} aria-hidden="true" />
      <span className="font-data text-[11px] text-fg-muted whitespace-nowrap">{label}</span>
    </div>
  );
}
