"""Shared FastAPI dependencies.

`get_store` is resolved fresh on every request (not cached at import
time) so that tests can point `LEADFORGE_HOME` at an isolated temp
directory per test and get a clean database, exactly as the CLI does.

`StoreDep` is the `Annotated` form recommended by current FastAPI
style guidance -- it keeps route signatures free of `Depends(...)`
calls in argument defaults.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from leadforge.config import get_settings
from leadforge.db import Store


def get_store() -> Store:
    settings = get_settings()
    return Store(settings.db_path)


StoreDep = Annotated[Store, Depends(get_store)]
