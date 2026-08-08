"""Combined lead listing, export, and dashboard stats endpoints."""
from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from leadforge.exporters import EXPORTERS

from ..dependencies import StoreDep
from ..schemas import AuditOut, LeadOut, ScoreOut, StatsOut

router = APIRouter(tags=["leads"])

_MEDIA_TYPES = {
    "csv": "text/csv",
    "json": "application/json",
    "markdown": "text/markdown",
    "md": "text/markdown",
}


def _filter_records(records: list[dict], tier: str | None, min_score: int | None) -> list[dict]:
    if tier:
        records = [r for r in records if (r.get("score") or {}).get("tier", "").lower() == tier.lower()]
    if min_score is not None:
        records = [r for r in records if (r.get("score") or {}).get("opportunity_score", 0) >= min_score]
    return records


@router.get("/leads", response_model=list[LeadOut])
def list_leads(
    store: StoreDep,
    tier: str | None = None,
    min_score: int | None = None,
) -> list[LeadOut]:
    records = _filter_records(store.all_latest_scores(), tier, min_score)
    records.sort(key=lambda r: (r.get("score") or {}).get("opportunity_score", 0), reverse=True)

    return [
        LeadOut(
            id=r["id"],
            name=r["name"],
            category=r.get("category") or "",
            city=r.get("city") or "",
            state=r.get("state") or "",
            country=r.get("country") or "",
            phone=r.get("phone") or "",
            website=r.get("website") or "",
            rating=r.get("rating") or 0.0,
            review_count=r.get("review_count") or 0,
            score=ScoreOut(**r["score"]) if r.get("score") else None,
            audit=AuditOut(**r["audit"]) if r.get("audit") else None,
        )
        for r in records
    ]


@router.get("/leads/export/{fmt}")
def export_leads(
    fmt: str,
    store: StoreDep,
    tier: str | None = None,
    min_score: int | None = None,
):
    fmt = fmt.lower()
    if fmt not in EXPORTERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{fmt}'. Choose from: {', '.join(sorted(set(EXPORTERS)))}",
        )

    records = _filter_records(store.all_latest_scores(), tier, min_score)
    if not records:
        raise HTTPException(status_code=404, detail="No matching leads to export")

    suffix = "md" if fmt in ("markdown", "md") else fmt
    with tempfile.NamedTemporaryFile(suffix=f".{suffix}", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    EXPORTERS[fmt](records, tmp_path)

    return FileResponse(
        path=tmp_path,
        media_type=_MEDIA_TYPES[fmt],
        filename=f"leadforge_leads.{suffix}",
    )


@router.get("/stats", response_model=StatsOut)
def get_stats(store: StoreDep) -> StatsOut:
    records = store.all_latest_scores()
    total = len(records)
    audited = sum(1 for r in records if r.get("audit"))
    scored_records = [r for r in records if r.get("score")]

    tier_breakdown: dict[str, int] = {}
    total_score = 0
    for r in scored_records:
        tier = r["score"]["tier"]
        tier_breakdown[tier] = tier_breakdown.get(tier, 0) + 1
        total_score += r["score"]["opportunity_score"]

    average_score = round(total_score / len(scored_records), 1) if scored_records else 0.0

    return StatsOut(
        total_businesses=total,
        audited=audited,
        scored=len(scored_records),
        tier_breakdown=tier_breakdown,
        average_score=average_score,
    )
