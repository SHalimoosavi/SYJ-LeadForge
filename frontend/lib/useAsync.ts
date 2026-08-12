'use client';

import { useCallback, useEffect, useState } from 'react';

type AsyncState<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
  refresh: () => void;
};

/**
 * Runs `fn` whenever `deps` change (and on demand via `refresh`),
 * tracking loading/error/data state. Guards against setting state after
 * unmount or after a newer request has already superseded this one.
 */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[], enabled = true): AsyncState<T> {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  useEffect(() => {
    if (!enabled) {
      // Reset loading when a caller disables fetching (e.g. API base not
      // ready yet) after having previously been enabled; `loading` is
      // genuine async state toggled elsewhere in this same effect, not
      // something derivable from `enabled` alone via useMemo.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    fn()
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Something went wrong.');
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick, enabled]);

  return { data, error, loading, refresh };
}
