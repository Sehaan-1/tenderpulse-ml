"""Level 1 zero-shot classification CLI using BART-large-mnli."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure src/ is on path when running as script
if __package__ is None or __package__ == "":
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_PROJECT_ROOT))
    from src.labels import LEVEL1_CANDIDATES, LEVEL1_HYPOTHESIS
    from src.title_cleaner import extract_title
else:
    from src.labels import LEVEL1_CANDIDATES, LEVEL1_HYPOTHESIS
    from src.title_cleaner import extract_title

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)


def classify_title(title: str, classifier) -> tuple[str, float]:
    """Classify title into one LEVEL1_CANDIDATE using BART zero-shot.

    Returns
    -------
    tuple
        (predicted_category, confidence)

    Notes
    -----
    - The caller owns the classifier lifecycle so the model is loaded once.
    - If the top label is not in LEVEL1_CANDIDATES (e.g. a subword
      tokenisation artifact), the highest-scoring *valid* label is used
      and a warning is logged.
    """
    result = classifier(
        title,
        candidate_labels=LEVEL1_CANDIDATES,
        hypothesis_template=LEVEL1_HYPOTHESIS,
    )

    labels = result["labels"]
    scores = result["scores"]

    top_label = labels[0]
    top_score = scores[0]

    if top_label in LEVEL1_CANDIDATES:
        return top_label, float(top_score)

    logger.warning(
        "Unexpected top label '%s' for title '%s'. Falling back.",
        top_label,
        title[:60],
    )

    for label, score in zip(labels, scores):
        if label in LEVEL1_CANDIDATES:
            return label, float(score)

    logger.error(
        "No valid candidate found for title '%s'. Returning 'Goods' fallback.",
        title[:60],
    )
    return "Goods", 0.0


def run(input_path: Path, output_path: Path) -> None:
    """Run classification pipeline on a JSONL file."""
    from transformers import pipeline

    local_model_path = str(Path(__file__).resolve().parent.parent / "models" / "bart-large-mnli")
    logger.info("Loading BART-large-mnli model from %s (one-time load)...", local_model_path)
    classifier = pipeline(
        "zero-shot-classification",
        model=local_model_path,
    )

    logger.info("Processing records from %s", input_path)
    classified = 0
    errors = 0

    with (
        open(input_path, encoding="utf-8") as infile,
        open(output_path, "w", encoding="utf-8") as outfile,
    ):
        for line in infile:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                logger.warning("Skipping malformed JSON line: %s", exc)
                errors += 1
                continue

            title_raw = record.get("title", "")

            try:
                clean_title, _ = extract_title(title_raw)
            except (ValueError, TypeError) as exc:
                logger.warning(
                    "extract_title failed for '%s': %s. Using raw title.",
                    title_raw[:60],
                    exc,
                )
                clean_title = title_raw.strip()

            predicted_category, category_confidence = classify_title(
                clean_title, classifier
            )

            record["predicted_category"] = predicted_category
            record["category_confidence"] = category_confidence

            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
            classified += 1

            if classified % 100 == 0:
                logger.info("Classified %d records...", classified)

    logger.info(
        "Done. Classified %d records (%d errors). Output: %s",
        classified,
        errors,
        output_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Level 1 zero-shot tender classification.",
    )
    parser.add_argument(
        "--input",
        dest="input_path",
        required=True,
        type=Path,
        help="Input JSONL path",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        required=True,
        type=Path,
        help="Output JSONL path",
    )
    args = parser.parse_args()

    if not args.input_path.exists():
        parser.error(f"Input file not found: {args.input_path}")

    run(args.input_path, args.output_path)


if __name__ == "__main__":
    main()
