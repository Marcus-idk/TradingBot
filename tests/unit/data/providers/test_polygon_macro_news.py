"""Polygon-specific macro news tests (complement contract coverage)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from config.providers.polygon import PolygonSettings
from data import DataSourceError
from data.providers.polygon import PolygonMacroNewsProvider
from data.storage.storage_utils import _datetime_to_iso

pytestmark = pytest.mark.asyncio


class TestPolygonMacroNewsProvider:
    """Targeted Polygon-only behaviors not covered by contracts."""

    async def test_fetch_incremental_handles_pagination(self, monkeypatch):
        """Test fetch incremental handles pagination."""
        settings = PolygonSettings(api_key="test_key")
        provider = PolygonMacroNewsProvider(settings, ["AAPL"])

        fixed_now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)

        class MockDatetime:
            @staticmethod
            def now(tz):
                return fixed_now

            @staticmethod
            def fromtimestamp(ts, tz):
                return datetime.fromtimestamp(ts, tz)

        monkeypatch.setattr(
            "data.providers.polygon.polygon_macro_news.datetime",
            MockDatetime,
        )

        now_iso = _datetime_to_iso(fixed_now)
        page1 = {
            "results": [
                {
                    "title": "A",
                    "article_url": "https://example.com/a",
                    "published_utc": now_iso,
                    "tickers": ["AAPL"],
                    "publisher": {"name": "SourceA"},
                    "description": "Desc A",
                }
            ],
            "next_url": "https://api.polygon.io/v2/reference/news?cursor=abc123",
        }
        page2 = {
            "results": [
                {
                    "title": "B",
                    "article_url": "https://example.com/b",
                    "published_utc": now_iso,
                    "tickers": ["AAPL"],
                    "publisher": {"name": "SourceB"},
                    "description": "Desc B",
                }
            ]
        }

        responses = [page1, page2]
        call_count = {"n": 0}

        async def mock_get(path: str, params: dict | None = None):
            idx = call_count["n"]
            call_count["n"] += 1
            return responses[idx]

        provider.client.get = mock_get

        result = await provider.fetch_incremental()

        # Each page yields one NewsItem mapped to 'AAPL'
        assert len(result) == 2
        assert call_count["n"] == 2
        assert all(item.is_important is None for item in result)

    async def test_since_buffer_applied(self):
        """Test since buffer applied."""
        settings = PolygonSettings(api_key="test_key")
        provider = PolygonMacroNewsProvider(settings, ["AAPL"])

        captured: dict[str, dict] = {}

        async def mock_get(path: str, params: dict | None = None):
            captured["params"] = dict(params or {})
            return {"results": []}

        provider.client.get = mock_get

        since = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)
        await provider.fetch_incremental(since=since)

        expected_cutoff = _datetime_to_iso(since - timedelta(minutes=2))
        assert captured["params"]["published_utc.gt"] == expected_cutoff

    async def test_empty_results_stops_pagination(self):
        """Test empty results stops pagination."""
        settings = PolygonSettings(api_key="test_key")
        provider = PolygonMacroNewsProvider(settings, ["AAPL"])

        call_count = {"n": 0}

        async def mock_get(path: str, params: dict | None = None):
            call_count["n"] += 1
            return {"results": []}

        provider.client.get = mock_get

        result = await provider.fetch_incremental()

        assert result == []
        assert call_count["n"] == 1

    async def test_fetch_incremental_missing_results_raises(self):
        """Missing results key is treated as a schema/contract error."""
        settings = PolygonSettings(api_key="test_key")
        provider = PolygonMacroNewsProvider(settings, ["AAPL"])

        provider.client.get = AsyncMock(return_value={"count": 1})

        with pytest.raises(DataSourceError, match="missing 'results'"):
            await provider.fetch_incremental()

    async def test_next_url_without_cursor_stops_pagination(self, monkeypatch):
        """Test next url without cursor stops pagination."""
        settings = PolygonSettings(api_key="test_key")
        provider = PolygonMacroNewsProvider(settings, ["AAPL"])

        fixed_now = datetime(2024, 1, 15, 12, 0, tzinfo=UTC)

        class MockDatetime:
            @staticmethod
            def now(tz):
                return fixed_now

            @staticmethod
            def fromtimestamp(ts, tz):
                return datetime.fromtimestamp(ts, tz)

        monkeypatch.setattr(
            "data.providers.polygon.polygon_macro_news.datetime",
            MockDatetime,
        )

        now_iso = _datetime_to_iso(fixed_now)
        page = {
            "results": [
                {
                    "title": "A",
                    "article_url": "https://example.com/a",
                    "published_utc": now_iso,
                    "tickers": ["AAPL"],
                    "publisher": {"name": "SourceA"},
                    "description": "Desc A",
                }
            ],
            "next_url": "https://api.polygon.io/v2/reference/news?nocursor",
        }

        provider.client.get = AsyncMock(return_value=page)

        result = await provider.fetch_incremental()

        assert len(result) == 1
        provider.client.get.assert_awaited_once()

    @pytest.mark.parametrize(
        "next_url,expected",
        [
            ("https://api.polygon.io/v2/reference/news?cursor=abc123", "abc123"),
            (
                "https://api.polygon.io/v2/reference/news?other=val&cursor=xyz",
                "xyz",
            ),
            ("https://api.polygon.io/v2/reference/news?nocursor", None),
            ("not a url", None),
        ],
    )
    async def test_extract_cursor_from_next_url(self, next_url: str, expected: str | None):
        """Test extract cursor from next url."""
        settings = PolygonSettings(api_key="test_key")
        provider = PolygonMacroNewsProvider(settings, ["AAPL"])  # watchlist

        cursor = provider._extract_cursor(next_url)
        assert cursor == expected

    async def test_extract_cursor_exception_returns_none(self):
        """Test extract cursor exception returns none."""
        settings = PolygonSettings(api_key="test_key")
        provider = PolygonMacroNewsProvider(settings, ["AAPL"])

        result = provider._extract_cursor(None)  # type: ignore[arg-type]
        assert result is None

    async def test_non_dict_publisher_defaults_to_polygon(self):
        """Test non dict publisher defaults to polygon."""
        settings = PolygonSettings(api_key="test_key")
        provider = PolygonMacroNewsProvider(settings, ["AAPL"])

        published_iso = _datetime_to_iso(datetime(2024, 1, 15, 12, 0, tzinfo=UTC))
        article = {
            "id": 1,
            "title": "Headline",
            "article_url": "https://example.com/macro",
            "published_utc": published_iso,
            "tickers": ["AAPL"],
            "publisher": "Not a dict",
            "description": "Desc",
        }

        entries = provider._parse_article(article, buffer_time=None)

        assert len(entries) == 1
        entry = entries[0]
        assert entry.source == "Polygon"
