"""Unit tests for the news classifier stub."""

from datetime import UTC, datetime

from analysis.news_classifier import classify
from data.models import NewsEntry, NewsItem, NewsType


def _make_entry(symbol: str, url_suffix: str) -> NewsEntry:
    article = NewsItem(
        url=f"https://example.com/news{url_suffix}",
        headline=f"Headline {url_suffix}",
        published=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        source="UnitTest",
        news_type=NewsType.COMPANY_SPECIFIC,
        content=None,
    )
    return NewsEntry(article=article, symbol=symbol)


def test_classify_returns_empty_list_for_any_input():
    """Stub classifier returns empty list regardless of entries provided."""
    entries = [_make_entry("AAPL", "1"), _make_entry("MSFT", "2")]

    labels = classify(entries)

    assert labels == []


def test_classify_handles_empty_list():
    """Classifier handles empty input without logging debug path."""
    labels = classify([])

    assert labels == []
