# Roadmap

## v0.1.0 — Core CLI (done)

- CSV import, website audit, transparent opportunity scoring
- CSV / JSON / Markdown export
- SQLite local storage, no external services required
- Test suite + CI (Linux/macOS/Windows × Python 3.10–3.12)

## v0.2.0 — Backend API (done)

- FastAPI service exposing the same `leadforge` core modules over REST
- Endpoints for business CRUD/import, per-business and batch audit, per-business and batch scoring, ranked lead listing, CSV/JSON/Markdown export, and dashboard-style stats
- Interactive docs at `/docs` (OpenAPI)
- 42 endpoint tests (FastAPI TestClient, fully mocked/offline) alongside the original 14 core tests

## v0.3.0 — Dashboard (done)

- Next.js 16 App Router, static export (`output: 'export'`) — deployable to GitHub Pages (with `NEXT_PUBLIC_BASE_PATH` for project subpaths), Vercel, Netlify, or any static host
- Installable PWA: web manifest, generated icon set, a stale-while-revalidate service worker that caches the app shell for offline use but never caches API responses
- Runtime-configurable API URL (Settings page, localStorage) — no server URL baked into the build
- Dashboard (stats + batch audit/score actions), Businesses (filterable table with per-row actions), Leads (ranked list, tier/score filters, expandable score reasons and audit issues, CSV/JSON/Markdown export), Import (drag-and-drop CSV), Settings (API URL + live connection test)
- Dark-mode-first theming via CSS custom properties, with a light mode toggle
- `scripts/integration-check.ts`: runs the real `lib/api.ts` against a live backend, wired into CI on all three OSes
- Zero `npm audit` vulnerabilities; `tsc --noEmit` and `eslint` both clean

## v0.4.0 — Plugin system

- Documented plugin API for custom scoring rules, industry packs, and audit checks
- Community plugin registry

## v0.5.0 — Reporting & AI assist

- Branded PDF report generation
- Opt-in AI-generated recommendation text (bring your own API key; never required)

## Later

- Saved searches, richer charting
- PostgreSQL as an optional backend alongside SQLite
- Background job queue for large batch audits (replacing the current synchronous `/audits/run`)
- Desktop app (Tauri)
- i18n (Spanish, French, Portuguese, Hindi, Arabic)
- Revenue estimator refinements based on community-contributed pricing data
