"""Extract clean title and reference number from eProcure bracketed strings.

eProcure titles come in the format::

    [Title text that may contain [nested] brackets] [Reference Number]

The outermost bracket pair from the *right* is always the reference number.
Everything before it (including any nested brackets) is the title.
"""

from __future__ import annotations

import re


def extract_title(raw: str) -> tuple[str, str | None]:
    """Extract (title, reference) from an eProcure-style bracketed string.

    Rules
    -----
    1. Scan ``raw`` from right to left and locate the *last* matching pair of
       square brackets ``[...]``.  This pair is the **reference number**.
    2. Everything that appears *before* that final pair (including any nested
       brackets) is the **title**.
    3. If no matching bracket pair exists, return ``(raw, None)``.
    4. Surrounding whitespace is stripped from both components.
    5. Empty titles after stripping raise :py:class:`ValueError`.

    Parameters
    ----------
    raw:
        The raw title string, e.g.::

            "[Supply of [DRDO] Equipment [Model-X]] [REF-123/2026]"

    Returns
    -------
    tuple
        ``(title, reference)`` where *reference* may be ``None``.

    Raises
    ------
    ValueError
        If *raw* is empty or the extracted title is empty after stripping.
    TypeError
        If *raw* is not a string.

    Examples
    --------
    >>> extract_title("[ Repairs and Maintenance ] [02/AE/2026]")
    ('Repairs and Maintenance', '02/AE/2026')

    >>> extract_title("[Dimension test [2.5m x 1.5m]] [DIM-2026/01]")
    ('Dimension test [2.5m x 1.5m]', 'DIM-2026/01')
    """
    if not isinstance(raw, str):
        raise TypeError(f"expected str, got {type(raw).__name__}")

    stripped = raw.strip()
    if not stripped:
        raise ValueError("raw string cannot be empty or whitespace-only")

    # Find the last matching pair of brackets by scanning from the right.
    # We look for the rightmost ']' then walk back to its matching '['.
    ref: str | None = None
    title = stripped

    # Locate the last ']' in the string.
    close_idx = stripped.rfind("]")
    if close_idx == -1:
        # No brackets at all; the whole string is the title.
        return _clean(title), None

    # Find the corresponding '[' by scanning left from close_idx.
    open_idx = stripped.rfind("[", 0, close_idx)
    if open_idx == -1:
        # Unmatched ']' — malformed, treat whole string as title.
        return _clean(title), None

    # Extract reference and title.
    ref = stripped[open_idx + 1 : close_idx].strip()
    title = stripped[:open_idx].strip()

    # If there is no title before the reference, the reference may actually
    # be the title (e.g. "[SomeTitle]" with no separate ref).
    if not title:
        title = f"[{ref}]"
        ref = None

    cleaned_title = _clean(title)
    if not cleaned_title:
        raise ValueError("extracted title is empty after cleaning")

    return cleaned_title, ref if ref else None


def _clean(text: str) -> str:
    """Remove surrounding brackets and whitespace, keep inner content intact."""
    text = text.strip()
    # Remove exactly one pair of outer brackets if they wrap the whole string.
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return inner
    return text
