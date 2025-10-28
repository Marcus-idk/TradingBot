"""
News classification stub.

The refactored pipeline relies on per-symbol importance flags stored in `news_symbols`,
so this module currently returns no additional metadata. It remains as an extension
point for future LLM-based classifiers.
"""

import logging

from data.models import NewsEntry, NewsSymbol

logger = logging.getLogger(__name__)


def classify(news_entries: list[NewsEntry]) -> list[NewsSymbol]:
    """
    Stub classifier for news entries.

    Args:
        news_entries: List of NewsEntry objects to evaluate.

    Returns:
        Empty list; routing is handled elsewhere.
    """
    if news_entries:
        logger.debug("News classifier stub invoked but no labels are generated.")
    return []
