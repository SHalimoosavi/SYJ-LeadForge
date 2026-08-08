"""Website audit endpoints."""
from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from leadforge.audit import audit_website
from leadforge.config import get_settings

from ..dependencies import StoreDep
from ..schemas import AuditOut, AuditRunResult

router = APIRouter(tags=["audits"])


@router.post("/businesses/{business_id}/audit", response_model=AuditOut)
def audit_business(business_id: int, store: StoreDep) -> AuditOut:
    business = store.get_business(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if not business.website:
        raise HTTPException(status_code=400, detail="Business has no website to audit")

    settings = get_settings()
    result = audit_website(business.id, business.website, settings)
    store.save_audit(result)
    return AuditOut(**result.to_dict())


@router.get("/businesses/{business_id}/audit", response_model=AuditOut)
def get_latest_audit(business_id: int, store: StoreDep) -> AuditOut:
    business = store.get_business(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    audit = store.latest_audit(business_id)
    if not audit:
        raise HTTPException(status_code=404, detail="No audit found for this business yet")
    return AuditOut(**audit)


@router.post("/audits/run", response_model=AuditRunResult)
def run_all_audits(store: StoreDep) -> AuditRunResult:
    """Audit every business that has a website. Runs synchronously and
    respects the same polite `LEADFORGE_DELAY` between requests as the
    CLI's `leadforge audit` command."""
    settings = get_settings()
    businesses = [b for b in store.list_businesses() if b.website]

    results: list[AuditOut] = []
    for i, business in enumerate(businesses):
        result = audit_website(business.id, business.website, settings)
        store.save_audit(result)
        results.append(AuditOut(**result.to_dict()))
        if i < len(businesses) - 1 and settings.request_delay_seconds > 0:
            time.sleep(settings.request_delay_seconds)

    return AuditRunResult(audited=len(results), results=results)
