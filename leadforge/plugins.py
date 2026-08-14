"""SYJ LeadForge plugin system.

A plugin is a small Python module that customizes scoring and auditing
without forking the project. Plugins can:

- Add or override **category weights** (how much a business category
  scales the opportunity score and suggested price range).
- Add **excluded categories** (categories that should always score 0,
  same mechanism as the built-in tea-stall/street-vendor exclusions).
- Register **audit checks**: functions that inspect a fetched page
  (given its URL, raw HTML, and the core `AuditResult`) and return
  extra human-readable issue strings, appended to `AuditResult.issues`.
  Audit checks are informational only — they never touch numeric
  scores directly, keeping "what changed the number" traceable to
  scoring rules alone.
- Register **scoring rules**: functions that see the business, its
  latest audit (if any), and the core `LeadScore`, and return a
  `ScoreAdjustment` (a point delta plus reason strings, e.g. industry
  recommendations or suggested-feature callouts). All registered
  scoring rules run, their deltas sum, the final score is re-clamped
  to 0-100, and stars/tier/estimated value are recomputed from that
  final number — so a business's tier always matches its own score.

A plugin is just a Python file (or an installed package using the
standard `importlib.metadata` entry-points mechanism) exposing a single
function: `register(registry: PluginRegistry) -> None`. See
`docs/PLUGIN_GUIDE.md` and the example plugins in `plugins/examples/`
for a walkthrough.

Discovery order (all are loaded, not "first match wins"):

1. Installed packages declaring an entry point in the
   ``leadforge.plugins`` group (standard for pip-installed plugins).
2. Python files directly inside the plugin directory: `LEADFORGE_PLUGINS_DIR`
   if set, otherwise `<LEADFORGE_HOME>/plugins/` (created automatically,
   empty by default — nothing loads unless you put a file there).

A plugin that fails to import or raises inside `register()` is skipped
with a warning; it never prevents the rest of the app from working,
and it never prevents other plugins from loading.
"""
from __future__ import annotations

import importlib.metadata
import importlib.util
import logging
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import AuditResult, Business, LeadScore

logger = logging.getLogger("leadforge.plugins")

ENTRY_POINT_GROUP = "leadforge.plugins"
PLUGIN_DIR_ENV_VAR = "LEADFORGE_PLUGINS_DIR"


@dataclass
class AuditCheckContext:
    """Passed to each registered audit-check function."""

    business: Business | None
    url: str
    html: str | None
    result: AuditResult


AuditCheckFn = Callable[[AuditCheckContext], list[str]]


@dataclass
class ScoreAdjustment:
    """Returned by a scoring-rule function."""

    delta: int = 0
    reasons: list[str] = field(default_factory=list)


@dataclass
class ScoringContext:
    """Passed to each registered scoring-rule function."""

    business: Business
    audit: AuditResult | None
    score: LeadScore


ScoringRuleFn = Callable[[ScoringContext], ScoreAdjustment]


@dataclass
class LoadedPlugin:
    """Metadata about a successfully loaded plugin, for `leadforge plugins`
    and the `/plugins` API endpoint."""

    name: str
    source: str
    category_weights_added: int = 0
    categories_excluded: int = 0
    audit_checks_added: int = 0
    scoring_rules_added: int = 0


