"""Analytics endpoints for dashboard charts and evaluation views."""

from __future__ import annotations

from fastapi import APIRouter

from backend.data import evaluation_payload, summary_payload

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary() -> dict:
    return summary_payload()


@router.get("/evaluation")
def get_evaluation() -> dict:
    return evaluation_payload()

