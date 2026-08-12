# SYJ LeadForge — Dashboard

A static, installable PWA that talks to the [SYJ LeadForge REST API](../backend). Built with Next.js (App Router, static export), TypeScript, and Tailwind CSS — no Node.js server required at runtime, deployable to GitHub Pages, Vercel, Netlify, or any static file host.

## Why static export

This dashboard has no backend of its own. `next build` produces plain HTML/CSS/JS in `out/`; every page fetches data client-side from wherever you point it (see **Settings** in the app, or `NEXT_PUBLIC_BASE_PATH` below). That's what makes it deployable to GitHub Pages: there's no server-side rendering or API routes to host.

## Quick start

```bash
npm install
npm run dev
```

Open http://localhost:3000, then go to **Settings** and point it at your running SYJ LeadForge API (default `http://127.0.0.1:8000` — see the [backend README](../backend) or run `uvicorn backend.main:app --reload` from the repo root).

## Build

```bash
npm run build      # outputs static files to out/
npm run start       # serves out/ locally via `serve`, to sanity-check the export
```

## Deploying to GitHub Pages

GitHub Pages *project* sites (`username.github.io/SYJ-LeadForge/`) serve from a subpath, not the domain root. Set `NEXT_PUBLIC_BASE_PATH` at build time so the app, its manifest, icons, and service worker all resolve correctly under that subpath:

```bash
NEXT_PUBLIC_BASE_PATH=/SYJ-LeadForge npm run build
```

Then publish the contents of `out/` to the `gh-pages` branch (or configure Pages to build from `/frontend/out`). Leave `NEXT_PUBLIC_BASE_PATH` unset for a custom domain, a GitHub Pages *user/org* site, Vercel, or Netlify — those serve from the root already.

## Scripts

| Command | Purpose |
|---|---|
| `npm run dev` | Local dev server with hot reload |
| `npm run build` | Static export to `out/` |
| `npm run start` | Serve `out/` locally (`npx serve`) |
| `npm run lint` | ESLint (flat config, `eslint-config-next`) |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run test:integration` | Runs the **real** `lib/api.ts` against a live backend — see below |

## Verifying against a real backend

`scripts/integration-check.ts` imports the actual frontend API client (not a reimplementation) and exercises it against a running backend: health check, CSV import, scoring, filtering, sorting, CSV export, and both error paths (unreachable server vs. a 404 from the server). This is what CI runs on every push, across Linux/macOS/Windows.

```bash
# terminal 1, from the repo root
LEADFORGE_HOME=/tmp/lf_demo uvicorn backend.main:app --port 8000

# terminal 2
cd frontend
API_BASE=http://127.0.0.1:8000 npm run test:integration
```

## Architecture

```
frontend/
├── app/                  # Next.js App Router pages (Dashboard, Businesses, Leads, Import, Settings)
├── components/            # Shared UI: Shell (nav), ScoreMeter, TierBadge, StateBlocks, ...
├── lib/
│   ├── api.ts              # Typed fetch client — the single source of truth for talking to the API
│   ├── types.ts              # Mirrors backend/schemas.py field-for-field
│   ├── apiBase.ts / useApiBase.ts  # Runtime-configurable API URL (localStorage, not baked into the build)
│   └── useAsync.ts            # Shared data-fetching hook (loading/error/data)
├── public/
│   ├── manifest.json           # PWA manifest
│   ├── sw.js                    # Service worker (stale-while-revalidate app shell, never caches the API)
│   └── icons/                    # Generated icon PNGs
└── scripts/integration-check.ts   # Live backend verification (see above)
```

Design notes (colors, typography, the "field audit console" identity) are documented inline in `app/globals.css` and `tailwind.config.ts`.

## Offline behavior

The service worker caches the app shell (HTML/CSS/JS) for offline use — the dashboard will load with no network at all. It never caches API responses, so business/lead data always requires a live connection to your API; the Settings page's connection indicator reflects this honestly rather than showing stale data as if it were current.
