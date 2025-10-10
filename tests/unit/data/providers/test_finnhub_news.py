"""
Tests for FinnhubNewsProvider news fetching and parsing.
Split from combined provider tests for clearer 1:1 mapping.
"""

import pytest
from datetime import datetime, timezone
from datetime import timedelta as real_timedelta

from config.providers.finnhub import FinnhubSettings
from data.providers.finnhub import FinnhubNewsProvider
from data.base import DataSourceError


class TestFinnhubNewsProvider:
    """Test FinnhubNewsProvider news fetching and parsing"""

    @pytest.mark.asyncio
    async def test_date_window_with_since(self, monkeypatch):
        """Test date window calculation when since is provided"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['AAPL'])

        # Mock datetime to have consistent "now"
        class MockDatetime:
            @staticmethod
            def now(tz):
                return datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)

            @staticmethod
            def fromtimestamp(ts, tz):
                return datetime.fromtimestamp(ts, tz)

        # Also need to provide timedelta and timezone from the mock
        MockDatetime.timedelta = real_timedelta
        MockDatetime.timezone = timezone

        monkeypatch.setattr('data.providers.finnhub.finnhub_news.datetime', MockDatetime)
        monkeypatch.setattr('data.providers.finnhub.finnhub_news.timedelta', real_timedelta)

        captured_params = {}
        async def mock_get(path, params=None):
            if path == '/company-news':
                if params:
                    captured_params.update(params)
                return []
            return None

        provider.client.get = mock_get

        since = datetime(2024, 1, 13, 5, 0, tzinfo=timezone.utc)
        await provider.fetch_incremental(since=since)

        # Should use min(since.date, yesterday) = 2024-01-13
        assert captured_params['from'] == '2024-01-13'
        assert captured_params['to'] == '2024-01-15'

    @pytest.mark.asyncio
    async def test_date_window_without_since(self, monkeypatch):
        """Test date window calculation when since is None"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['AAPL'])

        class MockDatetime:
            @staticmethod
            def now(tz):
                return datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)

            @staticmethod
            def fromtimestamp(ts, tz):
                return datetime.fromtimestamp(ts, tz)

        MockDatetime.timedelta = real_timedelta
        MockDatetime.timezone = timezone

        monkeypatch.setattr('data.providers.finnhub.finnhub_news.datetime', MockDatetime)
        monkeypatch.setattr('data.providers.finnhub.finnhub_news.timedelta', real_timedelta)

        captured_params = {}
        async def mock_get(path, params=None):
            if path == '/company-news':
                if params:
                    captured_params.update(params)
                return []
            return None

        provider.client.get = mock_get

        await provider.fetch_incremental(since=None)

        # Should use 2 days ago
        assert captured_params['from'] == '2024-01-13'
        assert captured_params['to'] == '2024-01-15'

    @pytest.mark.asyncio
    async def test_filters_old_articles(self, monkeypatch):
        """Test that articles are filtered with 2-minute buffer (published <= buffer_time)"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['AAPL'])

        # Buffer: 1000 - 120 = 880 seconds
        news_fixture = [
            {'headline': 'Very Old', 'url': 'http://veryold.com', 'datetime': 500, 'source': 'Reuters'},     # Before buffer
            {'headline': 'Old News', 'url': 'http://old.com', 'datetime': 880, 'source': 'Reuters'},         # Exactly at buffer (filtered)
            {'headline': 'Buffer Zone', 'url': 'http://buffer.com', 'datetime': 950, 'source': 'Bloomberg'}, # In buffer zone (kept)
            {'headline': 'At Watermark', 'url': 'http://exact.com', 'datetime': 1000, 'source': 'CNN'},      # At watermark (kept)
            {'headline': 'Latest News', 'url': 'http://latest.com', 'datetime': 1100, 'source': 'Yahoo'},    # After watermark (kept)
        ]

        async def mock_get(path, params=None):
            if path == '/company-news':
                return news_fixture
            return None

        provider.client.get = mock_get

        # Set since to datetime(1000)
        since = datetime.fromtimestamp(1000, tz=timezone.utc)
        results = await provider.fetch_incremental(since=since)

        # Should keep articles at 950, 1000, and 1100 (3 articles)
        assert len(results) == 3
        assert results[0].headline == 'Buffer Zone'    # In the 2-minute buffer window
        assert results[1].headline == 'At Watermark'   # Exactly at watermark (now kept!)
        assert results[2].headline == 'Latest News'    # After watermark

    @pytest.mark.asyncio
    async def test_parses_valid_article(self, monkeypatch):
        """Test parsing of valid article with all fields"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['TSLA'])

        news_fixture = [{
            'headline': 'Tesla Stock Rises',
            'url': 'https://example.com/tesla-news',
            'datetime': 1705320000,  # 2024-01-15 12:00:00 UTC
            'source': 'Reuters',
            'summary': 'Tesla stock rose 5% today on strong earnings.'
        }]

        async def mock_get(path, params=None):
            if path == '/company-news':
                return news_fixture
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert len(results) == 1
        item = results[0]
        assert item.symbol == 'TSLA'
        assert item.headline == 'Tesla Stock Rises'
        assert item.url == 'https://example.com/tesla-news'
        assert item.source == 'Reuters'
        assert item.content == 'Tesla stock rose 5% today on strong earnings.'  # summary → content
        assert item.published == datetime.fromtimestamp(1705320000, tz=timezone.utc)

    @pytest.mark.asyncio
    async def test_skips_missing_headline(self, monkeypatch):
        """Test that articles without headline are skipped"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['AAPL'])

        news_fixture = [
            {'url': 'http://no-headline.com', 'datetime': 1705320000},
            {'headline': '', 'url': 'http://empty-headline.com', 'datetime': 1705320000},
            {'headline': 'Valid News', 'url': 'http://valid.com', 'datetime': 1705320000}
        ]

        async def mock_get(path, params=None):
            if path == '/company-news':
                return news_fixture
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert len(results) == 1
        assert results[0].headline == 'Valid News'

    @pytest.mark.asyncio
    async def test_skips_invalid_epoch(self, monkeypatch):
        """Test that articles with invalid epoch timestamps are skipped"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['AAPL'])

        news_fixture = [
            {'headline': 'Zero Epoch', 'url': 'http://zero.com', 'datetime': 0},
            {'headline': 'Negative Epoch', 'url': 'http://negative.com', 'datetime': -100},
            {'headline': 'Valid News', 'url': 'http://valid.com', 'datetime': 1705320000}
        ]

        async def mock_get(path, params=None):
            if path == '/company-news':
                return news_fixture
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert len(results) == 1
        assert results[0].headline == 'Valid News'

    @pytest.mark.asyncio
    async def test_per_symbol_isolation(self, monkeypatch):
        """Test that error in one symbol doesn't affect others"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['FAIL', 'AAPL', 'TSLA'])

        call_count = 0
        async def mock_get(path, params=None):
            nonlocal call_count
            call_count += 1

            if path == '/company-news' and params:
                symbol = params.get('symbol')
                if symbol == 'FAIL':
                    raise Exception('API error for FAIL symbol')
                elif symbol == 'AAPL':
                    return [{'headline': 'Apple News', 'url': 'http://apple.com', 'datetime': 1705320000}]
                elif symbol == 'TSLA':
                    return [{'headline': 'Tesla News', 'url': 'http://tesla.com', 'datetime': 1705320000}]
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert call_count == 3  # All symbols attempted
        assert len(results) == 2  # Only successful ones returned
        headlines = [r.headline for r in results]
        assert 'Apple News' in headlines
        assert 'Tesla News' in headlines

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, monkeypatch):
        """Test validate_connection returns True on success"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['AAPL'])

        async def mock_get(path, params=None):
            if path == '/quote':
                return {'c': 150.0, 't': 1705320000}
            return None

        provider.client.get = mock_get

        result = await provider.validate_connection()
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, monkeypatch):
        """Test validate_connection returns False on exception"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['AAPL'])

        async def mock_get(path, params=None):
            raise Exception('Connection failed')

        provider.client.get = mock_get

        result = await provider.validate_connection()
        assert result is False

    @pytest.mark.asyncio
    async def test_company_news_raises_on_non_list_response(self, monkeypatch):
        """Test fail-fast when API returns non-list response (structural error)"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubNewsProvider(settings, ['AAPL'])

        async def mock_get(path, params=None):
            return {'unexpected': 'object'}  # not a list

        provider.client.get = mock_get

        with pytest.raises(DataSourceError, match="returned dict instead of list"):
            await provider.fetch_incremental()

