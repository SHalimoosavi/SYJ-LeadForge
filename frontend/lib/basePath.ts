/**
 * Mirrors the `NEXT_PUBLIC_BASE_PATH` build-time setting from
 * next.config.js. Next.js auto-prefixes `next/link` and `next/image`
 * with `basePath`, but raw string paths (manifest link, service worker
 * registration, icon hrefs) need this applied manually.
 */
export const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || '';

export function withBasePath(path: string): string {
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${BASE_PATH}${normalized}`;
}
