# SYJ LeadForge

> Find website opportunities. Qualify leads. Grow your freelance business.

SYJ LeadForge is an open-source, MIT-licensed **lead qualification and website audit toolkit** for freelancers, web developers, and agencies. It helps you turn a list of local businesses into a prioritized list of *website opportunities* — businesses with no website, or with a website that's slow, insecure, or hard to use on mobile.

This is **not** a scraper and **not** a spam tool. It works from CSV lists you already have (your own research, CRM exports, or data from sources you're permitted to use), audits each business's *own* public homepage the same way a browser would, and produces a transparent, explainable opportunity score — never a black box.

**Status:** v0.1.0 — a working, tested CLI covering import → audit → score → export. This is the first milestone of a larger roadmap (see below); the web dashboard, plugin system, and AI suggestion modules described in the original design doc are not built yet.

---

## What it does today

- **Import** — load businesses from a CSV (name, category, city, website, rating, review count, ...).
- **Audit** — fetch each business's homepage and check for HTTPS, valid SSL, a responsive viewport tag, title/meta description, H1, favicon, alt text coverage, WhatsApp/contact links, redirects, and response time.
- **Score** — a transparent, rule-based 0–100 opportunity score, star rating, tier, and an illustrative project-value range, combining "no website" / "poor website" signals with review count and rating.
- **Export** — CSV, JSON, or a Markdown report, filterable by tier or minimum score.
- **List** — a quick table view of all businesses and their latest scores.
- **Doctor** — environment/config sanity check.

Everything runs **locally**, stores data in a local SQLite file, and makes no network calls except the one GET request per business you explicitly audit.

## Install

```bash
git clone https://github.com/SHalimoosavi/SYJ-LeadForge.git
cd SYJ-LeadForge
pip install -e ".[dev]"
```

Requires Python 3.10+. Works on Windows, macOS, Linux, Android (Termux), Docker, and Raspberry Pi — anywhere Python and `pip` run.

## Quick start

```bash
# 1. Import a list of businesses you've compiled
leadforge import sample_data/businesses_sample.csv

# 2. Audit their websites (skips businesses with no website)
leadforge audit

# 3. Compute opportunity scores
leadforge score

# 4. See the results
leadforge list

# 5. Export qualified leads
leadforge export csv --out leads.csv
leadforge export markdown --out leads.md --min-score 60
```

## CSV format

Any of these column names are recognized (case-insensitive): `name`/`business_name`, `category`/`type`/`industry`, `city`, `state`, `country`, `phone`, `website`/`url`, `rating`/`stars`, `review_count`/`reviews`, `notes`. Only `name` is required. See [`sample_data/businesses_sample.csv`](sample_data/businesses_sample.csv).

## How scoring works

The scorer is deliberately simple and inspectable (`leadforge/scoring.py`):

- No website → strong opportunity signal.
- Website exists but audits poorly, or is unreachable → still a strong signal, slightly weaker than "no website."
- Rating × review count (log-dampened) scales the estimate — well-reviewed businesses can usually justify a bigger budget.
- A per-category weight multiplier (configurable) reflects that some categories — law firms, clinics, hospitals — typically have higher project budgets.
- Certain low-value categories (tea stalls, street vendors, kiosks, etc.) are excluded by default; this list is configurable, not hardcoded policy.

Every score comes with a `reasons` list explaining exactly why it landed where it did.

## Configuration

All settings are environment variables (see `leadforge/config.py`), so nothing sensitive or machine-specific is ever hardcoded:

| Variable | Default | Purpose |
|---|---|---|
| `LEADFORGE_HOME` | `~/.leadforge` | Where the local SQLite DB lives |
| `LEADFORGE_TIMEOUT` | `10` | HTTP request timeout (seconds) |
| `LEADFORGE_USER_AGENT` | `SYJLeadForge/0.1 ...` | User-Agent sent when auditing a site |
| `LEADFORGE_MAX_REDIRECTS` | `5` | Max redirects followed during audit |
| `LEADFORGE_DELAY` | `1.0` | Delay between audit requests (seconds), to be a polite, non-spammy client |

## Development

```bash
pip install -e ".[dev]"
pytest -q                 # 14 tests, all offline/mocked — no network needed
ruff check leadforge tests
```

## Roadmap

This CLI is the foundation. Planned next milestones (see [ROADMAP.md](docs/ROADMAP.md)):

1. FastAPI backend + REST API over the same core modules
2. Static, installable PWA dashboard (Next.js, exportable to GitHub Pages)
3. Plugin system for custom scoring rules and industry packs
4. PDF report generation
5. AI-assisted recommendation text (opt-in, bring-your-own-API-key)

## Principles

This project will never: scrape data without permission, bypass access controls or rate limits, automate unsolicited outreach, or collect personal data beyond what a user explicitly imports. See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
