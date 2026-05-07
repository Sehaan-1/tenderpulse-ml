#!/usr/bin/env python3
"""PII scanner for tender JSONL files.

Runs before any data is committed to the repository.  Scans every record
for:

* 10-digit Indian mobile numbers
* ``+91`` prefixes
* landline patterns (area code + number)
* email addresses
* officer name prefixes (Shri, Smt, Dr., Er.)

Usage::

    python scripts/check_pii.py data/raw/tenders.jsonl

Exit code 0 means no PII found; exit code 1 means PII detected.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
_MOBILE_RE = re.compile(r"\b\d{10}\b")
_PLUS91_RE = re.compile(r"\+91[\s\-]?\d{10}")
_LANDLINE_RE = re.compile(r"\b0\d{2,4}[\s\-]?\d{6,8}\b")
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_PREFIX_RE = re.compile(r"\b(Shri|Shree|Smt|Smt\.|Dr\.?|Er\.?|Prof\.?|Mr\.?|Mrs\.?|Ms\.?)\b", re.IGNORECASE)

PATTERNS: dict[str, re.Pattern[str]] = {
    "mobile": _MOBILE_RE,
    "+91": _PLUS91_RE,
    "landline": _LANDLINE_RE,
    "email": _EMAIL_RE,
    "officer_prefix": _PREFIX_RE,
}


def _scan_text(text: str) -> dict[str, list[str]]:
    """Return dict of pattern name → list of matches found in *text*."""
    matches: dict[str, list[str]] = {}
    for name, pattern in PATTERNS.items():
        found = pattern.findall(text)
        if found:
            matches[name] = found
    return matches


def check_file(path: Path) -> list[dict[str, object]]:
    """Scan *path* (JSONL) for PII. Return list of violation dicts."""
    violations: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"[WARN] {path}:{lineno} JSON decode error: {exc}")
                continue

            # Flatten all string values in the record for scanning
            texts: list[str] = []
            for value in record.values():
                if isinstance(value, str):
                    texts.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            texts.append(item)

            full_text = " ".join(texts)
            matches = _scan_text(full_text)
            if matches:
                violations.append({
                    "file": str(path),
                    "line": lineno,
                    "tender_id": record.get("tender_id"),
                    "matches": matches,
                })
    return violations


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Scan JSONL for PII")
    parser.add_argument("file", nargs="?", default="data/raw/tenders.jsonl", help="JSONL file to scan")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return 2

    print(f"Scanning {path} for PII ...")
    violations = check_file(path)

    if not violations:
        print("No PII detected.")
        return 0

    total = 0
    for v in violations:
        count = sum(len(m) for m in v["matches"].values())
        total += count
        print(f"  {v['file']}:{v['line']} (tender_id={v['tender_id']}) -> {v['matches']}")

    print(f"\nFound {total} PII match(es) across {len(violations)} record(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
