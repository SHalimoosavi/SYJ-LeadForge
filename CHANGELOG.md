# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [0.3.0] - 2026-08-12

### Added
- **Next.js dashboard** (`frontend/`) — a static, installable PWA talking to the v0.2.0 REST API:
  - Dashboard (stats, tier breakdown chart, batch "audit all"/"score all" actions), Businesses (filterable table, per-row audit/score), Leads (ranked list, tier/min-score filters, expandable score reasons and audit issues, CSV/JSON/Markdown export), Import (drag-and-drop CSV), Settings (runtime-configurable API URL with a live connection test)
  - Static export (`output: 'export'`) — no Node.js server at runtime; deployable to GitHub Pages (`NEXT_PUBLIC_BASE_PATH` for project subpaths), Vercel, Netlify, or any static host
  - Installable PWA: web manifest, a generated icon set (flag/pennant mark), and a service worker that caches the app shell for offline use while never caching API responses
  - Dark-mode-first theming via CSS custom properties (no `dark:`/`light:` class duplication), with a light-mode toggle
  - `scripts/integration-check.ts` — runs the real, unmodified `lib/api.ts` against a live backend (not a reimplementation), wired into CI on Linux/macOS/Windows
- New CI job (`frontend`) — typecheck, lint, static build, and the live backend integration check, on the same OS matrix as the backend job

### Fixed
- The originally pinned `next@14.2.18` had known CVEs (npm audit flagged 1 critical); upgraded to the current patched `next@16.3.0`, keeping React 18 (still a supported peer) to minimize migration risk. Also patched a `postcss` advisory. Result: `npm audit` reports 0 vulnerabilities.
- `next lint` was removed in Next.js 16; migrated to ESLint 9 flat config (`eslint.config.mjs`) calling `eslint-config-next` directly.

### Verified
- `npm run build` (static export), `tsc --noEmit`, and `eslint .` all pass clean
- `npm audit`: 0 vulnerabilities, from a from-scratch `npm ci`
- Live integration check (`npm run test:integration`) against a real running backend: health check, CSV import, batch scoring, filtering, sorting, CSV export, and both error paths (unreachable server vs. 404) — all passed against the actual `lib/api.ts` code, not a mock
- Static export served and curl-tested end-to-end: all 5 routes, `manifest.json`, `sw.js`, icons all 200; unknown routes correctly 404 (not SPA-fallback-faked)

## [0.2.0] - 2026-08-08

### Added
- **FastAPI backend** (`backend/`) exposing the CLI's core modules over REST — no logic duplication, every route calls straight into `leadforge.importer` / `leadforge.audit` / `leadforge.scoring` / `leadforge.exporters`:
  - `POST /businesses/import` — CSV import via file upload
  - `GET/POST /businesses`, `GET /businesses/{id}` — business CRUD, filterable by category/city
  - `POST/GET /businesses/{id}/audit`, `POST /audits/run` — per-business and batch website audits
  - `POST/GET /businesses/{id}/score`, `POST /scores/run` — per-business and batch opportunity scoring
  - `GET /leads` — ranked lead list, filterable by tier/min-score
  - `GET /leads/export/{csv|json|markdown}` — downloadable exports
  - `GET /stats` — dashboard-style summary (tier breakdown, average score)
  - `GET /health` — liveness check; interactive docs auto-served at `/docs`
- New `backend` optional dependency group (`fastapi`, `uvicorn[standard]`, `python-multipart`)
- 42 new endpoint tests (`tests/test_backend_api.py`, `tests/conftest.py`) using FastAPI's TestClient with an isolated temp database per test — 56 tests total, all offline/mocked
- Verified against a real running `uvicorn` server with live `curl` requests end-to-end (import → score → list → export → error cases), not just mocked tests

### Changed
- Dev dependency `httpx` → `httpx2` to eliminate a Starlette test-client deprecation warning
- All FastAPI routes use the modern `Annotated[Type, Depends(...)]` dependency style rather than `Depends()` in argument defaults (fixes real `ruff` `B008` findings, not just suppresses them)

## [0.1.1] - 2026-08-07

### Fixed
- **Windows console crash (`UnicodeEncodeError`)** — the CLI printed Unicode symbols (`★`, `—`) directly, which crashed on Windows `cmd.exe`/legacy PowerShell consoles reporting `cp1252`/`cp437` encoding. Added `leadforge/term.py` with `safe_print`, `stars`, and `format_symbol` helpers that detect console capability and adaptively fall back to ASCII (`*`, `-`) without ever raising. Full Unicode output is preserved on UTF-8-capable terminals. All CLI output now routes through these helpers instead of scattering encoding logic across the codebase.
- Added `tests/test_term.py` (15 tests) simulating UTF-8, cp1252, cp437, and strict-ASCII console encodings.
- CI now runs an additional Windows/Linux/macOS smoke-test pass with `PYTHONIOENCODING=cp1252` forced, to catch regressions of this kind going forward.

## [0.1.0] - 2026-08-06

### Added
- Initial CLI: `leadforge import|audit|score|export|list|doctor`
- CSV importer with flexible column-name aliasing and validation
- Website auditor: HTTPS/SSL validation, viewport/title/meta/H1/favicon detection, alt-text coverage, WhatsApp/contact-link detection, redirect and response-time tracking
- Transparent, explainable 0–100 opportunity scoring with configurable category weights and excluded categories
- CSV, JSON, and Markdown exporters with tier/min-score filters
- SQLite local storage, zero external services required
- Test suite (pytest, fully mocked/offline) + GitHub Actions CI across Linux/macOS/Windows and Python 3.10–3.12
- MIT License, README, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, architecture & roadmap docs
