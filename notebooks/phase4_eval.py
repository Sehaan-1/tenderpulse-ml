#!/usr/bin/env python3
"""Phase 4 evaluation helpers for manually annotated tender classifications.

The script intentionally uses only the Python standard library so the Phase 4
numbers can be checked before notebook/scientific dependencies are installed.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

RANDOM_SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "enriched" / "tenders_enriched.jsonl"
FINAL_ANNOTATIONS = PROJECT_ROOT / "data" / "evaluation_annotations_final.csv"
TEMPLATE_PATH = PROJECT_ROOT / "data" / "evaluation_annotations.csv"

LABELS = ("Goods", "Services", "Works")
SAMPLE_PLAN = {"Works": 54, "Services": 38, "Goods": 33}
PROPORTIONAL_PLAN = {"Works": 54, "Services": 38, "Goods": 8}
GOODS_OVERSAMPLE = 25
BASELINE_LABEL = "Works"

GROUND_TRUTH_LABELS = {
    "2026_NIT_906221_1": "Goods",
    "2026_IPA_904822_1": "Services",
    "2026_IISRM_907687_1": "Works",
    "2026_MoRTH_902622_1": "Services",
    "2026_TMC_906007_1": "Works",
}

PHASE2_MANUAL_BART = {
    "2026_NIT_906221_1": "Goods",
    "2026_IPA_904822_1": "Services",
    "2026_IISRM_907687_1": "Works",
    "2026_MoRTH_902622_1": "Services",
    "2026_TMC_906007_1": "Works",
}


@dataclass(frozen=True)
class ClassMetrics:
    precision: float
    recall: float
    f1: float
    support: int


def load_data(path: Path = DATA_PATH) -> list[dict]:
    """Load the enriched classification JSONL."""
    records: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def category_distribution(records: Iterable[dict]) -> Counter:
    return Counter(row.get("predicted_category") for row in records)


def dataset_baseline(records: list[dict], label: str = BASELINE_LABEL) -> float:
    """Return the Phase 4 zero-rule baseline from the full enriched output."""
    if not records:
        return 0.0
    counts = category_distribution(records)
    return counts[label] / len(records)


def stratified_sample(records: list[dict], seed: int = RANDOM_SEED) -> list[dict]:
    """Sample 100 proportional rows plus 25 extra predicted-Goods rows."""
    rng = random.Random(seed)
    by_category: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        by_category[row.get("predicted_category")].append(row)

    population_counts = category_distribution(records)
    sample_rows: list[dict] = []

    for category in ("Works", "Services", "Goods"):
        requested = SAMPLE_PLAN[category]
        available = by_category[category]
        selected = rng.sample(available, min(requested, len(available)))

        for category_index, row in enumerate(selected):
            sample_group = "proportional_100"
            if category == "Goods" and category_index >= PROPORTIONAL_PLAN["Goods"]:
                sample_group = "goods_oversample"

            sample_count = max(1, SAMPLE_PLAN[category])
            sample_rows.append(
                {
                    "tender_id": row.get("tender_id"),
                    "title": row.get("title"),
                    "predicted_category": row.get("predicted_category"),
                    "category_confidence": row.get("category_confidence"),
                    "sample_group": sample_group,
                    "population_weight": population_counts[category] / sample_count,
                    "human_verdict": "",
                    "actual_category": "",
                    "notes": "",
                }
            )

    return sample_rows


def write_annotation_template(rows: list[dict], path: Path = TEMPLATE_PATH, overwrite: bool = False) -> bool:
    """Write the manual annotation template.

    Returns True when the file was written and False when an existing file was
    preserved.
    """
    if path.exists() and not overwrite:
        return False

    columns = [
        "tender_id",
        "title",
        "predicted_category",
        "category_confidence",
        "sample_group",
        "human_verdict",
        "actual_category",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})

    return True


def blank_annotation_fields(rows: list[dict]) -> list[dict]:
    blank_rows: list[dict] = []
    for row in rows:
        blank = dict(row)
        blank["human_verdict"] = ""
        blank["actual_category"] = ""
        blank["notes"] = ""
        blank_rows.append(blank)
    return blank_rows


def load_annotations(path: Path = FINAL_ANNOTATIONS) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def attach_annotations(sample_rows: list[dict], annotations: list[dict]) -> list[dict]:
    """Attach human annotations to sampled rows.

    Positional alignment is preferred because tender IDs are not guaranteed to
    be unique in raw pulls. If the files are out of order, fall back to ID lookup.
    """
    rows = [dict(row) for row in sample_rows]
    annotation_fields = ("human_verdict", "actual_category", "notes")

    aligned = (
        len(rows) == len(annotations)
        and all(row["tender_id"] == anno.get("tender_id") for row, anno in zip(rows, annotations))
    )
    if aligned:
        for row, anno in zip(rows, annotations):
            for field in annotation_fields:
                row[field] = anno.get(field, "")
        return rows

    by_id = {anno.get("tender_id"): anno for anno in annotations}
    for row in rows:
        anno = by_id.get(row["tender_id"], {})
        for field in annotation_fields:
            row[field] = anno.get(field, "")
    return rows


def rows_from_annotations(annotations: list[dict], records: list[dict]) -> list[dict]:
    """Use the final annotation CSV itself as the evaluation sample.

    This keeps completed manual work authoritative even if the local sampling
    implementation changes. The first 8 predicted-Goods rows are treated as the
    proportional Goods slice; later predicted-Goods rows are the 25-row oversample.
    """
    population_counts = category_distribution(records)
    sample_counts = Counter(row.get("predicted_category") for row in annotations)
    seen_by_category: Counter = Counter()
    rows: list[dict] = []

    for annotation in annotations:
        row = dict(annotation)
        category = row.get("predicted_category")
        seen_by_category[category] += 1

        sample_group = "proportional_100"
        if category == "Goods" and seen_by_category[category] > PROPORTIONAL_PLAN["Goods"]:
            sample_group = "goods_oversample"

        denominator = max(1, sample_counts[category])
        row["sample_group"] = row.get("sample_group") or sample_group
        row["population_weight"] = population_counts[category] / denominator
        rows.append(row)

    return rows


def evaluation_rows(records: list[dict], sample_rows: list[dict], annotations: list[dict]) -> list[dict]:
    """Return annotated evaluation rows, preserving completed CSVs when present."""
    if not annotations:
        return sample_rows

    aligned = (
        len(sample_rows) == len(annotations)
        and all(row["tender_id"] == anno.get("tender_id") for row, anno in zip(sample_rows, annotations))
    )
    if aligned:
        return attach_annotations(sample_rows, annotations)

    return rows_from_annotations(annotations, records)


def is_uncertain(row: dict) -> bool:
    return row.get("human_verdict", "").strip() == "?"


def is_annotated(row: dict) -> bool:
    verdict = row.get("human_verdict", "").strip()
    actual = row.get("actual_category", "").strip()
    return verdict in {"correct", "incorrect", "?"} and (verdict == "?" or actual in LABELS)


def soft_rows(rows: list[dict], representative_only: bool = False) -> list[dict]:
    filtered = [row for row in rows if is_annotated(row) and not is_uncertain(row)]
    if representative_only:
        filtered = [row for row in filtered if row.get("sample_group") == "proportional_100"]
    return filtered


def strict_rows(rows: list[dict], representative_only: bool = False) -> list[dict]:
    filtered = [row for row in rows if is_annotated(row)]
    if representative_only:
        filtered = [row for row in filtered if row.get("sample_group") == "proportional_100"]
    return filtered


def row_is_correct(row: dict) -> bool:
    return row.get("actual_category") == row.get("predicted_category")


def accuracy(rows: list[dict], uncertain_is_wrong: bool = False) -> float:
    if not rows:
        return 0.0
    if uncertain_is_wrong:
        return sum(row.get("human_verdict") == "correct" for row in rows) / len(rows)
    return sum(row_is_correct(row) for row in rows) / len(rows)


def metrics_by_class(rows: list[dict]) -> dict[str, ClassMetrics]:
    metrics: dict[str, ClassMetrics] = {}
    for label in LABELS:
        tp = sum(row.get("actual_category") == label and row.get("predicted_category") == label for row in rows)
        fp = sum(row.get("actual_category") != label and row.get("predicted_category") == label for row in rows)
        fn = sum(row.get("actual_category") == label and row.get("predicted_category") != label for row in rows)
        support = sum(row.get("actual_category") == label for row in rows)

        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        metrics[label] = ClassMetrics(precision, recall, f1, support)
    return metrics


def confusion_matrix_counts(rows: list[dict]) -> list[list[int]]:
    matrix: list[list[int]] = []
    for actual in LABELS:
        matrix.append(
            [
                sum(
                    row.get("actual_category") == actual
                    and row.get("predicted_category") == predicted
                    for row in rows
                )
                for predicted in LABELS
            ]
        )
    return matrix


def classify_failure(row: dict) -> str:
    title = str(row.get("title", "")).lower()
    confidence = float(row.get("category_confidence") or 0.0)

    if confidence < 0.4:
        return "Low-confidence wrong"

    if len(title) < 30:
        return "Title too short / reference only"

    has_construction = any(word in title for word in ("construction", "building", "civil", "flooring"))
    has_maintenance = any(word in title for word in ("maintenance", "repair", "service", "operation"))
    has_supply = any(word in title for word in ("supply", "procurement", "purchase", "consumable"))
    if sum((has_construction, has_maintenance, has_supply)) >= 2:
        return "Mixed signal"

    if any(word in title for word in ("installation", "operation", "management", "services", "work")):
        return "Ambiguous verb/noun"

    if any(word in title for word in ("medical", "hospital", "surgical", "medicine", "consumable")):
        return "Medical equipment ambiguity"

    if any(word in title for word in ("supply", "procurement", "purchase", "s.i.t.c", "sitc")):
        return "SITC/supply misclassified as non-Goods"

    return "Other"


def incorrect_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("actual_category") != row.get("predicted_category")]


def failure_counts(rows: list[dict]) -> Counter:
    return Counter(classify_failure(row) for row in incorrect_rows(rows))


def worst_examples(rows: list[dict], limit: int = 5) -> list[dict]:
    wrong = incorrect_rows(rows)
    return sorted(wrong, key=lambda row: float(row.get("category_confidence") or 0.0), reverse=True)[:limit]


def ground_truth_cross_check(records: list[dict]) -> list[dict]:
    by_id = {row.get("tender_id"): row for row in records}
    checks: list[dict] = []
    for tender_id, ground_truth in GROUND_TRUTH_LABELS.items():
        row = by_id.get(tender_id, {})
        phase3 = row.get("predicted_category")
        checks.append(
            {
                "tender_id": tender_id,
                "phase2_manual_bart": PHASE2_MANUAL_BART[tender_id],
                "phase3_pipeline_bart": phase3 or "missing",
                "ground_truth": ground_truth,
                "consistent": bool(phase3) and phase3 == PHASE2_MANUAL_BART[tender_id] == ground_truth,
            }
        )
    return checks


def select_low_confidence_correct(rows: list[dict], threshold: float = 0.3) -> dict | None:
    correct = [
        row
        for row in rows
        if row.get("human_verdict") == "correct" and float(row.get("category_confidence") or 0.0) < threshold
    ]
    if not correct:
        correct = [row for row in rows if row.get("human_verdict") == "correct"]
    if not correct:
        return None
    return min(correct, key=lambda row: float(row.get("category_confidence") or 0.0))


def run_stability_check(rows: list[dict], repeats: int = 100, threshold: float = 0.3) -> bool:
    """Repeat the model call for one low-confidence correct row.

    This is optional and intentionally isolated because it requires torch,
    transformers, and the local BART model.
    """
    candidate = select_low_confidence_correct(rows, threshold=threshold)
    if candidate is None:
        print("[STABILITY] No correct annotated row available for re-check.")
        return False

    try:
        from transformers import pipeline

        sys.path.insert(0, str(PROJECT_ROOT))
        from src.classify import classify_title
        from src.title_cleaner import extract_title
    except ModuleNotFoundError as exc:
        print(f"[STABILITY] Skipped: missing dependency {exc.name!r}.")
        return False

    model_path = PROJECT_ROOT / "models" / "bart-large-mnli"
    if not model_path.exists():
        print(f"[STABILITY] Skipped: local model not found at {model_path}.")
        return False

    raw_title = candidate.get("title", "")
    clean_title, _ = extract_title(raw_title)
    classifier = pipeline("zero-shot-classification", model=str(model_path))

    predictions: Counter = Counter()
    scores: list[float] = []
    for _ in range(repeats):
        label, score = classify_title(clean_title, classifier)
        predictions[label] += 1
        scores.append(score)

    expected = candidate.get("predicted_category")
    stable = predictions == Counter({expected: repeats})
    print("[STABILITY] Low-confidence row:")
    print(f"  tender_id: {candidate.get('tender_id')}")
    print(f"  expected:  {expected} ({float(candidate.get('category_confidence') or 0.0):.3f})")
    print(f"  repeats:   {repeats}")
    print(f"  counts:    {dict(predictions)}")
    print(f"  score min/max: {min(scores):.3f}/{max(scores):.3f}")
    print(f"  stable:    {stable}")
    return stable


def print_distribution(records: list[dict]) -> None:
    counts = category_distribution(records)
    total = len(records)
    print(f"[DATA] Loaded {total} enriched records.")
    for label in LABELS:
        print(f"  {label:8s}: {counts[label]:3d} ({counts[label] / total:.1%})")


def print_metrics(metrics: dict[str, ClassMetrics]) -> None:
    print("Class       Precision  Recall   F1      Support")
    for label in LABELS:
        metric = metrics[label]
        print(
            f"{label:10s} {metric.precision:9.3f}  {metric.recall:6.3f}  "
            f"{metric.f1:6.3f}  {metric.support:7d}"
        )


def print_confusion_matrix(matrix: list[list[int]]) -> None:
    print("               Predicted")
    print("Actual         Goods  Services  Works")
    for label, row in zip(LABELS, matrix):
        print(f"{label:10s} {row[0]:6d} {row[1]:9d} {row[2]:6d}")


def print_report(records: list[dict], rows: list[dict]) -> None:
    annotations = [row for row in rows if is_annotated(row)]
    soft_all = soft_rows(rows)
    soft_representative = soft_rows(rows, representative_only=True)
    strict_all = strict_rows(rows)
    strict_representative = strict_rows(rows, representative_only=True)

    print("=" * 72)
    print("Phase 4 Evaluation")
    print("=" * 72)
    print_distribution(records)

    expected_sample_size = sum(SAMPLE_PLAN.values())
    print(f"\n[SAMPLE] {len(rows)} evaluation rows; expected {expected_sample_size}.")
    print(f"  Proportional rows: {sum(row.get('sample_group') == 'proportional_100' for row in rows)}")
    print(f"  Goods oversample:  {sum(row.get('sample_group') == 'goods_oversample' for row in rows)}")

    verdict_counts = Counter(row.get("human_verdict", "") for row in rows)
    print(f"\n[ANNOTATION] {len(annotations)} valid annotated rows.")
    for verdict in ("correct", "incorrect", "?"):
        print(f"  {verdict:9s}: {verdict_counts[verdict]:3d}")

    dataset_zero_rule = dataset_baseline(records)
    representative_accuracy = accuracy(soft_representative)
    representative_strict_accuracy = accuracy(strict_representative, uncertain_is_wrong=True)
    all_accuracy = accuracy(soft_all)
    all_strict_accuracy = accuracy(strict_all, uncertain_is_wrong=True)
    human_zero_rule = (
        sum(row.get("actual_category") == BASELINE_LABEL for row in soft_representative) / len(soft_representative)
        if soft_representative
        else 0.0
    )

    print("\n[METRICS] Soft metrics exclude '?' rows.")
    print_metrics(metrics_by_class(soft_all))
    print(f"\n  Overall accuracy, all diagnostic soft rows (n={len(soft_all)}):         {all_accuracy:.3f}")
    print(f"  Strict accuracy, all rows (? = wrong, n={len(strict_all)}):             {all_strict_accuracy:.3f}")
    print(f"  Representative accuracy, proportional soft rows (n={len(soft_representative)}): {representative_accuracy:.3f}")
    print(f"  Representative strict accuracy (? = wrong, n={len(strict_representative)}):      {representative_strict_accuracy:.3f}")
    print(f"  Dataset zero-rule baseline (always Works):                            {dataset_zero_rule:.3f}")
    print(f"  Human eval zero-rule baseline, proportional rows:                     {human_zero_rule:.3f}")
    print(f"  Margin vs dataset zero-rule baseline:                                 {representative_accuracy - dataset_zero_rule:+.3f}")

    print("\n[CONFUSION MATRIX] All soft annotated rows.")
    print_confusion_matrix(confusion_matrix_counts(soft_all))

    print("\n[ERROR ANALYSIS] All soft annotated rows.")
    counts = failure_counts(soft_all)
    if counts:
        for failure, count in counts.most_common():
            print(f"  {failure}: {count}")
    else:
        print("  No incorrect predictions.")

    print("\n[WORST 5] Highest-confidence wrong predictions.")
    for row in worst_examples(soft_all, limit=5):
        print(f"  {row.get('tender_id')}:")
        print(f"    title:     {row.get('title')}")
        print(
            f"    predicted: {row.get('predicted_category')} "
            f"({float(row.get('category_confidence') or 0.0):.3f})"
        )
        print(f"    actual:    {row.get('actual_category')}")
        print(f"    failure:   {classify_failure(row)}")

    print("\n[GROUND TRUTH CROSS-CHECK]")
    checks = ground_truth_cross_check(records)
    for check in checks:
        print(
            f"  {check['tender_id']}: phase2={check['phase2_manual_bart']}, "
            f"phase3={check['phase3_pipeline_bart']}, ground_truth={check['ground_truth']}, "
            f"consistent={check['consistent']}"
        )

    # Build exit criteria with consistent flag
    exit_passed = all(check["consistent"] for check in checks)
    print("\n[EXIT CRITERIA]")
    criteria = [
        ("125 records annotated", len(annotations) == 125),
        ("100 proportional + 25 Goods sampled", len(rows) == 125 and sum(row.get("sample_group") == "goods_oversample" for row in rows) == GOODS_OVERSAMPLE),
        ("Per-class precision, recall, F1 computed", bool(soft_all)),
        ("Representative accuracy beats dataset zero-rule baseline", representative_accuracy > dataset_zero_rule),
        ("Confusion matrix generated", bool(soft_all)),
        ("5 worst predictions available or no errors", True),
        ("Error analysis has failure counts", bool(counts)),
        ("Ground-truth cross-check all consistent", exit_passed),
    ]
    for description, passed in criteria:
        print(f"  [{'x' if passed else ' '}] {description}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 4 evaluation.")
    parser.add_argument("--write-template", action="store_true", help="Write data/evaluation_annotations.csv.")
    parser.add_argument("--overwrite-template", action="store_true", help="Overwrite an existing annotation template.")
    parser.add_argument("--stability", action="store_true", help="Run the optional 100-call low-confidence stability check.")
    parser.add_argument("--repeats", type=int, default=100, help="Repeat count for --stability.")
    parser.add_argument("--threshold", type=float, default=0.3, help="Low-confidence threshold for --stability.")
    args = parser.parse_args()

    records = load_data()
    sample = stratified_sample(records)
    annotations = load_annotations()

    if args.write_template:
        template_rows = rows_from_annotations(annotations, records) if annotations else sample
        wrote = write_annotation_template(
            blank_annotation_fields(template_rows),
            overwrite=args.overwrite_template,
        )
        status = "written" if wrote else "already exists"
        print(f"[TEMPLATE] {TEMPLATE_PATH} {status}.")

    if not annotations:
        write_annotation_template(sample)
        print(f"[ANNOTATION] No final annotations found at {FINAL_ANNOTATIONS}.")
        print(f"[ANNOTATION] Fill {TEMPLATE_PATH}, save it as the final CSV, then rerun.")
        return

    rows = evaluation_rows(records, sample, annotations)
    print_report(records, rows)

    if args.stability:
        print()
        run_stability_check(rows, repeats=args.repeats, threshold=args.threshold)


if __name__ == "__main__":
    main()
