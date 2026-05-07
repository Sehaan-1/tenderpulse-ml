"""Tests for src/title_cleaner.py — 20 explicit cases."""

from __future__ import annotations

import pytest

from src.title_cleaner import extract_title


# ---------------------------------------------------------------------------
# Basic happy-path
# ---------------------------------------------------------------------------
def test_basic_title_and_ref() -> None:
    """Standard [Title] [Ref] format."""
    raw = "[Repairs and Maintenance of DI Quarters] [09/PCDH/2026-27]"
    title, ref = extract_title(raw)
    assert title == "Repairs and Maintenance of DI Quarters"
    assert ref == "09/PCDH/2026-27"


def test_title_with_dashes_and_slashes() -> None:
    """Reference containing slashes and dashes."""
    raw = "[Supply of Real Time PCR on Reagent Rental Basis] [HBCH/MPMMCC/RC/ST/29/KH]"
    title, ref = extract_title(raw)
    assert title == "Supply of Real Time PCR on Reagent Rental Basis"
    assert ref == "HBCH/MPMMCC/RC/ST/29/KH"


def test_multiple_words_in_ref() -> None:
    """Reference that looks like a sentence (edge case)."""
    raw = "[PRE TENDER MEET] [PRE-TENDER MEET FOR SWITCHBOARD-MV OF HPCL PROJECT]"
    title, ref = extract_title(raw)
    assert title == "PRE TENDER MEET"
    assert ref == "PRE-TENDER MEET FOR SWITCHBOARD-MV OF HPCL PROJECT"


# ---------------------------------------------------------------------------
# Edge: missing reference
# ---------------------------------------------------------------------------
def test_missing_ref() -> None:
    """Title without a trailing reference pair."""
    raw = "[Running Operation Maintenance and Management of NIOT Research Vessel]"
    title, ref = extract_title(raw)
    assert title == "Running Operation Maintenance and Management of NIOT Research Vessel"
    assert ref is None


def test_missing_ref_with_text_after() -> None:
    """No brackets after the title — ref should be None."""
    raw = "[Construction of Security Guard Booth]"
    title, ref = extract_title(raw)
    assert title == "Construction of Security Guard Booth"
    assert ref is None


# ---------------------------------------------------------------------------
# Edge: empty / whitespace
# ---------------------------------------------------------------------------
def test_empty_string_raises() -> None:
    """Empty input must raise ValueError."""
    with pytest.raises(ValueError):
        extract_title("")


def test_whitespace_only_raises() -> None:
    """Whitespace-only input must raise ValueError."""
    with pytest.raises(ValueError):
        extract_title("   \n\t  ")


# ---------------------------------------------------------------------------
# Edge: all caps, punctuation-heavy
# ---------------------------------------------------------------------------
def test_all_caps_title() -> None:
    """All-caps title with punctuation."""
    raw = "[PROCUREMENT OF AADHAR OTP BASED E-SIGN SERVICES] [DC/8589-000-SE-T-5036/94]"
    title, ref = extract_title(raw)
    assert title == "PROCUREMENT OF AADHAR OTP BASED E-SIGN SERVICES"
    assert ref == "DC/8589-000-SE-T-5036/94"


def test_punctuation_heavy() -> None:
    """Title full of commas, parentheses, hyphens."""
    raw = "[Assistance for Breakdown maintenance/skilled Jobs at Offsite Area (Bagging plant, Ammonia handling area, PAT area)] [4024/2025-2026/E33347]"
    title, ref = extract_title(raw)
    assert title == "Assistance for Breakdown maintenance/skilled Jobs at Offsite Area (Bagging plant, Ammonia handling area, PAT area)"
    assert ref == "4024/2025-2026/E33347"


# ---------------------------------------------------------------------------
# Edge: nested brackets inside title (explicit #3)
# ---------------------------------------------------------------------------
def test_nested_brackets_in_title() -> None:
    """Nested square brackets inside the title portion must be preserved."""
    raw = "[Provision of Signal Booster [DRDO] for the facility] [EMU/BAN/BOOSTER/01/2026-27]"
    title, ref = extract_title(raw)
    assert title == "Provision of Signal Booster [DRDO] for the facility"
    assert ref == "EMU/BAN/BOOSTER/01/2026-27"


def test_multiple_nested_brackets() -> None:
    """Multiple nested bracket pairs inside title."""
    raw = "[Repair of [Model-A] and [Model-B] equipment at [HQ] location] [MAINT-2026/04]"
    title, ref = extract_title(raw)
    assert title == "Repair of [Model-A] and [Model-B] equipment at [HQ] location"
    assert ref == "MAINT-2026/04"


