"""Business CRUD and CSV import endpoints."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile

from leadforge.importer import ImportError_, load_businesses_from_csv
from leadforge.models import Business

from ..dependencies import StoreDep
from ..schemas import BusinessCreate, BusinessOut, ImportResult

router = APIRouter(prefix="/businesses", tags=["businesses"])


@router.post("/import", response_model=ImportResult)
async def import_businesses(
    store: StoreDep,
    file: Annotated[UploadFile, File(...)],
) -> ImportResult:
    """Import businesses from an uploaded CSV file (same format as the CLI)."""
    filename = (file.filename or "").lower()
    if not filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    content = await file.read()
    tmp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        businesses = load_businesses_from_csv(tmp_path)
    except ImportError_ as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)

    saved: list[BusinessOut] = []
    for business in businesses:
        business.id = store.upsert_business(business)
        saved.append(BusinessOut(**business.to_dict()))

    return ImportResult(imported=len(saved), businesses=saved)


@router.get("", response_model=list[BusinessOut])
def list_businesses(
    store: StoreDep,
    category: str | None = None,
    city: str | None = None,
) -> list[BusinessOut]:
    businesses = store.list_businesses(category=category, city=city)
    return [BusinessOut(**b.to_dict()) for b in businesses]


@router.post("", response_model=BusinessOut, status_code=201)
def create_business(payload: BusinessCreate, store: StoreDep) -> BusinessOut:
    business = Business(**payload.model_dump())
    business.id = store.upsert_business(business)
    return BusinessOut(**business.to_dict())


@router.get("/{business_id}", response_model=BusinessOut)
def get_business(business_id: int, store: StoreDep) -> BusinessOut:
    business = store.get_business(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return BusinessOut(**business.to_dict())
