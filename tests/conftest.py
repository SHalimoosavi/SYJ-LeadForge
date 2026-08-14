"""Shared pytest fixtures.

`api_client` gives each test an isolated `LEADFORGE_HOME` (so tests
never share a SQLite database) and a fresh FastAPI TestClient. The
backend resolves `LEADFORGE_HOME` per-request via `get_settings()`
inside the dependency function, so setting the env var before each
request is enough to guarantee isolation — no need to reload the app.

It also isolates the plugin registry: `leadforge.plugins.get_registry()`
caches its result at module/process scope (by design — plugins only
need to load once per run), which means without resetting it here,
one test's plugin directory could otherwise leak into another test
via that cache. Each test gets its own empty plugin directory and a
freshly reset registry, so `/plugins` returns an empty list by default
unless a test explicitly writes a plugin file first.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from backend.main import app
    from leadforge.plugins import reset_registry

    monkeypatch.setenv("LEADFORGE_HOME", str(tmp_path / "leadforge_home"))
    monkeypatch.setenv("LEADFORGE_PLUGINS_DIR", str(tmp_path / "leadforge_plugins"))
    monkeypatch.setenv("LEADFORGE_DELAY", "0")  # keep batch-run tests fast
    reset_registry()

    with TestClient(app) as client:
        yield client

    reset_registry()
