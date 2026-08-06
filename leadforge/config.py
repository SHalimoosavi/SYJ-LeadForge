"""Configuration for SYJ LeadForge.

All settings can be overridden via environment variables so that no
secrets or machine-specific paths ever need to be hardcoded or committed.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_DB_NAME = "leadforge.db"

# Categories excluded from scoring by default (configurable, see docs).
DEFAULT_EXCLUDED_CATEGORIES = {
    "tea stall",
    "street vendor",
    "kiosk",
    "fruit cart",
    "grocery shop",
    "push cart",
}

# Relative value weight per category used by the opportunity scorer.
# Values are illustrative starting points; override via a JSON file
# passed to `--weights` or by editing this table in a fork/plugin.
DEFAULT_CATEGORY_WEIGHTS = {
    "dental clinic": 1.4,
    "hospital": 1.5,
    "diagnostic lab": 1.3,
    "real estate agency": 1.4,
    "architect": 1.2,
    "interior designer": 1.2,
    "law firm": 1.5,
    "chartered accountant": 1.3,
    "travel agency": 1.1,
    "hotel": 1.4,
    "restaurant": 1.0,
    "wedding planner": 1.2,
    "event company": 1.1,
    "gym": 1.0,
    "coaching institute": 1.1,
    "automobile dealer": 1.3,
    "furniture store": 1.1,
    "private school": 1.3,
    "beauty clinic": 1.1,
    "medical specialist": 1.5,
    "salon": 1.0,
}


@dataclass
class Settings:
    """Runtime settings, resolved once at CLI startup."""

    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("LEADFORGE_HOME", Path.home() / ".leadforge")))
    db_path: Path = field(init=False)
    request_timeout: float = float(os.environ.get("LEADFORGE_TIMEOUT", "10"))
    user_agent: str = os.environ.get(
        "LEADFORGE_USER_AGENT",
        "SYJLeadForge/0.1 (+https://github.com/SHalimoosavi/SYJ-LeadForge; ethical website audit bot)",
    )
    max_redirects: int = int(os.environ.get("LEADFORGE_MAX_REDIRECTS", "5"))
    request_delay_seconds: float = float(os.environ.get("LEADFORGE_DELAY", "1.0"))

    def __post_init__(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / DEFAULT_DB_NAME


def get_settings() -> Settings:
    return Settings()
