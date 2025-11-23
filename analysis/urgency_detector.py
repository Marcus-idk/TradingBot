"""Urgency detection helpers for news entries.

Notes:
    Stub implementation; returns no urgent items. No urgency classification
    is performed.
"""

import logging

from data.models import NewsEntry

logger = logging.getLogger(__name__)


def detect_urgency(news_entries: list[NewsEntry]) -> list[NewsEntry]:
    """Detect urgent news items that require immediate attention.

    Notes:
        Stub implementation that always returns an empty list; no urgency
        classification is performed.
    """
    urgent: list[NewsEntry] = []

    if not news_entries:
        return urgent

    # Stub loop: no classification yet
    total_chars = 0
    for item in news_entries:
        # Combine headline and content length for logging
        total_chars += len(item.headline)
        if item.content:
            total_chars += len(item.content)
    logger.debug(
        f"Analyzed {len(news_entries)} news entries for urgency (stub) — text_len={total_chars}"
    )

    # Always return empty for now
    return urgent
