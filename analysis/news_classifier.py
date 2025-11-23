"""News classification helpers for downstream routing.

Notes:
    Stub implementation; returns no additional classification metadata. Routing
    and importance are driven by per-symbol importance flags stored in
    ``news_symbols``.
"""

import logging

from data.models import NewsEntry, NewsSymbol

logger = logging.getLogger(__name__)


def classify(news_entries: list[NewsEntry]) -> list[NewsSymbol]:
    """Classify news entries for downstream routing.

    Notes:
        Returns an empty list; no additional labels are generated. Routing and
        importance are handled outside this function using per-symbol
        importance flags.
    """
    if news_entries:
        logger.debug("News classifier stub invoked but no labels are generated.")
    return []
