"""Opportunity scoring endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from leadforge.db import Store
from leadforge.models import AuditResult
from leadforge.scoring import score_business

from ..dependencies import StoreDep
from ..schemas import ScoreOut, ScoreRunResult

router = APIRouter(tags=["scores"])


def _latest_audit_obj(store: Store, business_id: int) -> AuditResult | None:
    audit_dict = store.latest_audit(business_id)
    return AuditResult(**audit_dict) if audit_dict else None


@router.post("/businesses/{business_id}/score", response_model=ScoreOut)
def score_single_business(business_id: int, store: StoreDep) -> ScoreOut:
    business = store.get_business(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    audit_obj = _latest_audit_obj(store, business_id)
    score = score_business(business, audit_obj)
    store.save_score(score)
    return ScoreOut(**score.to_dict())


@router.get("/businesses/{business_id}/score", response_model=ScoreOut)
def get_latest_score(business_id: int, store: StoreDep) -> ScoreOut:
    business = store.get_business(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    score = store.latest_score(business_id)
    if not score:
        raise HTTPException(status_code=404, detail="No score found for this business yet")
    return ScoreOut(**score)


@router.post("/scores/run", response_model=ScoreRunResult)
def run_all_scores(store: StoreDep) -> ScoreRunResult:
    businesses = store.list_businesses()
    results: list[ScoreOut] = []
    for business in businesses:
        audit_obj = _latest_audit_obj(store, business.id)
        score = score_business(business, audit_obj)
        store.save_score(score)
        results.append(ScoreOut(**score.to_dict()))
    return ScoreRunResult(scored=len(results), results=results)
