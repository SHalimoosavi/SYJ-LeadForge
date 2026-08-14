"""Hello World — a minimal starting template for SYJ LeadForge plugins.

Copy this file into your plugin directory (see `docs/PLUGIN_GUIDE.md`
for where that is) and edit it, or use it as a reference while writing
your own plugin from scratch. Every hook shown here is optional — use
only the ones you need.

Try it:
    cp plugins/examples/hello_world.py "$(leadforge doctor | grep 'data dir' | awk '{print $3}')/plugins/"
    leadforge plugins
"""
from __future__ import annotations

from leadforge.plugins import AuditCheckContext, PluginRegistry, ScoreAdjustment, ScoringContext


def register(registry: PluginRegistry) -> None:
    """Every plugin must define exactly this function. It's called once,
    when the plugin loads, with a registry to add things to."""

    # 1. Add or override a category weight. Weight is a multiplier on the
    #    opportunity score (and it widens the suggested price range too):
    #    a weight of 1.0 is neutral, 1.5 means "prioritize this category."
    registry.add_category_weight("example category", 1.2)

    # 2. Exclude a category entirely — it will always score 0, exactly
    #    like the built-in tea-stall/street-vendor exclusions.
    # registry.exclude_category("example low-value category")

    # 3. Add an audit check: inspect the fetched page and return a list
    #    of extra issue strings (or an empty list if nothing to report).
    registry.add_audit_check(check_for_example_marker)

    # 4. Add a scoring rule: nudge the score up or down with a reason.
    registry.add_scoring_rule(example_scoring_rule)


def check_for_example_marker(context: AuditCheckContext) -> list[str]:
    """Audit checks receive the business (if known), the URL, the raw
    HTML (if the page was reachable), and the AuditResult computed so
    far. Return extra issue strings; return [] if nothing to flag."""
    if context.html and "example-marker" not in context.html.lower():
        return ["Example: missing the 'example-marker' this plugin looks for"]
    return []


def example_scoring_rule(context: ScoringContext) -> ScoreAdjustment:
    """Scoring rules receive the business, its latest audit (or None),
    and the core score computed so far. Return a ScoreAdjustment with a
    point delta (can be negative) and any reason strings to append."""
    if context.business.category.strip().lower() == "example category":
        return ScoreAdjustment(delta=5, reasons=["Example plugin: bonus for matching category"])
    return ScoreAdjustment()
