import { TIER_ORDER, type Tier } from '@/lib/types';

const TIER_BAR_COLOR: Record<Tier, string> = {
  'Very High': 'bg-signal',
  High: 'bg-signal/70',
  Medium: 'bg-circuit',
  Low: 'bg-fg-faint',
  'Very Low': 'bg-fg-faint/60',
  Excluded: 'bg-alert/60',
};

export function TierBreakdownChart({ breakdown }: { breakdown: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(breakdown));

  return (
    <div className="space-y-2.5">
      {TIER_ORDER.map((tier) => {
        const count = breakdown[tier] ?? 0;
        const pct = Math.round((count / max) * 100);
        return (
          <div key={tier} className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-xs text-fg-muted text-right">{tier}</span>
            <div className="flex-1 h-4 rounded bg-surface overflow-hidden border border-edge">
              <div
                className={`h-full rounded ${TIER_BAR_COLOR[tier]}`}
                style={{ width: count > 0 ? `${Math.max(pct, 4)}%` : '0%' }}
              />
            </div>
            <span className="w-6 shrink-0 font-data text-xs text-fg tabular-nums">{count}</span>
          </div>
        );
      })}
    </div>
  );
}
