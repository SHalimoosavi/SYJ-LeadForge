"""SYJ LeadForge command-line interface.

Examples:
    leadforge import sample_data/businesses_sample.csv
    leadforge audit
    leadforge score
    leadforge export csv --out leads.csv
    leadforge list --tier "Very High"
    leadforge doctor
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from . import __version__
from .audit import audit_website
from .config import get_settings
from .db import Store
from .exporters import EXPORTERS
from .importer import ImportError_, load_businesses_from_csv
from .models import AuditResult
from .scoring import score_business


def _get_store() -> Store:
    settings = get_settings()
    return Store(settings.db_path)


def cmd_import(args: argparse.Namespace) -> int:
    try:
        businesses = load_businesses_from_csv(Path(args.csv_path))
    except ImportError_ as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        return 1

    store = _get_store()
    count = 0
    for b in businesses:
        b.id = store.upsert_business(b)
        count += 1
    print(f"Imported/updated {count} businesses from {args.csv_path}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    settings = get_settings()
    store = _get_store()

    if args.id:
        businesses = [store.get_business(args.id)]
        businesses = [b for b in businesses if b]
    else:
        businesses = [b for b in store.list_businesses() if b.website]

    if not businesses:
        print("No businesses with a website found to audit. Run `leadforge import` first.")
        return 0

    print(f"Auditing {len(businesses)} website(s)...")
    for i, b in enumerate(businesses, start=1):
        print(f"  [{i}/{len(businesses)}] {b.name} -> {b.website}")
        result: AuditResult = audit_website(b.id, b.website, settings)
        store.save_audit(result)
        if result.reachable:
            print(f"      overall score: {result.overall_score}/100")
        else:
            print(f"      unreachable: {result.error}")
        if i < len(businesses) and settings.request_delay_seconds > 0:
            time.sleep(settings.request_delay_seconds)
    print("Audit complete.")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    store = _get_store()
    businesses = store.list_businesses()
    if not businesses:
        print("No businesses found. Run `leadforge import` first.")
        return 0

    for b in businesses:
        audit_dict = store.latest_audit(b.id)
        audit_obj = AuditResult(**audit_dict) if audit_dict else None
        score = score_business(b, audit_obj)
        store.save_score(score)
        print(f"{b.name}: {score.opportunity_score}/100 ({score.tier}, {'★' * score.stars})")
    print(f"Scored {len(businesses)} businesses.")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    fmt = args.format.lower()
    if fmt not in EXPORTERS:
        print(f"Unsupported format '{fmt}'. Choose from: {', '.join(sorted(set(EXPORTERS)))}", file=sys.stderr)
        return 1

    store = _get_store()
    records = store.all_latest_scores()
    if args.tier:
        records = [r for r in records if (r.get("score") or {}).get("tier", "").lower() == args.tier.lower()]
    if args.min_score is not None:
        records = [r for r in records if (r.get("score") or {}).get("opportunity_score", 0) >= args.min_score]

    if not records:
        print("No matching leads to export.")
        return 0

    default_name = f"leadforge_leads.{('md' if fmt in ('markdown', 'md') else fmt)}"
    out_path = Path(args.out) if args.out else Path(default_name)
    EXPORTERS[fmt](records, out_path)
    print(f"Exported {len(records)} lead(s) to {out_path}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    store = _get_store()
    records = store.all_latest_scores()
    if args.tier:
        records = [r for r in records if (r.get("score") or {}).get("tier", "").lower() == args.tier.lower()]
    records.sort(key=lambda r: (r.get("score") or {}).get("opportunity_score", 0), reverse=True)

    if not records:
        print("No businesses found. Run `leadforge import` first.")
        return 0

    print(f"{'ID':<4} {'Name':<30} {'Category':<20} {'City':<15} {'Score':<6} {'Tier':<10} {'Website'}")
    for r in records:
        score = r.get("score") or {}
        print(
            f"{r['id']:<4} {r['name'][:29]:<30} {(r['category'] or '')[:19]:<20} "
            f"{(r['city'] or '')[:14]:<15} {score.get('opportunity_score', '-'):<6} "
            f"{score.get('tier', '-'):<10} {r.get('website') or '(none)'}"
        )
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    settings = get_settings()
    print("SYJ LeadForge — doctor")
    print(f"  version:      {__version__}")
    print(f"  python:       {sys.version.split()[0]}")
    print(f"  data dir:     {settings.data_dir}")
    print(f"  database:     {settings.db_path} ({'exists' if settings.db_path.exists() else 'will be created'})")
    try:
        import requests  # noqa: F401
        print("  requests:     ok")
    except ImportError:
        print("  requests:     MISSING (pip install requests)")
    store = _get_store()
    businesses = store.list_businesses()
    print(f"  businesses:   {len(businesses)}")
    print("Status: OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="leadforge",
        description="SYJ LeadForge — find website opportunities, qualify leads, grow your freelance business.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_import = sub.add_parser("import", help="Import businesses from a CSV file")
    p_import.add_argument("csv_path", help="Path to the CSV file to import")
    p_import.set_defaults(func=cmd_import)

    p_audit = sub.add_parser("audit", help="Audit business websites")
    p_audit.add_argument("--id", type=int, help="Audit only this business ID")
    p_audit.set_defaults(func=cmd_audit)

    p_score = sub.add_parser("score", help="Compute opportunity scores for all businesses")
    p_score.set_defaults(func=cmd_score)

    p_export = sub.add_parser("export", help="Export scored leads")
    p_export.add_argument("format", choices=sorted(set(EXPORTERS)), help="Export format")
    p_export.add_argument("--out", help="Output file path")
    p_export.add_argument("--tier", help="Filter by tier (e.g. 'Very High')")
    p_export.add_argument("--min-score", type=int, help="Filter by minimum opportunity score")
    p_export.set_defaults(func=cmd_export)

    p_list = sub.add_parser("list", help="List businesses and their latest scores")
    p_list.add_argument("--tier", help="Filter by tier")
    p_list.set_defaults(func=cmd_list)

    p_doctor = sub.add_parser("doctor", help="Check environment and configuration")
    p_doctor.set_defaults(func=cmd_doctor)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
