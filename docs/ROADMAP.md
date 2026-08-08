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

## v0.3.0 — Dashboard

- Next.js static-export frontend (deployable to GitHub Pages, Vercel, Netlify)
- Installable PWA with offline caching (IndexedDB)
- Charts, saved searches, dark/light mode

## v0.4.0 — Plugin system

- Documented plugin API for custom scoring rules, industry packs, and audit checks
- Community plugin registry

## v0.5.0 — Reporting & AI assist

- Branded PDF report generation
- Opt-in AI-generated recommendation text (bring your own API key; never required)

## Later

- PostgreSQL as an optional backend alongside SQLite
- Background job queue for large batch audits (replacing the current synchronous `/audits/run`)
- Desktop app (Tauri)
- i18n (Spanish, French, Portuguese, Hindi, Arabic)
- Revenue estimator refinements based on community-contributed pricing data
