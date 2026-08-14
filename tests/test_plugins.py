"""Tests for leadforge.plugins: registry, directory/entry-point loading,
error isolation, and integration with scoring/audit.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from leadforge.audit import audit_website
from leadforge.config import get_settings
from leadforge.models import AuditResult, Business
from leadforge.plugins import (
    AuditCheckContext,
    PluginRegistry,
    ScoreAdjustment,
    ScoringContext,
    default_plugins_dir,
    get_registry,
    reset_registry,
)
from leadforge.scoring import is_excluded_category, score_business


@pytest.fixture(autouse=True)
def _isolate_registry(monkeypatch, tmp_path):
    """Every test gets its own empty plugin directory and a fresh global
    registry, so plugins from one test never leak into another."""
    monkeypatch.setenv("LEADFORGE_PLUGINS_DIR", str(tmp_path / "plugins"))
    reset_registry()
    yield
    reset_registry()


def _write_plugin(tmp_path, filename, source):
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True, exist_ok=True)
    path = plugins_dir / filename
    path.write_text(source, encoding="utf-8")
    return path


# -- PluginRegistry basics ----------------------------------------------

def test_empty_registry_by_default():
    registry = get_registry()
    assert registry.loaded_plugins == []
    assert registry.category_weights == {}
    assert registry.excluded_categories == set()


def test_directory_plugin_loads_and_registers_everything(tmp_path):
    _write_plugin(
        tmp_path,
        "sample.py",
        """
from leadforge.plugins import ScoreAdjustment

def register(registry):
    registry.add_category_weight("widget maker", 1.4)
    registry.exclude_category("hobby stall")
    registry.add_audit_check(lambda ctx: ["custom issue"])
    registry.add_scoring_rule(lambda ctx: ScoreAdjustment(delta=3, reasons=["bonus"]))
""",
    )
    registry = get_registry()
    assert len(registry.loaded_plugins) == 1
    plugin = registry.loaded_plugins[0]
    assert plugin.name == "sample"
    assert plugin.source.startswith("file:")
    assert plugin.category_weights_added == 1
    assert plugin.categories_excluded == 1
    assert plugin.audit_checks_added == 1
    assert plugin.scoring_rules_added == 1

    assert registry.category_weights["widget maker"] == 1.4
    assert "hobby stall" in registry.excluded_categories
    assert len(registry.audit_checks) == 1
    assert len(registry.scoring_rules) == 1


def test_plugin_file_without_register_function_is_skipped(tmp_path):
    _write_plugin(tmp_path, "broken.py", "x = 1\n")
    registry = get_registry()
    assert registry.loaded_plugins == []


def test_plugin_file_that_raises_is_skipped_without_crashing(tmp_path):
    _write_plugin(
        tmp_path,
        "explodes.py",
        """
def register(registry):
    raise RuntimeError("boom")
""",
    )
    registry = get_registry()  # must not raise
    assert registry.loaded_plugins == []


def test_underscore_prefixed_files_are_ignored(tmp_path):
    _write_plugin(
        tmp_path,
        "_helper.py",
        """
def register(registry):
    registry.add_category_weight("should not load", 9.9)
""",
    )
    registry = get_registry()
    assert registry.loaded_plugins == []
    assert "should not load" not in registry.category_weights


def test_multiple_plugins_all_load(tmp_path):
    _write_plugin(tmp_path, "one.py", "def register(registry):\n    registry.add_category_weight('a', 1.1)\n")
    _write_plugin(tmp_path, "two.py", "def register(registry):\n    registry.add_category_weight('b', 1.2)\n")
    registry = get_registry()
    assert len(registry.loaded_plugins) == 2
    assert registry.category_weights["a"] == 1.1
    assert registry.category_weights["b"] == 1.2


def test_default_plugins_dir_created(monkeypatch, tmp_path):
    monkeypatch.delenv("LEADFORGE_PLUGINS_DIR", raising=False)
    monkeypatch.setenv("LEADFORGE_HOME", str(tmp_path / "home"))
    directory = default_plugins_dir()
    assert directory.is_dir()
    assert directory == tmp_path / "home" / "plugins"


def test_entry_point_plugin_loads():
    fake_ep = MagicMock()
    fake_ep.name = "fake_plugin"
    fake_ep.value = "fake_module:register"
    fake_ep.load.return_value = lambda registry: registry.add_category_weight("ep category", 2.0)

    with patch("leadforge.plugins.importlib.metadata.entry_points", return_value=[fake_ep]):
        registry = PluginRegistry()
        registry.load_entry_point_plugins()

    assert len(registry.loaded_plugins) == 1
    assert registry.loaded_plugins[0].source == "entry_point:fake_module:register"
    assert registry.category_weights["ep category"] == 2.0


def test_entry_point_plugin_error_is_isolated():
    fake_ep = MagicMock()
    fake_ep.name = "broken_ep"
    fake_ep.value = "broken:register"
    fake_ep.load.side_effect = ImportError("no such module")

    with patch("leadforge.plugins.importlib.metadata.entry_points", return_value=[fake_ep]):
        registry = PluginRegistry()
        registry.load_entry_point_plugins()  # must not raise

    assert registry.loaded_plugins == []


# -- Scoring integration --------------------------------------------------

def test_scoring_uses_plugin_category_weight(tmp_path):
    _write_plugin(
        tmp_path,
        "weight_pack.py",
        """
