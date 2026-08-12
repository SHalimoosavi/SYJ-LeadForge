'use client';

import { useEffect } from 'react';
import { withBasePath } from '@/lib/basePath';

export function ServiceWorkerRegister() {
  useEffect(() => {
    if (typeof window === 'undefined' || !('serviceWorker' in navigator)) return;
    // Registered relative to basePath so this also works when the app is
    // deployed under a GitHub Pages project subpath.
    navigator.serviceWorker.register(withBasePath('/sw.js')).catch(() => {
      // Offline caching is a progressive enhancement; a failed
      // registration (e.g. unsupported browser, dev server quirks)
      // should never block the app from working online.
    });
  }, []);

  return null;
}
