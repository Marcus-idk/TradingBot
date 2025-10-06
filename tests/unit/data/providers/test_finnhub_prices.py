"""
Tests for FinnhubPriceProvider quote fetching and parsing.
Split from combined provider tests for clearer 1:1 mapping.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal

from config.providers.finnhub import FinnhubSettings
from data.providers.finnhub import FinnhubPriceProvider
from data.models import Session


class TestFinnhubPriceProvider:
    """Test FinnhubPriceProvider quote fetching and parsing"""

    @pytest.mark.asyncio
    async def test_requires_positive_price(self, monkeypatch):
        """Test that quotes with c <= 0 are skipped"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubPriceProvider(settings, ['AAPL'])

        quote_fixture = {'c': 0, 't': 1705320000, 'h': 125, 'l': 122}

        async def mock_get(path, params=None):
            if path == '/quote':
                return quote_fixture
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_decimal_conversion(self, monkeypatch):
        """Test that price is converted to Decimal with string precision"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubPriceProvider(settings, ['AAPL'])

        quote_fixture = {'c': 123.45, 't': 1705320000}

        async def mock_get(path, params=None):
            if path == '/quote':
                return quote_fixture
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert len(results) == 1
        assert results[0].price == Decimal('123.45')
        assert isinstance(results[0].price, Decimal)

    @pytest.mark.asyncio
    async def test_fallback_timestamp_missing_t(self, monkeypatch):
        """Test fallback to now() when 't' field is missing"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubPriceProvider(settings, ['AAPL'])

        # Mock datetime.now
        fixed_now = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        class MockDatetime:
            @staticmethod
            def now(tz):
                return fixed_now

            @staticmethod
            def fromtimestamp(ts, tz):
                return datetime.fromtimestamp(ts, tz)

        monkeypatch.setattr('data.providers.finnhub.finnhub_prices.datetime', MockDatetime)

        quote_fixture = {'c': 150.0}  # No 't' field

        async def mock_get(path, params=None):
            if path == '/quote':
                return quote_fixture
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert len(results) == 1
        assert results[0].timestamp == fixed_now

    @pytest.mark.asyncio
    async def test_fallback_timestamp_invalid_t(self, monkeypatch):
        """Test fallback to now() when 't' field is invalid"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubPriceProvider(settings, ['AAPL'])

        fixed_now = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)
        class MockDatetime:
            @staticmethod
            def now(tz):
                return fixed_now

            @staticmethod
            def fromtimestamp(ts, tz):
                if ts == -999999999999:  # Invalid timestamp
                    raise OSError('Invalid timestamp')
                return datetime.fromtimestamp(ts, tz)

        monkeypatch.setattr('data.providers.finnhub.finnhub_prices.datetime', MockDatetime)

        quote_fixture = {'c': 150.0, 't': -999999999999}

        async def mock_get(path, params=None):
            if path == '/quote':
                return quote_fixture
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert len(results) == 1
        assert results[0].timestamp == fixed_now

    @pytest.mark.asyncio
    async def test_defaults_session_and_volume(self, monkeypatch):
        """Test session classification and default volume"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubPriceProvider(settings, ['AAPL'])
        # 15:00:00 UTC = 10:00:00 ET (REG session)
        reg_dt_utc = datetime(2024, 1, 17, 15, 0, tzinfo=timezone.utc)
        quote_fixture = {'c': 150.0, 't': int(reg_dt_utc.timestamp())}

        async def mock_get(path, params=None):
            if path == '/quote':
                return quote_fixture
            return None

        provider.client.get = mock_get

        results = await provider.fetch_incremental()

        assert len(results) == 1
        assert results[0].session == Session.REG
        assert results[0].volume is None

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, monkeypatch):
        """Test validate_connection returns True on success"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubPriceProvider(settings, ['AAPL'])

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
        provider = FinnhubPriceProvider(settings, ['AAPL'])

        async def mock_get(path, params=None):
            raise Exception('Connection failed')

        provider.client.get = mock_get

        result = await provider.validate_connection()
        assert result is False

    @pytest.mark.asyncio
    async def test_price_per_symbol_isolation(self, monkeypatch):
        """Test that error in one symbol doesn't prevent others from succeeding"""
        settings = FinnhubSettings(api_key='test_key')
        provider = FinnhubPriceProvider(settings, ['AAPL', 'FAIL', 'TSLA'])

        async def mock_get(path, params=None):
            sym = params.get('symbol') if params else None
            if sym == 'FAIL':
                raise Exception('quote error')
            return {'c': 123.45, 't': 1705320000}

        provider.client.get = mock_get
        results = await provider.fetch_incremental()
        got = sorted((r.symbol for r in results))
        assert got == ['AAPL', 'TSLA']  # failed symbol skipped but others succeed

