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

## v0.4.0 — Plugin system (done)

- `leadforge/plugins.py`: a `PluginRegistry` with four extension points — category weights, excluded categories, audit checks (extra issue strings from inspecting fetched HTML), and scoring rules (point deltas + reasons, applied after core scoring and re-clamped to 0–100)
- Discovery: installed packages via a `leadforge.plugins` entry-point group, plus `.py` files dropped in `<LEADFORGE_HOME>/plugins/` (or `LEADFORGE_PLUGINS_DIR`) — zero-config for local use, standard entry points for pip-installable packages
- A broken plugin (import error, exception in `register()`, or a raising audit check/scoring rule) is skipped with a logged warning — it never breaks loading of other plugins or the rest of the app
- `leadforge plugins` CLI command and `GET /plugins` API endpoint, both showing what's loaded and what each plugin registered
- Two realistic example industry-pack plugins (`plugins/examples/restaurant_pack.py`, `legal_pack.py`) plus a minimal template (`hello_world.py`), and a full [Plugin Guide](PLUGIN_GUIDE.md)
- 26 new tests (registry loading, error isolation, scoring/audit integration) — 82 backend tests total, all still passing
- A community plugin registry (a searchable index of third-party plugins) is **not** built yet — deferred, see below

## v0.5.0 — Reporting & AI assist

- Branded PDF report generation
- Opt-in AI-generated recommendation text (bring your own API key; never required)

## Later

- Community plugin registry (searchable index of third-party plugins)
- Saved searches, richer charting
- PostgreSQL as an optional backend alongside SQLite
- Background job queue for large batch audits (replacing the current synchronous `/audits/run`)
- Desktop app (Tauri)
- i18n (Spanish, French, Portuguese, Hindi, Arabic)
- Revenue estimator refinements based on community-contributed pricing data