# ---------------------------------------------------------------------------
# Edge: dimensions in brackets (explicit #4)
# ---------------------------------------------------------------------------
def test_dimensions_in_brackets() -> None:
    """Dimensions like [2.5m x 1.5m] inside the title must be preserved."""
    raw = "[Construction of Shed [2.5m x 1.5m] at Site-7] [PWD-DEL/2026-27/18]"
    title, ref = extract_title(raw)
    assert title == "Construction of Shed [2.5m x 1.5m] at Site-7"
    assert ref == "PWD-DEL/2026-27/18"


def test_multiple_dimensions() -> None:
    """Multiple dimension specs inside title."""
    raw = "[Fabrication of Frame [3.0m x 2.0m] and Panel [1.5m x 1.5m]] [FAB/2026/12]"
    title, ref = extract_title(raw)
    assert title == "Fabrication of Frame [3.0m x 2.0m] and Panel [1.5m x 1.5m]"
    assert ref == "FAB/2026/12"


# ---------------------------------------------------------------------------
# Edge: Hindi / Unicode
# ---------------------------------------------------------------------------
def test_hindi_in_title() -> None:
    """Hindi unicode text inside the title."""
    raw = "[सड़क निर्माण कार्य NH-157] [14 CE NH of 2025-26]"
    title, ref = extract_title(raw)
    assert title == "सड़क निर्माण कार्य NH-157"
    assert ref == "14 CE NH of 2025-26"


# ---------------------------------------------------------------------------
# Edge: numeric-only ref, complex ref
# ---------------------------------------------------------------------------
def test_numeric_ref() -> None:
    """Reference that is just a number."""
    raw = "[Day to Day Electrical Maintenance] [02]"
    title, ref = extract_title(raw)
    assert title == "Day to Day Electrical Maintenance"
    assert ref == "02"


def test_alphanumeric_mixed_ref() -> None:
    """Reference with letters, numbers, slashes, dashes."""
    raw = "[Extension of DG sets stacks] [PGI/Engg./Elect./2026-27/03]"
    title, ref = extract_title(raw)
    assert title == "Extension of DG sets stacks"
    assert ref == "PGI/Engg./Elect./2026-27/03"


# ---------------------------------------------------------------------------
# Edge: only a single bracket pair (title only, no ref)
# ---------------------------------------------------------------------------
def test_single_pair_no_ref() -> None:
    """A single pair of brackets — the whole thing is the title."""
    raw = "[Renovation of IWC and GOs section at Pushpa Bhawan]"
    title, ref = extract_title(raw)
    assert title == "Renovation of IWC and GOs section at Pushpa Bhawan"
    assert ref is None


# ---------------------------------------------------------------------------
# Edge: title and ref are identical (duplicate bracket)
# ---------------------------------------------------------------------------
def test_duplicate_brackets() -> None:
    """Both pairs contain the exact same text — last pair wins as ref."""
    raw = "[VIII.11011/33 AR/Engr-MW/NIT/2026-27/16] [VIII.11011/33 AR/Engr-MW/NIT/2026-27/16]"
    title, ref = extract_title(raw)
    assert title == "VIII.11011/33 AR/Engr-MW/NIT/2026-27/16"
    assert ref == "VIII.11011/33 AR/Engr-MW/NIT/2026-27/16"


# ---------------------------------------------------------------------------
# Edge: extra whitespace, mixed spacing
# ---------------------------------------------------------------------------
def test_leading_trailing_whitespace() -> None:
    """Leading/trailing spaces around the whole string."""
    raw = "  [  Construction of Toilet Block  ]  [  REF/123  ]  "
    title, ref = extract_title(raw)
    assert title == "Construction of Toilet Block"
    assert ref == "REF/123"


def test_no_brackets_at_all() -> None:
    """Free-form title with no brackets — title is whole string, ref is None."""
    raw = "Free form tender title without any brackets"
    title, ref = extract_title(raw)
    assert title == "Free form tender title without any brackets"
    assert ref is None


# ---------------------------------------------------------------------------
# Edge: Type safety
# ---------------------------------------------------------------------------
def test_non_string_input_raises() -> None:
    """Passing a non-string must raise TypeError."""
    with pytest.raises(TypeError):
        extract_title(123)  # type: ignore[arg-type]
