"""Tests for src/classify.py — no network calls, no model download."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.classify import classify_title
from src.title_cleaner import extract_title


# ---------------------------------------------------------------------------
# Helper for consistent mock creation
# ---------------------------------------------------------------------------
def _make_mock_classifier(labels: list[str], scores: list[float]) -> MagicMock:
    """Return a mock zero-shot classifier that returns *labels* and *scores*."""
    mock = MagicMock()
    mock.return_value = {"labels": labels, "scores": scores}
    return mock


# ---------------------------------------------------------------------------
# Extract title (tuple unpacking) Tests
# ---------------------------------------------------------------------------
class TestExtractTitleUnpacking:
    @pytest.mark.parametrize("raw,expected_title,expected_ref", [
        ("[Repairs and Maintenance] [REF-123]", "Repairs and Maintenance", "REF-123"),
        ("[No brackets at all]", "No brackets at all", None),
        ("[Just a title no ref]", "Just a title no ref", None),
    ])
    def test_unpacking(self, raw: str, expected_title: str, expected_ref: str | None) -> None:
        title, ref = extract_title(raw)
        assert title == expected_title
        assert ref == expected_ref

    def test_missing_ref(self) -> None:
        raw = "Supply of Office Furniture with no brackets at all"
        title, ref = extract_title(raw)
        assert isinstance(title, str)
        assert ref is None
        assert len(title) > 0


# ---------------------------------------------------------------------------
# Confidence Bounds Tests
# ---------------------------------------------------------------------------
class TestConfidenceBounds:
    def test_confidence_values_are_floats_in_range(self) -> None:
        mock = _make_mock_classifier(["Goods"], [0.92])
        label, score = classify_title("any title", mock)
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)

    def test_low_confidence_is_valid(self) -> None:
        mock = _make_mock_classifier(["Services"], [0.12])
        label, score = classify_title("any title", mock)
        assert 0.0 <= score <= 1.0

    def test_perfect_confidence_is_valid(self) -> None:
        mock = _make_mock_classifier(["Works"], [1.0])
        label, score = classify_title("any title", mock)
        assert score == 1.0

    def test_zero_confidence_is_valid(self) -> None:
        mock = _make_mock_classifier(["Goods"], [0.0])
        label, score = classify_title("any title", mock)
        assert score == 0.0


# ---------------------------------------------------------------------------
# Original Fields Preserved Tests
# ---------------------------------------------------------------------------
class TestOriginalFieldsPreserved:
    def test_all_original_keys_present(self) -> None:
        record = self._sample_record()
        original_keys = set(record.keys())

        mock = _make_mock_classifier(["Goods"], [0.95])
        label, score = classify_title("any title", mock)
        record["predicted_category"] = label
        record["category_confidence"] = score

        assert original_keys.issubset(record.keys())

    def test_original_values_untouched(self) -> None:
        record = self._sample_record()
        original = json.dumps(record, sort_keys=True)

        mock = _make_mock_classifier(["Services"], [0.88])
        label, score = classify_title("any title", mock)
        record["predicted_category"] = label
        record["category_confidence"] = score

        assert json.dumps(record, sort_keys=True) != original  # New fields added
        for k, v in json.loads(original).items():
            assert record[k] == v

    @staticmethod
    def _sample_record() -> dict:
        return {
            "source": "eprocure",
            "tender_id": "2026_TEST_001",
            "title": "[Sample Title] [REF-1]",
            "reference_number": None,
            "org_chain": "Test Org",
            "tender_type": None,
            "category": None,
            "tender_value": None,
            "emd_amount": None,
            "doc_fee": None,
            "currency": "INR",
            "closing_date": "2026-05-08T09:00:00",
            "opening_date": "2026-05-09T09:00:00",
            "published_date": "2026-04-24T10:00:00",
            "detail_url": "https://example.com/tender/1",
            "attachments": [],
            "meta": {"run_id": None, "task_id": None, "fetched_at": None, "fetcher_used": "test", "parse_version": "1.0"},
            "raw_json": None,
        }


# ---------------------------------------------------------------------------
# New Fields Added Tests
# ---------------------------------------------------------------------------
class TestNewFieldsAdded:
    def test_predicted_category_is_one_of_level1(self) -> None:
        for cat in ["Goods", "Services", "Works"]:
            mock = _make_mock_classifier([cat], [0.9])
            label, _ = classify_title("any title", mock)
            assert label in {"Goods", "Services", "Works"}

    def test_category_confidence_is_float(self) -> None:
        mock = _make_mock_classifier(["Goods"], [0.75])
        _, score = classify_title("any title", mock)
        assert isinstance(score, float)


# ---------------------------------------------------------------------------
# Missing Ref Handling Tests
# ---------------------------------------------------------------------------
class TestMissingRefHandling:
    def test_no_bracket_title(self) -> None:
        raw = "Supply of Office Furniture with no brackets"
        title, ref = extract_title(raw)
        assert title == raw
        assert ref is None

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValueError):
            extract_title("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError):
            extract_title("   \n\t  ")


# ---------------------------------------------------------------------------
# JSONL Roundtrip Tests
# ---------------------------------------------------------------------------
class TestJsonlRoundtrip:
    def test_single_record_roundtrip(self, tmp_path: Path) -> None:
        record = {
            "tender_id": "TEST-001",
            "title": "[Sample] [REF]",
            "predicted_category": "Goods",
            "category_confidence": 0.95,
        }
        path = tmp_path / "test.jsonl"
        path.write_text(json.dumps(record) + "\n", encoding="utf-8")

        read = json.loads(path.read_text(encoding="utf-8").strip())
        assert read["predicted_category"] == "Goods"
        assert read["category_confidence"] == 0.95

    def test_multiple_records_roundtrip(self, tmp_path: Path) -> None:
        records = [
            {"tender_id": f"TEST-{i:03d}", "predicted_category": ["Goods", "Services", "Works"][i % 3], "category_confidence": 0.5 + (i * 0.1)}
            for i in range(5)
        ]
        path = tmp_path / "test.jsonl"
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")

        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == len(records)
        for line in lines:
            obj = json.loads(line)
            assert "predicted_category" in obj
            assert "category_confidence" in obj

    def test_line_count_matches_input(self, tmp_path: Path) -> None:
        input_lines = ["{}"] * 10
        path = tmp_path / "test.jsonl"
        path.write_text("".join(json.dumps({"predicted_category": "Goods", "category_confidence": 0.9}) + "\n" for _ in input_lines), encoding="utf-8")

        output_lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(output_lines) == len(input_lines)