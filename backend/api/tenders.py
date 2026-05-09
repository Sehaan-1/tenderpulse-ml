"""Tender browsing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.data import filter_tenders, load_tenders, organization_options, paginate, tender_by_id

router = APIRouter(prefix="/api/tenders", tags=["tenders"])


@router.get("")
def list_tenders(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = None,
    category: str | None = None,
    org: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    records = filter_tenders(
        load_tenders(),
        search=search,
        category=category,
        org=org,
        date_from=date_from,
        date_to=date_to,
    )
    items, total = paginate(records, page, page_size)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "categories": ["All", "Goods", "Services", "Works"],
        "organizations": organization_options(),
    }


@router.get("/{tender_id}")
def get_tender(tender_id: str) -> dict:
    record = tender_by_id(tender_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Tender not found")
    return record

