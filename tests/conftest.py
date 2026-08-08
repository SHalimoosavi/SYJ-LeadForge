"""Shared pytest fixtures.

`api_client` gives each test an isolated `LEADFORGE_HOME` (so tests
never share a SQLite database) and a fresh FastAPI TestClient. The
backend resolves `LEADFORGE_HOME` per-request via `get_settings()`
inside the dependency function, so setting the env var before each
request is enough to guarantee isolation — no need to reload the app.
"""
from __future__ import annotations

import pytest


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from backend.main import app

    monkeypatch.setenv("LEADFORGE_HOME", str(tmp_path / "leadforge_home"))
    monkeypatch.setenv("LEADFORGE_DELAY", "0")  # keep batch-run tests fast

    with TestClient(app) as client:
        yield client
