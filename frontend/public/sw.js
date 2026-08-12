// SYJ LeadForge service worker.
//
// This app is a static export with no build-time file manifest we can
// wire in without extra tooling, so instead of trying to precache every
// hashed chunk name, this uses a runtime "stale-while-revalidate" cache
// for same-origin GET requests: whatever page/asset you actually visit
// gets cached, and later visits (including offline) serve the cached
// copy immediately while refreshing it in the background when online.
//
// It deliberately never intercepts cross-origin requests — that's where
// the LeadForge API lives, and API responses should always be fresh,
// never served from a stale cache.

const CACHE_NAME = 'leadforge-shell-v1';
const APP_SHELL = ['./', './manifest.json'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(APP_SHELL))
      .catch(() => {
        // Best-effort precache; an offline first install (unlikely, but
        // possible in dev) shouldn't block the worker from installing.
      })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;

  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return; // never cache the API

  event.respondWith(
    caches.open(CACHE_NAME).then(async (cache) => {
      const cached = await cache.match(request);
      const network = fetch(request)
        .then((response) => {
          if (response && response.status === 200) {
            cache.put(request, response.clone());
          }
          return response;
        })
        .catch(() => cached);

      return cached || network;
    })
  );
});
