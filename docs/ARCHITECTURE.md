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
└── scoring.py          # Business + AuditResult -> LeadScore
```

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

## Planned (see ROADMAP.md)

The backend (`FastAPI`) and frontend (`Next.js`) will be added as separate top-level directories (`backend/`, `frontend/`) that import and wrap these same core `leadforge` modules, rather than duplicating logic — the CLI, API, and dashboard should always agree on how a lead is scored.
