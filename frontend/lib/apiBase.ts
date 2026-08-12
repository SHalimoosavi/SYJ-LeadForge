/**
 * Where the dashboard finds the SYJ LeadForge API. This is a static
 * export with no build-time knowledge of where the API will be hosted
 * (localhost during development, a self-hosted box, a tunnel, etc.), so
 * the base URL is a runtime setting stored in the browser, editable from
 * the Settings page — not an env var baked into the build.
 */

export const DEFAULT_API_BASE = 'http://127.0.0.1:8000';
const STORAGE_KEY = 'leadforge.apiBase';

export function getStoredApiBase(): string {
  if (typeof window === 'undefined') return DEFAULT_API_BASE;
  try {
    return window.localStorage.getItem(STORAGE_KEY) || DEFAULT_API_BASE;
  } catch {
    // localStorage can throw in locked-down/private-browsing contexts;
    // fall back to the default rather than crashing the app shell.
    return DEFAULT_API_BASE;
  }
}

export function setStoredApiBase(url: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(STORAGE_KEY, url.trim().replace(/\/+$/, ''));
  } catch {
    // Ignore write failures (e.g. storage disabled); the in-memory
    // React state still reflects the change for this session.
  }
}
