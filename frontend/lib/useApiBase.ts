'use client';

import { useCallback, useEffect, useState } from 'react';
import { DEFAULT_API_BASE, getStoredApiBase, setStoredApiBase } from './apiBase';

/**
 * Reads the API base URL from localStorage on mount (client-only, since
 * this is a statically exported app with no server to read it from) and
 * exposes a setter that persists changes immediately.
 */
export function useApiBase(): {
  apiBase: string;
  setApiBase: (url: string) => void;
  ready: boolean;
} {
  const [apiBase, setApiBaseState] = useState(DEFAULT_API_BASE);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Read localStorage only after mount: this is a static export with
    // no server, so the prerendered HTML always has the default value.
    // Reading synchronously during render would mismatch that prerender
    // and trigger a hydration error; this is the standard fix.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setApiBaseState(getStoredApiBase());
    setReady(true);
  }, []);

  const setApiBase = useCallback((url: string) => {
    const cleaned = url.trim().replace(/\/+$/, '') || DEFAULT_API_BASE;
    setStoredApiBase(cleaned);
    setApiBaseState(cleaned);
  }, []);

  return { apiBase, setApiBase, ready };
}