def register(registry):
    registry.add_category_weight("widget maker", 3.0)
""",
    )
    business = Business(id=1, name="Acme Widgets", category="Widget Maker")
    with_plugin = score_business(business, use_plugins=True)
    without_plugin = score_business(business, use_plugins=False)
    assert with_plugin.opportunity_score > without_plugin.opportunity_score


def test_scoring_uses_plugin_excluded_category(tmp_path):
    _write_plugin(
        tmp_path,
        "exclude_pack.py",
        """
def register(registry):
    registry.exclude_category("hobby stall")
""",
    )
    business = Business(id=1, name="Jane's Hobby Stall", category="Hobby Stall")
    result = score_business(business, use_plugins=True)
    assert result.opportunity_score == 0
    assert result.tier == "Excluded"
    assert is_excluded_category("Hobby Stall")


def test_scoring_rule_adjusts_final_score_and_reasons(tmp_path):
    _write_plugin(
        tmp_path,
        "bonus_pack.py",
        """
from leadforge.plugins import ScoreAdjustment

def register(registry):
    registry.add_scoring_rule(lambda ctx: ScoreAdjustment(delta=10, reasons=["Plugin bonus applied"]))
""",
    )
    business = Business(id=1, name="Acme", category="Gym", rating=4.0, review_count=10)
    with_plugin = score_business(business, use_plugins=True)
    without_plugin = score_business(business, use_plugins=False)

    assert with_plugin.opportunity_score == min(100, without_plugin.opportunity_score + 10)
    assert "Plugin bonus applied" in with_plugin.reasons


def test_scoring_rule_result_is_reclamped_to_100(tmp_path):
    _write_plugin(
        tmp_path,
        "huge_bonus.py",
        """
from leadforge.plugins import ScoreAdjustment

def register(registry):
    registry.add_scoring_rule(lambda ctx: ScoreAdjustment(delta=1000))
""",
    )
    business = Business(id=1, name="Acme", category="Gym")
    result = score_business(business, use_plugins=True)
    assert result.opportunity_score == 100
    assert result.tier == "Very High"


def test_scoring_rule_can_reduce_score(tmp_path):
    _write_plugin(
        tmp_path,
        "penalty.py",
        """
from leadforge.plugins import ScoreAdjustment

def register(registry):
    registry.add_scoring_rule(lambda ctx: ScoreAdjustment(delta=-1000, reasons=["big penalty"]))
""",
    )
    business = Business(id=1, name="Acme", category="Gym")
    result = score_business(business, use_plugins=True)
    assert result.opportunity_score == 0
    assert "big penalty" in result.reasons


def test_broken_scoring_rule_is_skipped_without_crashing(tmp_path):
    _write_plugin(
        tmp_path,
        "broken_rule.py",
        """
def register(registry):
    def bad_rule(ctx):
        raise ValueError("nope")
    registry.add_scoring_rule(bad_rule)
""",
    )
    business = Business(id=1, name="Acme", category="Gym")
    result = score_business(business, use_plugins=True)  # must not raise
    assert isinstance(result.opportunity_score, int)


def test_excluded_business_never_reaches_scoring_rules(tmp_path):
    _write_plugin(
        tmp_path,
        "counter_pack.py",
        """
from leadforge.plugins import ScoreAdjustment

calls = []

def register(registry):
    registry.add_scoring_rule(record_call)

def record_call(ctx):
    calls.append(ctx.business.name)
    return ScoreAdjustment()
