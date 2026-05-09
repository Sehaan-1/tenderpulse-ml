"""JSONL upload and classification endpoint."""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.data import CATEGORY_COLORS, clean_title
from src.classify import classify_title
from src.title_cleaner import extract_title

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = PROJECT_ROOT / "models" / "bart-large-mnli"

router = APIRouter(prefix="/api/classify", tags=["classification"])


@lru_cache(maxsize=1)
def _classifier() -> Any:
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Local model not found at {MODEL_PATH}")

    try:
        from transformers import pipeline
    except ModuleNotFoundError as exc:
        raise RuntimeError("transformers is required to run classification") from exc

    return pipeline("zero-shot-classification", model=str(MODEL_PATH))


def _parse_jsonl(text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue

        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append({"line": line_number, "error": str(exc)})
            continue

        if not isinstance(value, dict):
            errors.append({"line": line_number, "error": "JSONL rows must be objects"})
            continue

        records.append(value)

    return records, errors


def _classify_text(text: str) -> dict[str, Any]:
    records, errors = _parse_jsonl(text)
    classifier = _classifier()
    enriched: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        raw_title = record.get("title") or record.get("clean_title") or ""

        try:
            title, reference = extract_title(str(raw_title))
        except (TypeError, ValueError):
            title = clean_title(raw_title)
            reference = None

        if not title:
            errors.append({"line": index + 1, "error": "Missing tender title"})
            continue

        category, confidence = classify_title(title, classifier)
        item = dict(record)
        item["clean_title"] = title
        if reference and not item.get("reference_number"):
            item["reference_number"] = reference
        item["predicted_category"] = category
        item["category_confidence"] = confidence
        enriched.append(item)

    output_jsonl = "".join(
        json.dumps(record, ensure_ascii=False) + "\n" for record in enriched
    )
    counts = Counter(record.get("predicted_category") for record in enriched)
    confidences = [float(record.get("category_confidence") or 0.0) for record in enriched]

    return {
        "total": len(enriched),
        "errors": errors,
        "results": enriched,
        "enriched_jsonl": output_jsonl,
        "category_counts": [
            {
                "label": label,
                "count": count,
                "color": CATEGORY_COLORS.get(str(label), "#7C8797"),
            }
            for label, count in counts.most_common()
        ],
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
    }


@router.post("")
async def classify_upload(file: UploadFile = File(...)) -> dict[str, Any]:
    payload = await file.read()
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Upload must be UTF-8 JSONL") from exc

    try:
        result = await run_in_threadpool(_classify_text, text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    result["file_name"] = file.filename
    return result

