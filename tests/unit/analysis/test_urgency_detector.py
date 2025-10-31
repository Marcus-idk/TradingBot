"""Unit tests for urgency detection module."""

from datetime import UTC, datetime

from analysis.urgency_detector import detect_urgency
from data.models import NewsEntry, NewsItem, NewsType


def _make_entry(
    *,
    symbol: str,
    url_suffix: str,
    content: str | None = None,
) -> NewsEntry:
    article = NewsItem(
        url=f"https://example.com/news{url_suffix}",
        headline=f"Headline {url_suffix}",
        published=datetime(2024, 1, 15, 12, 0, tzinfo=UTC),
        source="UnitTest",
        news_type=NewsType.COMPANY_SPECIFIC,
        content=content,
    )
    return NewsEntry(article=article, symbol=symbol)


def test_detect_urgency_returns_empty_list():
    """Detector stub returns empty list for populated entries."""
    entries = [
        _make_entry(symbol="AAPL", url_suffix="1", content="Bankruptcy chatter"),
        _make_entry(symbol="MSFT", url_suffix="2"),
    ]

    urgent_items = detect_urgency(entries)

    assert urgent_items == []


def test_detect_urgency_handles_empty_list():
    """Detector stub handles empty input."""
    urgent_items = detect_urgency([])

    assert urgent_items == []


def test_detect_urgency_extracts_text_from_headline_and_content():
    """Detector accesses headline/content safely even when content is None."""
    entries = [
        _make_entry(symbol="AAPL", url_suffix="1"),
        _make_entry(
            symbol="MSFT",
            url_suffix="2",
            content="Detailed content about market movement.",
        ),
        _make_entry(symbol="TSLA", url_suffix="3", content=None),
    ]

    urgent_items = detect_urgency(entries)

    assert urgent_items == []
