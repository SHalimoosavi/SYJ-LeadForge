# Architecture

## Current (v0.1.0)

```
leadforge/
├── __init__.py      # package version
├── cli.py           # argparse-based CLI: import, audit, score, export, list, doctor
├── config.py         # Settings, env-var overrides, default weights/exclusions
├── models.py         # Business, AuditResult, LeadScore dataclasses
├── db.py             # SQLite persistence (Store class)
├── importer.py        # CSV -> Business parsing & normalization
├── audit.py           # HTTP fetch + stdlib-only HTML analysis + sub-scoring
├── scoring.py          # Business + AuditResult -> LeadScore
└── term.py             # Cross-platform-safe console output (see below)
```

### Cross-platform console output

Windows consoles (`cmd.exe`, older PowerShell hosts) and some CI runners
often report a non-UTF-8 encoding (`cp1252`, `cp437`) that cannot
represent characters like `★` or `—`, which raises `UnicodeEncodeError`
on a plain `print()`. All console output in the CLI goes through
`leadforge/term.py` instead of calling `print()` directly:

- `supports_unicode(stream)` — detects, by actually attempting to
  encode, whether the target stream can safely emit the symbols this
  CLI uses.
- `stars(count)` / `format_symbol(symbol)` — return the Unicode glyph on
  capable terminals, or an ASCII-equivalent fallback (`*`, `-`, `OK`,
  `X`, ...) otherwise.
- `safe_print(...)` — a drop-in `print()` replacement that never raises
  `UnicodeEncodeError`: it tries full Unicode first, falls back to
  ASCII-equivalent text for known symbols, and as a last resort
  replaces any remaining unencodable characters (e.g. an accented
  business name from an imported CSV on a strict-ASCII console) rather
  than crashing the run.

File output (CSV/JSON/Markdown exports) is unaffected by any of this:
those are already written with explicit `encoding="utf-8"`, so exported
files retain full Unicode fidelity regardless of console encoding.

Data flow:

```
CSV file --import--> SQLite (businesses)
SQLite businesses --audit--> SQLite (audits, keyed by business_id)
SQLite businesses + latest audit --score--> SQLite (scores)
SQLite businesses + latest score + latest audit --export--> CSV/JSON/Markdown
```

Design choices:

- **SQLite by default** — zero setup, works identically on Windows/macOS/Linux/Termux.
- **Stdlib HTML parsing** (`html.parser.HTMLParser`) instead of BeautifulSoup — keeps the dependency surface tiny (`requests` is the only runtime dependency) and audits stay fast on low-end devices (e.g. Raspberry Pi).
- **One HTTP GET per audited business** — no crawling, no following internal links, no bypassing robots.txt-style restrictions, and a configurable delay between requests.
- **Every score is explainable** — `LeadScore.reasons` always lists the concrete signals that produced the number.

## Backend (v0.2.0)

```
backend/
├── main.py            # FastAPI app, CORS, router wiring, /health
├── dependencies.py     # StoreDep — Annotated dependency-injection for the SQLite Store
├── schemas.py          # Pydantic response/request models mirroring leadforge.models
└── routers/
    ├── businesses.py    # CRUD + CSV import
    ├── audits.py         # per-business and batch website audit
    ├── scores.py          # per-business and batch opportunity scoring
    └── leads.py            # ranked lead list, CSV/JSON/Markdown export, stats
```

The backend does not reimplement import, audit, or scoring logic — every
route calls straight into `leadforge.importer`, `leadforge.audit`, and
`leadforge.scoring`, the same functions `leadforge/cli.py` calls. A
request is handled by opening a fresh `Store` (SQLite connection) per
request via `get_settings()`, so `LEADFORGE_HOME` continues to be the
single source of truth for where data lives, in both the CLI and the API.

## Dashboard (v0.3.0)

```
frontend/
├── app/                     # Next.js App Router pages
│   ├── layout.tsx             # Root layout: metadata, anti-flash theme script, manifest/icon links
│   ├── globals.css              # Design tokens as CSS custom properties (see design note inline)
│   ├── page.tsx                  # Dashboard: stats + batch audit/score actions
│   ├── businesses/page.tsx        # Filterable business table, per-row audit/score
│   ├── leads/page.tsx              # Ranked lead list, tier/score filters, export
│   ├── import/page.tsx              # CSV upload
│   └── settings/page.tsx             # API URL config + connection test
├── components/               # Shell (nav/topbar), ScoreMeter, TierBadge, StateBlocks, ...
├── lib/
│   ├── api.ts                  # Typed fetch client — single source of truth for the API contract
│   ├── types.ts                  # Mirrors backend/schemas.py field-for-field
│   ├── apiBase.ts / useApiBase.ts   # Runtime-configurable API URL (localStorage), not build-time
│   └── useAsync.ts                    # Shared loading/error/data fetching hook
├── public/{manifest.json,sw.js,icons/}   # PWA assets
└── scripts/integration-check.ts            # Runs the real lib/api.ts against a live backend
```

Key decisions:

- **Static export (`output: 'export'`), not SSR.** No Node.js server at runtime — deployable to GitHub Pages, Vercel, Netlify, or any static host. All data fetching happens client-side against a runtime-configured API URL (see Settings), since a static export can't know at build time where its API will be hosted.
- **No dynamic route segments.** Business/lead detail is shown via expandable rows instead of `/leads/[id]` pages, avoiding the `generateStaticParams` complexity a fully client-driven detail route would need under static export.
- **CSS-custom-property theming**, not Tailwind `dark:`/`light:` duplication. Semantic tokens (`bg-surface`, `text-fg`, `border-edge`, ...) read CSS variables flipped by a `.dark`/`.light` class on `<html>`, set before paint by an inline script to avoid a flash of the wrong theme.
- **System font stacks, not Google Fonts.** This is an offline-first PWA; nothing in the app shell should depend on a font CDN fetch to render correctly.
- **Service worker caches the app shell only**, never API responses (see `public/sw.js`) — offline means "the app loads," not "you see stale business data as if it were current."
- **`scripts/integration-check.ts`** imports the actual `lib/api.ts` (not a reimplementation) and runs it against a live backend — this is what CI uses to prove the frontend and backend contracts still agree, on every push, across Linux/macOS/Windows.

## Planned (see ROADMAP.md)

Next up: a plugin system for custom scoring rules and industry packs, PDF report generation, and opt-in AI-assisted recommendation text.
