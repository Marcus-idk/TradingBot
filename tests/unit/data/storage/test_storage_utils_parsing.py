"""
Tests for storage_utils parsing and row conversion helpers.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from data.models import AnalysisType, NewsLabelType, Session, Stance
from data.storage.storage_utils import (
    _iso_to_datetime,
    _parse_rfc3339,
    _row_to_analysis_result,
    _row_to_holdings,
    _row_to_news_item,
    _row_to_news_label,
    _row_to_price_data,
)


class TestIsoParsingHelpers:
    """Tests for ISO/RFC3339 parsing helpers."""

    def test_iso_to_datetime_parses_z_suffix(self):
        dt = _iso_to_datetime("2024-03-10T15:45:00Z")
        assert dt == datetime(2024, 3, 10, 15, 45, tzinfo=UTC)

    def test_iso_to_datetime_preserves_offset(self):
        dt = _iso_to_datetime("2024-03-10T15:45:00+00:00")
        assert dt == datetime(2024, 3, 10, 15, 45, tzinfo=UTC)

    def test_parse_rfc3339_handles_naive_as_utc(self):
        dt = _parse_rfc3339("2024-03-10T15:45:00")
        assert dt == datetime(2024, 3, 10, 15, 45, tzinfo=UTC)

    def test_parse_rfc3339_raises_for_non_string(self):
        with pytest.raises(TypeError):
            _parse_rfc3339(123)

    def test_parse_rfc3339_invalid_format_raises(self):
        with pytest.raises(ValueError):
            _parse_rfc3339("not-a-timestamp")


class TestRowMappers:
    """Tests for row-to-model conversion helpers."""

    def test_row_to_news_item_maps_fields(self):
        row = {
            "symbol": "aapl",
            "url": "https://example.com/news/1",
            "headline": "Headline",
            "published_iso": "2024-03-10T15:45:00Z",
            "source": "Source",
            "content": "Body",
        }

        result = _row_to_news_item(row)

        assert result.symbol == "AAPL"
        assert result.url == "https://example.com/news/1"
        assert result.headline == "Headline"
        assert result.published == datetime(2024, 3, 10, 15, 45, tzinfo=UTC)
        assert result.source == "Source"
        assert result.content == "Body"

    def test_row_to_news_label_handles_optional_created_at(self):
        row = {
            "symbol": "aapl",
            "url": "https://example.com/news/1",
            "label": "Company",
            "created_at_iso": None,
        }

        result = _row_to_news_label(row)

        assert result.symbol == "AAPL"
        assert result.label == NewsLabelType.COMPANY
        assert result.created_at is None

    def test_row_to_news_label_parses_created_at(self):
        row = {
            "symbol": "aapl",
            "url": "https://example.com/news/1",
            "label": "Company",
            "created_at_iso": "2024-03-10T16:00:00Z",
        }

        result = _row_to_news_label(row)

        assert result.created_at == datetime(2024, 3, 10, 16, 0, tzinfo=UTC)

    def test_row_to_price_data_maps_decimal_and_session(self):
        row = {
            "symbol": "msft",
            "timestamp_iso": "2024-03-10T15:45:00Z",
            "price": "310.55",
            "volume": 1500,
            "session": "REG",
        }

        result = _row_to_price_data(row)

        assert result.symbol == "MSFT"
        assert result.price == Decimal("310.55")
        assert result.volume == 1500
        assert result.session == Session.REG

    def test_row_to_analysis_result_builds_model(self):
        row = {
            "symbol": "tsla",
            "analysis_type": "news_analysis",
            "model_name": "gpt",
            "stance": "BULL",
            "confidence_score": 0.85,
            "last_updated_iso": "2024-03-10T15:45:00Z",
            "result_json": '{"text": "ok"}',
            "created_at_iso": "2024-03-10T15:50:00Z",
        }

        result = _row_to_analysis_result(row)

        assert result.symbol == "TSLA"
        assert result.analysis_type == AnalysisType.NEWS_ANALYSIS
        assert result.stance == Stance.BULL
        assert result.confidence_score == pytest.approx(0.85)
        assert result.last_updated == datetime(2024, 3, 10, 15, 45, tzinfo=UTC)
        assert result.created_at == datetime(2024, 3, 10, 15, 50, tzinfo=UTC)

    def test_row_to_holdings_parses_decimals(self):
        row = {
            "symbol": "aapl",
            "quantity": "10.5",
            "break_even_price": "120.00",
            "total_cost": "1260.00",
            "notes": "Long position",
            "created_at_iso": "2024-03-10T15:45:00Z",
            "updated_at_iso": "2024-03-11T09:30:00Z",
        }

        result = _row_to_holdings(row)

        assert result.symbol == "AAPL"
        assert result.quantity == Decimal("10.5")
        assert result.break_even_price == Decimal("120.00")
        assert result.total_cost == Decimal("1260.00")
        assert result.notes == "Long position"
        assert result.created_at == datetime(2024, 3, 10, 15, 45, tzinfo=UTC)
        assert result.updated_at == datetime(2024, 3, 11, 9, 30, tzinfo=UTC)
