# SYJ LeadForge

> Find website opportunities. Qualify leads. Grow your freelance business.

SYJ LeadForge is an open-source, MIT-licensed **lead qualification and website audit toolkit** for freelancers, web developers, and agencies. It helps you turn a list of local businesses into a prioritized list of *website opportunities* — businesses with no website, or with a website that's slow, insecure, or hard to use on mobile.

This is **not** a scraper and **not** a spam tool. It works from CSV lists you already have (your own research, CRM exports, or data from sources you're permitted to use), audits each business's *own* public homepage the same way a browser would, and produces a transparent, explainable opportunity score — never a black box.

**Status:** v0.4.0 — the CLI, a FastAPI REST backend, a static Next.js PWA dashboard, and a plugin system, all sharing the same core scoring/audit logic. This is the fourth milestone of a larger roadmap; PDF reports and AI-assisted suggestions described in the original design doc are not built yet.

---

## What it does today

- **Import** — load businesses from a CSV (name, category, city, website, rating, review count, ...).
- **Audit** — fetch each business's homepage and check for HTTPS, valid SSL, a responsive viewport tag, title/meta description, H1, favicon, alt text coverage, WhatsApp/contact links, redirects, and response time.
- **Score** — a transparent, rule-based 0–100 opportunity score, star rating, tier, and an illustrative project-value range, combining "no website" / "poor website" signals with review count and rating.
- **Export** — CSV, JSON, or a Markdown report, filterable by tier or minimum score.
- **List** — a quick table view of all businesses and their latest scores.
- **Doctor** — environment/config sanity check.
- **Plugins** — extend scoring and auditing without forking: industry-specific category weights, custom audit checks, and scoring rules with their own reasons, loaded from a plugin directory or an installed package.
- **REST API** — a FastAPI backend exposing every one of the above over HTTP, with interactive docs at `/docs`, so you can drive LeadForge from a dashboard, script, or another tool.

Everything runs **locally**, stores data in a local SQLite file, and makes no network calls except the one GET request per business you explicitly audit.

## Install

```bash
git clone https://github.com/SHalimoosavi/SYJ-LeadForge.git
cd SYJ-LeadForge
pip install -e ".[dev]"        # CLI only
pip install -e ".[dev,backend]"  # CLI + REST API
```

Requires Python 3.10+. Works on Windows, macOS, Linux, Android (Termux), Docker, and Raspberry Pi — anywhere Python and `pip` run.

## Quick start — CLI

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

## Quick start — REST API

```bash
uvicorn backend.main:app --reload
```

Then open **http://127.0.0.1:8000/docs** for interactive API docs, or:

```bash
# Import a CSV
curl -X POST -F "file=@sample_data/businesses_sample.csv;type=text/csv" \
  http://127.0.0.1:8000/businesses/import

# Score everything
curl -X POST http://127.0.0.1:8000/scores/run

# Get the ranked lead list
curl http://127.0.0.1:8000/leads

# Export as CSV
curl http://127.0.0.1:8000/leads/export/csv -o leads.csv
```

### API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/businesses/import` | Import businesses from an uploaded CSV |
| GET | `/businesses` | List businesses (filter by `category`, `city`) |
| POST | `/businesses` | Create a business manually |
| GET | `/businesses/{id}` | Get one business |
| POST | `/businesses/{id}/audit` | Audit one business's website |
| GET | `/businesses/{id}/audit` | Get the latest audit for a business |
| POST | `/audits/run` | Audit every business that has a website |
| POST | `/businesses/{id}/score` | Score one business |
| GET | `/businesses/{id}/score` | Get the latest score for a business |
| POST | `/scores/run` | Score every business |
| GET | `/leads` | Ranked lead list (filter by `tier`, `min_score`) |
| GET | `/leads/export/{csv\|json\|markdown}` | Download qualified leads |
| GET | `/stats` | Dashboard-style summary (counts, tier breakdown, average score) |
| GET | `/plugins` | List loaded plugins and what they registered |

The API and CLI share the exact same `leadforge/` core modules — no logic is duplicated, so results are always consistent between the two.

## Quick start — Dashboard

A static, installable PWA that talks to the API above — see [`frontend/README.md`](frontend/README.md) for full details.

```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
```

Open **Settings** in the app and point it at your running API (default `http://127.0.0.1:8000`). For production, `npm run build` produces a static `out/` directory deployable to GitHub Pages, Vercel, Netlify, or any static host — no Node.js server needed at runtime.

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

## Plugins

Extend scoring and auditing without forking the project — industry-specific category weights, custom audit checks, and scoring rules with their own point deltas and reasons. See the [Plugin Guide](docs/PLUGIN_GUIDE.md) for the full API, or try an example:

```bash
leadforge doctor                                          # shows your plugin directory ("data dir")
cp plugins/examples/restaurant_pack.py ~/.leadforge/plugins/
leadforge plugins                                          # confirm it loaded
leadforge score                                              # scores now reflect it
```

A plugin is a `.py` file with one `register(registry) -> None` function — no build step, no restart. See [`plugins/README.md`](plugins/README.md) for what ships as examples.

## Configuration

All settings are environment variables (see `leadforge/config.py`), so nothing sensitive or machine-specific is ever hardcoded:

| Variable | Default | Purpose |
|---|---|---|
| `LEADFORGE_HOME` | `~/.leadforge` | Where the local SQLite DB lives |
| `LEADFORGE_TIMEOUT` | `10` | HTTP request timeout (seconds) |
| `LEADFORGE_USER_AGENT` | `SYJLeadForge/0.1 ...` | User-Agent sent when auditing a site |
| `LEADFORGE_MAX_REDIRECTS` | `5` | Max redirects followed during audit |
| `LEADFORGE_DELAY` | `1.0` | Delay between audit requests (seconds), to be a polite, non-spammy client |
| `LEADFORGE_PLUGINS_DIR` | `<LEADFORGE_HOME>/plugins` | Where to load `.py` plugin files from |

## Development

```bash
# CLI + API
pip install -e ".[dev,backend]"
pytest -q                 # 82 tests, all offline/mocked — no network needed
ruff check leadforge backend tests scripts

# Dashboard
cd frontend
npm ci
npm run typecheck && npm run lint && npm run build
```

## Roadmap

The CLI, REST API, dashboard, and plugin system are the foundation. Planned next milestones (see [ROADMAP.md](docs/ROADMAP.md)):

1. PDF report generation
2. AI-assisted recommendation text (opt-in, bring-your-own-API-key)
3. A community plugin registry (searchable index of third-party plugins)

## Principles

This project will never: scrape data without permission, bypass access controls or rate limits, automate unsolicited outreach, or collect personal data beyond what a user explicitly imports. See [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT — see [LICENSE](LICENSE).
