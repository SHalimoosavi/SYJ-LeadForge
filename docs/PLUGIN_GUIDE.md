# Plugin Guide

SYJ LeadForge's scoring and auditing logic is intentionally simple and
transparent — but every market, industry, and freelancer has different
priorities. Plugins let you customize that behavior without forking the
project or editing its source.

A plugin can:

- Add or override **category weights** — how much a business category
  scales the opportunity score and the suggested price range.
- Add **excluded categories** — categories that should always score 0,
  using the same mechanism as the built-in tea-stall/street-vendor list.
- Register **audit checks** — inspect a fetched page's HTML and flag
  additional issues (e.g. "no online ordering platform detected").
- Register **scoring rules** — nudge a business's final score up or
  down with your own reasoning, which shows up right alongside the
  built-in reasons in `leadforge list`, exports, and the API.

Everything a plugin does is visible and explainable: run `leadforge
plugins` to see what's loaded and what it registered, and every score
adjustment comes with a reason string, never a silent number change.

## Where plugins live

Run `leadforge doctor` to see your **data dir**. Your plugin directory
is `<data dir>/plugins/` — created automatically, empty by default (so
nothing changes until you add something). Override the location with:

```bash
export LEADFORGE_PLUGINS_DIR=/path/to/your/plugins
```

Drop a `.py` file in there. That's it — no installation step, no
restart needed beyond your next `leadforge` command (the CLI and each
API request load plugins fresh at startup).

For plugins you want to install via `pip` and share as a package, see
[Entry-point plugins](#entry-point-plugins-pip-installable) below.

## Writing a plugin

Every plugin file needs exactly one function:

```python
def register(registry):
    ...
```

It's called once, when the plugin loads, with a `PluginRegistry` you
add things to. Copy [`plugins/examples/hello_world.py`](../plugins/examples/hello_world.py)
as a starting point — it demonstrates every hook with comments.

### Category weights

```python
def register(registry):
    registry.add_category_weight("wedding photographer", 1.3)
```

A weight of `1.0` is neutral (the default for any category not in the
built-in list or a plugin). Higher values increase both the opportunity
score and the suggested price range for that category; lower values
(e.g. `0.8`) do the opposite. If your plugin sets a weight for a
category the built-in list already covers, your value wins.

### Excluded categories

```python
def register(registry):
    registry.exclude_category("home-based hobby business")
```

Businesses in an excluded category always score `0` with tier
`"Excluded"` — same as the built-in tea-stall/street-vendor list. Use
this for categories that are low-value in *your* market specifically,
rather than editing the built-in defaults.

### Audit checks

```python
from leadforge.plugins import AuditCheckContext

def register(registry):
    registry.add_audit_check(check_for_booking_widget)

def check_for_booking_widget(context: AuditCheckContext) -> list[str]:
    if context.html and "calendly.com" not in context.html.lower():
        return ["No booking widget (e.g. Calendly) detected"]
    return []
```

An audit check receives an `AuditCheckContext` with:

| Field | Type | Notes |
|---|---|---|
| `business` | `Business \| None` | The business being audited, if known |
| `url` | `str` | The URL that was fetched |
| `html` | `str \| None` | The raw HTML, if the page was reachable |
| `result` | `AuditResult` | The core audit result computed so far (read-only in practice — see note below) |

Return a list of extra issue strings (or `[]`). They're appended to
`AuditResult.issues` — deduplicated, so returning the same string twice
across plugins only shows once.

**Audit checks are informational only** — they don't change any numeric
score directly. This keeps "what changed the number" traceable to
scoring rules alone. If you want an audit finding to affect the score,
check `context.audit.issues` for it inside a scoring rule (see the
`restaurant_pack.py` and `legal_pack.py` examples, which do exactly this).

### Scoring rules

```python
from leadforge.plugins import ScoringContext, ScoreAdjustment

def register(registry):
    registry.add_scoring_rule(bonus_for_high_review_count)

def bonus_for_high_review_count(context: ScoringContext) -> ScoreAdjustment:
    if context.business.review_count >= 500:
        return ScoreAdjustment(delta=5, reasons=["500+ reviews — exceptionally high visibility"])
    return ScoreAdjustment()
```

A scoring rule receives a `ScoringContext` with `business`, `audit`
(`AuditResult | None`), and `score` (the core `LeadScore` computed so
far), and returns a `ScoreAdjustment(delta, reasons)`. All registered
rules run; their `delta`s sum together, the final score is re-clamped
to 0–100, and `stars`/`tier`/`estimated_value_low`/`estimated_value_high`
are all recomputed from that final number — so a business's tier always
matches its own score, even with several plugins active at once.

Excluded-category businesses never reach scoring rules (they short-circuit
to score `0` before rules run, same as the built-in exclusion logic).

## Error isolation

A plugin that fails to import, or whose `register()` raises, is skipped
with a logged warning — it never breaks loading of other plugins or the
rest of the app. Likewise, if an individual audit check or scoring rule
raises when called, that one call is skipped (also logged) and everyone
else's checks/rules still run. You'll never lose a whole `leadforge
score` run because of one buggy plugin.

## Entry-point plugins (pip-installable)

To ship a plugin as an installable package (so others can `pip install
your-plugin-name` instead of copying a file), declare an entry point in
the `leadforge.plugins` group. With `pyproject.toml`:

```toml
[project.entry-points."leadforge.plugins"]
my_plugin = "my_plugin_package.plugin:register"
```

`my_plugin_package/plugin.py` just needs the same `register(registry)`
function described above. Once installed in the same environment as
`leadforge`, it loads automatically — no directory copying needed.

## Debugging

```bash
leadforge plugins
```

Lists every loaded plugin, its source (file path or entry point), and
counts of what it registered. If a plugin didn't load, check `leadforge
plugins` output plus your terminal for a `leadforge.plugins` warning
log line explaining why.

The REST API exposes the same information at `GET /plugins` (see the
[backend README](../backend) / OpenAPI docs at `/docs`).
