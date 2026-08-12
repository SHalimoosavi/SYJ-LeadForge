import type { Tier } from '@/lib/types';

const TIER_STYLES: Record<Tier, string> = {
  'Very High': 'bg-signal/15 text-signal-bright border-signal/40',
  High: 'bg-signal/10 text-signal border-signal/30',
  Medium: 'bg-circuit/10 text-circuit border-circuit/30',
  Low: 'bg-fg-faint/10 text-fg-muted border-edge',
  'Very Low': 'bg-fg-faint/10 text-fg-faint border-edge',
  Excluded: 'bg-alert/10 text-alert border-alert/30',
};

export function TierBadge({ tier }: { tier: Tier | string }) {
  const style = TIER_STYLES[tier as Tier] ?? TIER_STYLES.Low;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded border font-data text-[11px] uppercase tracking-wide ${style}`}
    >
      {tier}
    </span>
  );
}
