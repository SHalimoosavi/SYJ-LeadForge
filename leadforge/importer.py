"""Import businesses from user-supplied CSV files.

SYJ LeadForge does not scrape or crawl third-party sites for this step.
It reads a CSV that the user has legitimately compiled -- e.g. from
their own research, a CRM export, or an official/permitted API dump --
and normalizes it into the local database.
"""
from __future__ import annotations

import csv
from pathlib import Path

from .models import Business

# Accepted column aliases -> canonical field name.
COLUMN_ALIASES = {
    "name": "name", "business_name": "name", "business": "name",
    "category": "category", "type": "category", "industry": "category",
    "city": "city", "town": "city",
    "state": "state", "province": "state",
    "country": "country",
    "phone": "phone", "phone_number": "phone", "contact": "phone",
    "website": "website", "url": "website", "site": "website",
    "rating": "rating", "stars": "rating",
    "review_count": "review_count", "reviews": "review_count", "num_reviews": "review_count",
    "notes": "notes",
}

REQUIRED_FIELDS = {"name"}


class ImportError_(Exception):
    """Raised when a CSV cannot be parsed into valid business records."""


def _normalize_row(raw_row: dict) -> dict:
    normalized: dict = {}
    for key, value in raw_row.items():
        if key is None:
            continue
        canonical = COLUMN_ALIASES.get(key.strip().lower())
        if canonical:
            normalized[canonical] = (value or "").strip()
    return normalized


def load_businesses_from_csv(path: Path) -> list[Business]:
    """Parse a CSV file into a list of Business records.

    Raises ImportError_ if the file has no recognizable header or is missing
    required columns such as 'name'.
    """
    path = Path(path)
    if not path.exists():
        raise ImportError_(f"File not found: {path}")

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ImportError_("CSV file has no header row")

        recognized = {COLUMN_ALIASES.get(h.strip().lower()) for h in reader.fieldnames}
        recognized.discard(None)
        missing = REQUIRED_FIELDS - recognized
        if missing:
            raise ImportError_(
                f"CSV is missing required column(s): {', '.join(sorted(missing))}. "
                f"Recognized columns: {', '.join(sorted(recognized)) or 'none'}"
            )

        businesses: list[Business] = []
        for line_num, raw_row in enumerate(reader, start=2):
            row = _normalize_row(raw_row)
            name = row.get("name", "").strip()
            if not name:
                continue  # skip blank rows rather than failing the whole import
            businesses.append(
                Business(
                    name=name,
                    category=row.get("category", "").strip(),
                    city=row.get("city", "").strip(),
                    state=row.get("state", "").strip(),
                    country=row.get("country", "").strip(),
                    phone=row.get("phone", "").strip(),
                    website=_normalize_url(row.get("website", "")),
                    rating=_safe_float(row.get("rating", "0")),
                    review_count=_safe_int(row.get("review_count", "0")),
                    notes=row.get("notes", "").strip(),
                )
            )
        return businesses


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def _safe_float(value: str) -> float:
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _safe_int(value: str) -> int:
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return 0
