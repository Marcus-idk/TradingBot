"""
Live integration tests for Polygon providers leveraging the real API.
"""

import os
from datetime import datetime, timedelta, timezone

import pytest

from config.providers.polygon import PolygonSettings
from data.models import NewsItem
from data.providers.polygon import PolygonNewsProvider

pytestmark = [pytest.mark.network, pytest.mark.asyncio]


async def test_live_news_fetch():
    """Fetch real company news for AAPL."""
    if not os.environ.get("POLYGON_API_KEY"):
        pytest.skip("POLYGON_API_KEY not set, skipping live test")

    try:
        settings = PolygonSettings.from_env()
    except ValueError:
        pytest.skip("POLYGON_API_KEY not configured properly")

    provider = PolygonNewsProvider(settings, ["AAPL"])
    # Validate connection first
    assert await provider.validate_connection() is True, "connection should validate"
    since = datetime.now(timezone.utc) - timedelta(days=2)
    results = await provider.fetch_incremental(since=since)

    assert isinstance(results, list), "fetch_incremental should return a list"

    if results:
        article = results[0]
        assert isinstance(article, NewsItem), "should return NewsItem instances"
        assert article.symbol == "AAPL", "fetched symbol should match request"
        assert article.headline and len(article.headline) > 0, "headline should be non-empty"
        assert article.url and article.url.startswith("http"), "url should be http(s)"
        assert article.published.tzinfo == timezone.utc, "timestamps must be UTC"
        assert article.source is not None, "source should be present"
    else:
        pass


async def test_live_multiple_symbols():
    """Fetch company news for multiple symbols (at least one should have items)."""
    if not os.environ.get("POLYGON_API_KEY"):
        pytest.skip("POLYGON_API_KEY not set, skipping live test")

    try:
        settings = PolygonSettings.from_env()
    except ValueError:
        pytest.skip("POLYGON_API_KEY not configured properly")

    symbols = ["AAPL", "MSFT", "GOOGL"]
    provider = PolygonNewsProvider(settings, symbols)
    # Validate connection first (mirror Finnhub style)
    assert await provider.validate_connection() is True, "connection should validate"

    since = datetime.now(timezone.utc) - timedelta(days=2)
    results = await provider.fetch_incremental(since=since)

    assert isinstance(results, list), "fetch_incremental should return a list"
    fetched_symbols = {r.symbol for r in results}
    # At least one symbol should have data (news may be sparse)
    assert len(fetched_symbols) >= 1, "should fetch at least one symbol"

    for item in results:
        assert item.symbol in symbols, "item symbol should be from requested set"
        assert item.headline and item.url.startswith("http"), "headline present and url http(s)"


async def test_live_error_handling():
    """Invalid symbol should be handled gracefully (empty or valid items)."""
    if not os.environ.get("POLYGON_API_KEY"):
        pytest.skip("POLYGON_API_KEY not set, skipping live test")

    try:
        settings = PolygonSettings.from_env()
    except ValueError:
        pytest.skip("POLYGON_API_KEY not configured properly")

    provider = PolygonNewsProvider(settings, ["INVALID_SYMBOL_XYZ123"])
    results = await provider.fetch_incremental(since=datetime.now(timezone.utc) - timedelta(days=2))
    assert (
        len(results) == 0 or all(r.headline and r.url.startswith("http") for r in results)
    ), "invalid symbol should yield no results or valid-shaped items"
