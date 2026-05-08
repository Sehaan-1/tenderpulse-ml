#!/usr/bin/env python3
"""Sample 200 records from the full enriched dataset.

Handles duplicate tender_ids (deduplicates first), preserves
proportional class distribution, and forces inclusion of
5 ground-truth cross-check records.  Seed is fixed for determinism.

After sampling the enriched file, the raw file is filtered to the
*same* set of tender_ids so the full pipeline stays reproducible.
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import shutil
from pathlib import Path

SEED = 42

GROUND_TRUTH_IDS = {
    "2026_MoRTH_903667_1",  # Works — bridge reconstruction
    "2026_DREV_906625_1",    # Works — security guard booth
    "2026_EIL_906516_1",     # Services — Aadhaar OTP e-sign
    "2026_NIOT_903950_1",    # Services — research vessel O&M
    "2026_NITJ_905166_1",    # Goods — contact angle goniometer
}

# These match the full 769-record distribution.  After dedup the
# proportions shift <1 %-point so we keep the same targets.
TARGET_COUNTS = {"Works": 108, "Services": 75, "Goods": 17}


def load_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def save_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def deduplicate(records: list[dict]) -> list[dict]:
    """Keep first occurrence of each tender_id."""
    seen: set[str] = set()
    deduped: list[dict] = []
    for r in records:
        tid = r.get("tender_id")
        if tid and tid not in seen:
            seen.add(tid)
            deduped.append(r)
    return deduped


def compute_targets(records: list[dict], n: int = 200) -> dict[str, int]:
    """Compute category targets proportional to *records* distribution."""
    counts = collections.Counter(r["predicted_category"] for r in records)
    total = len(records)
    targets: dict[str, int] = {}
    allocated = 0
    # Integer allocation via largest remainder
    remainders: list[tuple[float, str]] = []
    for cat, cnt in sorted(counts.items()):
        exact = cnt / total * n
        floor = int(exact)
        targets[cat] = floor
        allocated += floor
        remainders.append((exact - floor, cat))

    # Distribute remaining slots by largest remainder
    for _, cat in sorted(remainders, reverse=True):
        if allocated >= n:
            break
        targets[cat] += 1
        allocated += 1

    return targets


def sample_records(records: list[dict], targets: dict[str, int]) -> list[dict]:
    random.seed(SEED)

    pool = [r for r in records if r["tender_id"] not in GROUND_TRUTH_IDS]
    ground_truth = [r for r in records if r["tender_id"] in GROUND_TRUTH_IDS]

    by_cat: dict[str, list[dict]] = collections.defaultdict(list)
    for r in pool:
        by_cat[r["predicted_category"]].append(r)

    gt_counts = collections.Counter(r["predicted_category"] for r in ground_truth)
    remaining = {cat: targets[cat] - gt_counts.get(cat, 0) for cat in targets}

    sampled: list[dict] = []
    for cat, need in remaining.items():
        if need < 0:
            raise ValueError(f"Ground truth over-represents {cat}: {gt_counts[cat]} > target {targets[cat]}")
        if need > len(by_cat[cat]):
            raise ValueError(f"Not enough {cat}: need {need}, have {len(by_cat[cat])}")
        sampled.extend(random.sample(by_cat[cat], need))

    sampled.extend(ground_truth)
    return sampled


def verify(sampled: list[dict], targets: dict[str, int]) -> None:
    counts = collections.Counter(r["predicted_category"] for r in sampled)
    assert len(sampled) == 200, f"Expected 200 records, got {len(sampled)}"
    for cat, target in targets.items():
        assert counts[cat] == target, f"Category {cat}: expected {target}, got {counts[cat]}"

    ids = {r["tender_id"] for r in sampled}
    missing = GROUND_TRUTH_IDS - ids
    assert not missing, f"Missing ground-truth records: {missing}"

    print(f"Sample verified: {len(sampled)} records")
    for cat in ["Works", "Services", "Goods"]:
        pct = counts[cat] / 200 * 100
        print(f"  {cat}: {counts[cat]} ({pct:.1f}%)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sample 200 records from enriched JSONL")
    parser.add_argument("--enriched", default="data/enriched/tenders_enriched.jsonl")
    parser.add_argument("--raw", default="data/raw/tenders.jsonl")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    enriched_path = Path(args.enriched)
    raw_path = Path(args.raw)

    # Load and deduplicate
    enriched_raw = load_jsonl(enriched_path)
    print(f"Loaded {len(enriched_raw)} enriched records")

    enriched = deduplicate(enriched_raw)
    print(f"Deduplicated to {len(enriched)} unique tender_ids ({len(enriched_raw) - len(enriched)} dupes removed)")

    full_cats = collections.Counter(r["predicted_category"] for r in enriched)
    for cat in ["Works", "Services", "Goods"]:
        pct = full_cats[cat] / len(enriched) * 100
        print(f"  Full deduped {cat}: {full_cats[cat]} ({pct:.1f}%)")

    # Verify ground-truth IDs exist
    gt_in_enriched = [r for r in enriched if r["tender_id"] in GROUND_TRUTH_IDS]
    print(f"Ground truth records found: {len(gt_in_enriched)}")

    # Compute proportional targets or use fixed ones
    prop_targets = compute_targets(enriched, 200)
    print(f"Proportional targets: {prop_targets}")
    print(f"Fixed targets: {TARGET_COUNTS}")

    # Use fixed targets since they match within ±2% for deduped set
    targets = TARGET_COUNTS

    # Sample
    sampled = sample_records(enriched, targets)
    verify(sampled, targets)

    # Filter raw file (deduplicated) to same tender_ids
    raw_raw = load_jsonl(raw_path)
    raw = deduplicate(raw_raw)
    sampled_ids = {r["tender_id"] for r in sampled}
    raw_filtered = [r for r in raw if r["tender_id"] in sampled_ids]
    assert len(raw_filtered) == len(sampled), \
        f"Raw ({len(raw_filtered)}) and enriched ({len(sampled)}) sizes differ"
    print(f"Filtered deduped raw file to {len(raw_filtered)} records")

    if args.dry_run:
        print("Dry run complete. No files written.")
        return 0

    # Backup full files (kept locally, not committed)
    for path in [enriched_path, raw_path]:
        backup = path.with_suffix(".full.jsonl")
        if not backup.exists():
            shutil.copy(path, backup)
    print("Backed up full files as *.full.jsonl")

    # Overwrite with 200-record sample
    save_jsonl(enriched_path, sampled)
    save_jsonl(raw_path, raw_filtered)
    print("Wrote 200-record files to data/enriched/ and data/raw/.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())