/**
 * The dashboard's signature element: a 5-segment "signal strength"
 * meter, styled like an instrument readout rather than a star rating.
 * It reads the same opportunity_score every table and card uses, so a
 * business's flag strength is recognizable at a glance across the app.
 */
export function ScoreMeter({
  score,
  stars,
  size = 'md',
}: {
  score: number;
  stars: number;
  size?: 'sm' | 'md';
}) {
  const segments = [1, 2, 3, 4, 5];
  const barWidth = size === 'sm' ? 'w-1' : 'w-1.5';
  const gap = size === 'sm' ? 'gap-0.5' : 'gap-1';

  return (
    <div
      className={`inline-flex items-end ${gap}`}
      role="img"
      aria-label={`Opportunity signal: ${score} out of 100, ${stars} of 5 bars filled`}
      title={`${score}/100`}
    >
      {segments.map((seg) => {
        const filled = seg <= stars;
        return (
          <span
            key={seg}
            className={`${barWidth} rounded-sm ${filled ? 'bg-signal' : 'bg-edge'}`}
            style={{ height: `${(size === 'sm' ? 6 : 8) + seg * (size === 'sm' ? 1.5 : 2)}px` }}
            aria-hidden="true"
          />
        );
      })}
      <span className="ml-1.5 font-data text-xs text-fg-muted tabular-nums">{score}</span>
    </div>
  );
}
