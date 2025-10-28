"""
Urgency detection module (stub).

For v0.3.3 this is a no-op detector that returns an empty list. It
exists to establish the extension point for future LLM-based analysis.
"""

import logging

from data.models import NewsEntry

logger = logging.getLogger(__name__)


def detect_urgency(news_entries: list[NewsEntry]) -> list[NewsEntry]:
    """
    Detect urgent news items that require immediate attention.

    Analyzes headline and content text for urgent keywords.

    Args:
        news_entries: List of NewsEntry objects to analyze

    Returns:
        List of NewsItem objects flagged as urgent (empty for stub implementation)

    Note:
        Current implementation is a stub that always returns empty list.
        Future versions (v0.5) will use LLM to analyze text for urgent keywords like
        bankruptcy, SEC investigation, etc.
    """
    urgent: list[NewsEntry] = []

    if not news_entries:
        return urgent

    # Stub loop: exercise basic access; no classification yet
    if logger.isEnabledFor(logging.DEBUG):
        total_chars = 0
        for item in news_entries:
            # Access headline/content safely; accumulate length for lightweight debug metric
            total_chars += len(item.headline)
            if item.content:
                total_chars += len(item.content)
        logger.debug(
            f"Analyzed {len(news_entries)} news entries for urgency (stub) — text_len={total_chars}"
        )

    # Always return empty for v0.3.3
    return urgent
