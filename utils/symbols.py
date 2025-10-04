"""
Helpers for parsing and filtering symbol lists.

Follow Writing_Code.md: simple, clear, and consistent utilities.
"""

import logging
from typing import Iterable


logger = logging.getLogger(__name__)


def parse_symbols(
    raw: str | None,
    filter_to: Iterable[str] | None = None,
    *,
    validate: bool = True,
    log_label: str = "SYMBOLS",
) -> list[str]:
    """
    Parse a comma-separated string into an order-preserving, deduplicated list of
    uppercase symbols. Optionally filter to a watchlist and validate shape.

    - Trims/uppercases
    - Deduplicates while preserving order
    - If `filter_to` is provided, returns only symbols present in that set
    - If `validate` is True, enforce 1-5 A-Z and log anomalies at DEBUG
    """

    if not raw or not isinstance(raw, str) or not raw.strip():
        return []

    # Build watchlist filter set for fast lookup
    allow: set[str] | None = None
    if filter_to is not None:
        allow = {s.strip().upper() for s in filter_to if isinstance(s, str) and s.strip()}

    tokens = [s.strip().upper() for s in raw.split(",") if s and s.strip()]

    out: list[str] = []
    seen: set[str] = set()

    for sym in tokens:
        # Skip duplicates
        if sym in seen:
            continue

        # Validate format: 1-5 uppercase letters only
        if validate and not (sym.isalpha() and 1 <= len(sym) <= 5):
            logger.debug(f"Unexpected {log_label} entry format: {sym}")
            continue

        # Filter to watchlist if provided
        if allow is not None and sym not in allow:
            continue

        out.append(sym)
        seen.add(sym)

    return out
