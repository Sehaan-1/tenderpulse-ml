"""Shared data loading and analytics helpers for the FastAPI backend."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from functools import lru_cache
import json
from pathlib import Path
from typing import Any

from notebooks import phase4_eval
from src.title_cleaner import extract_title

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENRICHED_PATH = PROJECT_ROOT / "data" / "enriched" / "tenders_enriched.jsonl"
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "tenders.jsonl"
EVALUATION_PATH = PROJECT_ROOT / "data" / "evaluation_annotations_final.csv"

LABELS = ("Goods", "Services", "Works")
CATEGORY_COLORS = {
    "Works": "#1976D2",
    "Goods": "#2E7D32",
    "Services": "#ED6C02",
    "Unclassified": "#7C8797",
}


def _jsonable_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return a copy that FastAPI can safely JSON encode."""
    return {key: value for key, value in record.items() if key != "raw_json"}


def _parse_date(value: Any) -> datetime | None:
    if not value:
        return None

    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clean_title(raw_title: Any) -> str:
    if not isinstance(raw_title, str):
        return ""

    try:
        title, _ = extract_title(raw_title)
        return title
    except (TypeError, ValueError):
        return raw_title.strip()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records

    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))

    return records


@lru_cache(maxsize=1)
def load_tenders() -> list[dict[str, Any]]:
    path = ENRICHED_PATH if ENRICHED_PATH.exists() else RAW_PATH
    records = load_jsonl(path)
    normalized: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        item = _jsonable_record(dict(record))
        tender_id = str(item.get("tender_id") or f"row-{index + 1}")
        category = item.get("predicted_category") or "Unclassified"

        item["record_key"] = f"{tender_id}-{index}"
        item["clean_title"] = clean_title(item.get("title"))
        item["predicted_category"] = category
        item["category_confidence"] = _as_float(item.get("category_confidence"))
        item["_sort_index"] = index
        normalized.append(item)

    return normalized


def tender_by_id(tender_id: str) -> dict[str, Any] | None:
    for record in load_tenders():
        if record.get("tender_id") == tender_id or record.get("record_key") == tender_id:
            return record
    return None


def filter_tenders(
    records: list[dict[str, Any]],
    search: str | None = None,
    category: str | None = None,
    org: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict[str, Any]]:
    query = (search or "").strip().lower()
    org_query = (org or "").strip().lower()
    start = _parse_date(date_from)
    end = _parse_date(date_to)

    filtered: list[dict[str, Any]] = []
    for record in records:
        haystack = " ".join(
            str(record.get(field) or "")
            for field in ("tender_id", "title", "clean_title", "org_chain", "predicted_category")
        ).lower()
        if query and query not in haystack:
            continue

        if category and category != "All" and record.get("predicted_category") != category:
            continue

        if org_query and org_query not in str(record.get("org_chain") or "").lower():
            continue

        published = _parse_date(record.get("published_date"))
        closing = _parse_date(record.get("closing_date"))
        comparison_date = published or closing
        if start and comparison_date and comparison_date < start:
            continue
        if end and comparison_date and comparison_date > end:
            continue

        filtered.append(record)

    return filtered


