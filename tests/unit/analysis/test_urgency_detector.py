"""Unit tests for urgency detection module."""

from analysis.urgency_detector import detect_news_urgency, detect_social_urgency
from tests.factories import make_news_entry, make_social_discussion


def test_detect_news_urgency_returns_empty_list():
    """News detector stub returns empty list for populated entries."""
    entries = [
        make_news_entry(
            symbol="AAPL",
            url="https://example.com/news1",
            headline="Headline 1",
            content="Bankruptcy chatter",
        ),
        make_news_entry(
            symbol="MSFT",
            url="https://example.com/news2",
            headline="Headline 2",
        ),
    ]

    urgent_items = detect_news_urgency(entries)

    assert urgent_items == []


def test_detect_news_urgency_handles_empty_list():
    """News detector stub handles empty input."""
    urgent_items = detect_news_urgency([])

    assert urgent_items == []


def test_detect_news_urgency_extracts_text_from_headline_and_content():
    """News detector accesses headline/content safely even when content is None."""
    entries = [
        make_news_entry(
            symbol="AAPL",
            url="https://example.com/news1",
            headline="Headline 1",
        ),
        make_news_entry(
            symbol="MSFT",
            url="https://example.com/news2",
            headline="Headline 2",
            content="Detailed content about market movement.",
        ),
        make_news_entry(
            symbol="TSLA",
            url="https://example.com/news3",
            headline="Headline 3",
            content=None,
        ),
    ]

    urgent_items = detect_news_urgency(entries)

    assert urgent_items == []


def test_detect_social_urgency_handles_empty_and_content_none():
    """Social detector stub returns empty and tolerates missing content."""
    items = [
        make_social_discussion(
            symbol="AAPL",
            url="https://example.com/social1",
            title="Big rumor",
            content="Comments included",
        ),
        make_social_discussion(
            symbol="MSFT",
            url="https://example.com/social2",
            title="Another thread",
            content=None,
        ),
    ]

    urgent_items = detect_social_urgency(items)

    assert urgent_items == []
