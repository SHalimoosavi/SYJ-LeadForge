export function StatCard({
  label,
  value,
  hint,
  accent = 'default',
}: {
  label: string;
  value: string | number;
  hint?: string;
  accent?: 'default' | 'signal' | 'circuit';
}) {
  const valueColor =
    accent === 'signal' ? 'text-signal' : accent === 'circuit' ? 'text-circuit' : 'text-fg';

  return (
    <div className="plate relative p-4 pt-5">
      <span className="absolute top-0 left-4 -translate-y-1/2 bg-surface-2 px-1.5 eyebrow border border-edge rounded-sm">
        {label}
      </span>
      <div className={`font-data text-3xl font-semibold tabular-nums ${valueColor}`}>{value}</div>
      {hint && <div className="mt-1 text-xs text-fg-muted">{hint}</div>}
    </div>
  );
}