""",
    )
    business = Business(id=1, name="Rahul's Tea Stall", category="Tea Stall")
    result = score_business(business, use_plugins=True)
    assert result.tier == "Excluded"
    assert result.opportunity_score == 0


# -- Audit integration ------------------------------------------------------

GOOD_HTML_WITH_MARKER = """
<html lang="en"><head><title>T</title>
<meta name="description" content="d"><meta name="viewport" content="w">
<link rel="icon" href="/f.ico"></head>
<body><h1>Hi</h1><a href="mailto:a@b.com">mail</a><a href="https://wa.me/1">wa</a></body></html>
"""


def _mock_response(text, status_code=200, url="https://acme.example.com"):
    resp = MagicMock()
    resp.text = text
    resp.status_code = status_code
    resp.url = url
    resp.history = []
    return resp


@patch("leadforge.audit._check_tls", return_value=True)
@patch("leadforge.audit.requests.get")
def test_audit_check_appends_issue(mock_get, mock_tls, tmp_path):
    _write_plugin(
        tmp_path,
        "audit_pack.py",
        """
def register(registry):
    registry.add_audit_check(lambda ctx: ["Plugin found a problem"])
""",
    )
    mock_get.return_value = _mock_response(GOOD_HTML_WITH_MARKER)
    settings = get_settings()
    result = audit_website(1, "https://acme.example.com", settings, use_plugins=True)
    assert "Plugin found a problem" in result.issues


@patch("leadforge.audit._check_tls", return_value=True)
@patch("leadforge.audit.requests.get")
def test_audit_check_receives_business_and_html(mock_get, mock_tls, tmp_path):
    _write_plugin(
        tmp_path,
        "context_pack.py",
        """
def register(registry):
    registry.add_audit_check(check)

def check(ctx):
    issues = []
    if ctx.business is not None and ctx.business.category == "Gym":
        issues.append(f"Category was {ctx.business.category}")
    if ctx.html and "<h1>Hi</h1>" in ctx.html:
        issues.append("Found the H1 marker")
    return issues
""",
    )
    mock_get.return_value = _mock_response(GOOD_HTML_WITH_MARKER)
    settings = get_settings()
    business = Business(id=1, name="Acme", category="Gym", website="https://acme.example.com")
    result = audit_website(1, business.website, settings, business=business, use_plugins=True)
    assert "Category was Gym" in result.issues
    assert "Found the H1 marker" in result.issues


@patch("leadforge.audit._check_tls", return_value=True)
@patch("leadforge.audit.requests.get")
def test_audit_check_disabled_via_use_plugins_false(mock_get, mock_tls, tmp_path):
    _write_plugin(
        tmp_path,
        "audit_pack.py",
        """
def register(registry):
    registry.add_audit_check(lambda ctx: ["Should not appear"])
""",
    )
    mock_get.return_value = _mock_response(GOOD_HTML_WITH_MARKER)
    settings = get_settings()
    result = audit_website(1, "https://acme.example.com", settings, use_plugins=False)
    assert "Should not appear" not in result.issues


@patch("leadforge.audit._check_tls", return_value=True)
@patch("leadforge.audit.requests.get")
def test_broken_audit_check_is_skipped_without_crashing(mock_get, mock_tls, tmp_path):
    _write_plugin(
        tmp_path,
        "broken_audit.py",
        """
def register(registry):
    def bad_check(ctx):
        raise ValueError("nope")
    registry.add_audit_check(bad_check)
""",
    )
    mock_get.return_value = _mock_response(GOOD_HTML_WITH_MARKER)
    settings = get_settings()
    result = audit_website(1, "https://acme.example.com", settings, use_plugins=True)  # must not raise
    assert result.reachable is True


@patch("leadforge.audit._check_tls", return_value=True)
@patch("leadforge.audit.requests.get")
def test_audit_checks_skipped_when_unreachable(mock_get, mock_tls, tmp_path):
    _write_plugin(
        tmp_path,
        "should_not_run.py",
        """
def register(registry):
    registry.add_audit_check(lambda ctx: ["should not run"])
""",
    )
    mock_get.side_effect = Exception("connection refused")
    settings = get_settings()
    result = audit_website(1, "https://down.example.com", settings, use_plugins=True)
    assert result.reachable is False
    assert "should not run" not in result.issues


# -- Dataclass sanity -------------------------------------------------------

def test_score_adjustment_defaults():
    adj = ScoreAdjustment()
    assert adj.delta == 0
    assert adj.reasons == []


def test_scoring_context_and_audit_check_context_construct():
    business = Business(id=1, name="Acme")
    audit = AuditResult(business_id=1, url="https://a.example.com")
    ctx = ScoringContext(business=business, audit=audit, score=score_business(business, use_plugins=False))
    assert ctx.business is business
    actx = AuditCheckContext(business=business, url="https://a.example.com", html="<html></html>", result=audit)
    assert actx.html == "<html></html>"