class PluginRegistry:
    """Collects everything registered by loaded plugins."""

    def __init__(self) -> None:
        self.category_weights: dict[str, float] = {}
        self.excluded_categories: set[str] = set()
        self.audit_checks: list[tuple[str, AuditCheckFn]] = []
        self.scoring_rules: list[tuple[str, ScoringRuleFn]] = []
        self.loaded_plugins: list[LoadedPlugin] = []
        self._current_plugin_name = "unknown"
        self._current_counts = {"weights": 0, "excluded": 0, "checks": 0, "rules": 0}

    # -- registration API, called from inside a plugin's register() ----
    def add_category_weight(self, category: str, weight: float) -> None:
        """Set (or override) the score multiplier for a category."""
        self.category_weights[category.strip().lower()] = float(weight)
        self._current_counts["weights"] += 1

    def exclude_category(self, category: str) -> None:
        """Mark a category as always scoring 0 (e.g. a low-value category
        specific to your market that isn't in the built-in default list)."""
        self.excluded_categories.add(category.strip().lower())
        self._current_counts["excluded"] += 1

    def add_audit_check(self, fn: AuditCheckFn) -> None:
        """Register a function that inspects a fetched page and returns
        extra issue strings (a list; return `[]` for no issues found)."""
        self.audit_checks.append((self._current_plugin_name, fn))
        self._current_counts["checks"] += 1

    def add_scoring_rule(self, fn: ScoringRuleFn) -> None:
        """Register a function that returns a `ScoreAdjustment` (a point
        delta and/or reason strings) given a business, its audit, and the
        core score computed so far."""
        self.scoring_rules.append((self._current_plugin_name, fn))
        self._current_counts["rules"] += 1

    # -- discovery / loading --------------------------------------------
    def _begin_plugin(self, name: str) -> None:
        self._current_plugin_name = name
        self._current_counts = {"weights": 0, "excluded": 0, "checks": 0, "rules": 0}

    def _finish_plugin(self, name: str, source: str) -> None:
        self.loaded_plugins.append(
            LoadedPlugin(
                name=name,
                source=source,
                category_weights_added=self._current_counts["weights"],
                categories_excluded=self._current_counts["excluded"],
                audit_checks_added=self._current_counts["checks"],
                scoring_rules_added=self._current_counts["rules"],
            )
        )
        self._current_plugin_name = "unknown"

    def load_entry_point_plugins(self) -> None:
        try:
            eps = importlib.metadata.entry_points(group=ENTRY_POINT_GROUP)
        except Exception as exc:  # pragma: no cover - defensive, environment-dependent
            logger.warning("Could not query plugin entry points: %s", exc)
            return

        for ep in eps:
            self._begin_plugin(ep.name)
            try:
                register_fn = ep.load()
                register_fn(self)
                self._finish_plugin(ep.name, f"entry_point:{ep.value}")
            except Exception as exc:
                logger.warning("Failed to load plugin '%s' (entry point): %s", ep.name, exc)
                self._current_plugin_name = "unknown"

    def load_directory_plugins(self, directory: Path) -> None:
        if not directory.is_dir():
            return

        for path in sorted(directory.glob("*.py")):
            if path.name.startswith("_"):
                continue
            name = path.stem
            self._begin_plugin(name)
            try:
                spec = importlib.util.spec_from_file_location(f"leadforge_plugin_{name}", path)
                if spec is None or spec.loader is None:
                    logger.warning("Could not load plugin file '%s'", path)
                    self._current_plugin_name = "unknown"
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                register_fn = getattr(module, "register", None)
                if register_fn is None:
                    logger.warning("Plugin file '%s' has no register(registry) function; skipping", path)
                    self._current_plugin_name = "unknown"
                    continue
                register_fn(self)
                self._finish_plugin(name, f"file:{path}")
            except Exception as exc:
                logger.warning("Failed to load plugin file '%s': %s", path, exc)
                self._current_plugin_name = "unknown"

    def load_all(self, plugins_dir: Path | None = None) -> None:
        self.load_entry_point_plugins()
        self.load_directory_plugins(plugins_dir or default_plugins_dir())


def default_plugins_dir() -> Path:
    env = os.environ.get(PLUGIN_DIR_ENV_VAR)
    if env:
        return Path(env)
    from .config import get_settings

    directory = get_settings().data_dir / "plugins"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


_registry: PluginRegistry | None = None


def get_registry() -> PluginRegistry:
    """Returns the process-wide plugin registry, loading plugins on first
    use. Cached after the first call — call `reset_registry()` first if
    you need plugins reloaded (e.g. after changing `LEADFORGE_PLUGINS_DIR`
    or in tests)."""
    global _registry
    if _registry is None:
        _registry = PluginRegistry()
        _registry.load_all()
    return _registry


def reset_registry() -> None:
    """Clears the cached global registry so the next `get_registry()`
    call reloads plugins from scratch. Mainly useful for tests."""
    global _registry
    _registry = None
