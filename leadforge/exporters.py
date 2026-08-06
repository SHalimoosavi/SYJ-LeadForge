"""Export qualified leads to CSV, JSON, or Markdown."""
from __future__ import annotations

import csv
import json
from pathlib import Path

FIELDNAMES = [
    "id", "name", "category", "city", "state", "country", "phone", "website",
    "rating", "review_count", "opportunity_score", "tier", "stars",
    "estimated_value_low", "estimated_value_high", "overall_website_score", "top_reasons",
]


def _flatten(record: dict) -> dict:
    score = record.get("score") or {}
    audit = record.get("audit") or {}
    return {
        "id": record.get("id"),
        "name": record.get("name"),
        "category": record.get("category"),
        "city": record.get("city"),
        "state": record.get("state"),
        "country": record.get("country"),
        "phone": record.get("phone"),
        "website": record.get("website"),
        "rating": record.get("rating"),
        "review_count": record.get("review_count"),
        "opportunity_score": score.get("opportunity_score", ""),
        "tier": score.get("tier", ""),
        "stars": score.get("stars", ""),
        "estimated_value_low": score.get("estimated_value_low", ""),
        "estimated_value_high": score.get("estimated_value_high", ""),
        "overall_website_score": audit.get("overall_score", ""),
        "top_reasons": "; ".join((score.get("reasons") or [])[:3]),
    }


def export_csv(records: list[dict], out_path: Path) -> Path:
    rows = [_flatten(r) for r in records]
    out_path = Path(out_path)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return out_path


def export_json(records: list[dict], out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
    return out_path


def export_markdown(records: list[dict], out_path: Path) -> Path:
    rows = sorted((_flatten(r) for r in records), key=lambda r: r["opportunity_score"] or 0, reverse=True)
    lines = [
        "# SYJ LeadForge — Lead Report",
        "",
        f"Total leads: {len(rows)}",
        "",
        "| Business | Category | City | Score | Tier | Website | Est. Value (INR) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        website = r["website"] or "_none_"
        value = f"{r['estimated_value_low']}-{r['estimated_value_high']}" if r["estimated_value_low"] else ""
        lines.append(
            f"| {r['name']} | {r['category']} | {r['city']} | {r['opportunity_score']} | "
            f"{r['tier']} | {website} | {value} |"
        )
    out_path = Path(out_path)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


EXPORTERS = {
    "csv": export_csv,
    "json": export_json,
    "markdown": export_markdown,
    "md": export_markdown,
}