def paginate(records: list[dict[str, Any]], page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    total = len(records)
    safe_page = max(1, page)
    safe_size = min(max(1, page_size), 100)
    start = (safe_page - 1) * safe_size
    return records[start : start + safe_size], total


def category_distribution(records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = records if records is not None else load_tenders()
    counts = Counter(str(row.get("predicted_category") or "Unclassified") for row in rows)
    ordered_labels = [*LABELS, *sorted(label for label in counts if label not in LABELS)]

    return [
        {
            "label": label,
            "count": counts[label],
            "color": CATEGORY_COLORS.get(label, "#7C8797"),
        }
        for label in ordered_labels
        if counts[label]
    ]


def confidence_buckets(records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = records if records is not None else load_tenders()
    buckets = [
        {"label": "0.0-0.2", "min": 0.0, "max": 0.2, "count": 0},
        {"label": "0.2-0.4", "min": 0.2, "max": 0.4, "count": 0},
        {"label": "0.4-0.6", "min": 0.4, "max": 0.6, "count": 0},
        {"label": "0.6-0.8", "min": 0.6, "max": 0.8, "count": 0},
        {"label": "0.8-1.0", "min": 0.8, "max": 1.0, "count": 0},
    ]

    for row in rows:
        confidence = _as_float(row.get("category_confidence"))
        if confidence is None:
            continue

        for bucket in buckets:
            if bucket["min"] <= confidence < bucket["max"] or (
                confidence == 1.0 and bucket["max"] == 1.0
            ):
                bucket["count"] += 1
                break

    return buckets


def monthly_category_counts(records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    rows = records if records is not None else load_tenders()
    grouped: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        date_value = _parse_date(row.get("published_date")) or _parse_date(row.get("closing_date"))
        if date_value is None:
            continue

        month = date_value.strftime("%Y-%m")
        grouped[month][str(row.get("predicted_category") or "Unclassified")] += 1

    output: list[dict[str, Any]] = []
    for month in sorted(grouped):
        entry: dict[str, Any] = {"month": month}
        for label in LABELS:
            entry[label] = grouped[month][label]
        output.append(entry)

    return output


def recent_tenders(limit: int = 8) -> list[dict[str, Any]]:
    records = sorted(
        load_tenders(),
        key=lambda row: _parse_date(row.get("published_date")) or datetime.min,
        reverse=True,
    )
    return records[:limit]


def organization_options(limit: int = 25) -> list[str]:
    counts = Counter(str(row.get("org_chain") or "Unknown") for row in load_tenders())
    return [org for org, _ in counts.most_common(limit)]


def summary_payload() -> dict[str, Any]:
    records = load_tenders()
    confidences = [
        value
        for value in (_as_float(row.get("category_confidence")) for row in records)
        if value is not None
    ]
    evaluation = evaluation_payload()

    return {
        "total": len(records),
        "category_counts": category_distribution(records),
        "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0,
        "confidence_buckets": confidence_buckets(records),
        "monthly_category_counts": monthly_category_counts(records),
        "recent_tenders": recent_tenders(),
        "accuracy": evaluation.get("representative_accuracy", 0.0),
        "baseline_accuracy": evaluation.get("dataset_baseline", 0.0),
    }


def evaluation_payload() -> dict[str, Any]:
    records = load_tenders()
    annotations = phase4_eval.load_annotations(EVALUATION_PATH)

    if not annotations:
        return {
            "labels": list(LABELS),
            "metrics": [],
            "confusion_matrix": [],
            "failure_counts": [],
            "worst_examples": [],
            "representative_accuracy": 0.0,
            "strict_representative_accuracy": 0.0,
            "all_accuracy": 0.0,
            "dataset_baseline": phase4_eval.dataset_baseline(records),
            "annotated_count": 0,
        }

    sample = phase4_eval.stratified_sample(records)
    rows = phase4_eval.evaluation_rows(records, sample, annotations)
    soft_all = phase4_eval.soft_rows(rows)
    soft_representative = phase4_eval.soft_rows(rows, representative_only=True)
    strict_representative = phase4_eval.strict_rows(rows, representative_only=True)
    metrics = phase4_eval.metrics_by_class(soft_all)
    failures = phase4_eval.failure_counts(soft_all)

    return {
        "labels": list(LABELS),
        "metrics": [
            {
                "label": label,
                "precision": metrics[label].precision,
                "recall": metrics[label].recall,
                "f1": metrics[label].f1,
                "support": metrics[label].support,
                "color": CATEGORY_COLORS[label],
            }
            for label in LABELS
        ],
        "confusion_matrix": phase4_eval.confusion_matrix_counts(soft_all),
        "failure_counts": [
            {"label": label, "count": count} for label, count in failures.most_common()
        ],
        "worst_examples": [
            {
                "tender_id": row.get("tender_id"),
                "title": row.get("title"),
                "clean_title": clean_title(row.get("title")),
                "predicted_category": row.get("predicted_category"),
                "actual_category": row.get("actual_category"),
                "category_confidence": _as_float(row.get("category_confidence")),
                "failure": phase4_eval.classify_failure(row),
            }
            for row in phase4_eval.worst_examples(soft_all, limit=8)
        ],
        "representative_accuracy": phase4_eval.accuracy(soft_representative),
        "strict_representative_accuracy": phase4_eval.accuracy(
            strict_representative,
            uncertain_is_wrong=True,
        ),
        "all_accuracy": phase4_eval.accuracy(soft_all),
        "dataset_baseline": phase4_eval.dataset_baseline(records),
        "annotated_count": len([row for row in rows if phase4_eval.is_annotated(row)]),
    }

