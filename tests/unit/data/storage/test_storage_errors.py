"""
Tests error handling and edge cases in storage operations.
"""

import sqlite3
from datetime import UTC, datetime

import pytest

from data.models import NewsEntry, NewsItem, NewsType
from data.storage import (
    get_all_holdings,
    get_analysis_results,
    get_news_before,
    get_news_since,
    get_price_data_since,
    get_prices_before,
    store_news_items,
)


class TestErrorHandling:
    """Test comprehensive error handling and edge cases"""

    def test_database_operations_with_nonexistent_db(self):
        """Test operations fail gracefully with non-existent database"""
        nonexistent_path = "/nonexistent/path/database.db"

        # Create test data to force actual database connection attempt
        test_entry = NewsEntry(
            article=NewsItem(
                url="https://example.com/test",
                headline="Test News",
                source="Test",
                published=datetime.now(UTC),
                news_type=NewsType.COMPANY_SPECIFIC,
            ),
            symbol="AAPL",
            is_important=None,
        )

        # Operations should raise appropriate database errors
        with pytest.raises((sqlite3.OperationalError, FileNotFoundError)):
            store_news_items(nonexistent_path, [test_entry])  # Forces DB connection

        with pytest.raises((sqlite3.OperationalError, FileNotFoundError)):
            get_news_since(nonexistent_path, datetime.now(UTC))

    def test_query_operations_with_empty_database(self, temp_db):
        """Test query operations return empty results with empty database"""
        # All query operations should return empty lists
        now = datetime.now(UTC)
        assert get_news_since(temp_db, now) == []
        assert get_price_data_since(temp_db, now) == []
        assert get_news_before(temp_db, now) == []
        assert get_prices_before(temp_db, now) == []
        assert get_all_holdings(temp_db) == []
        assert get_analysis_results(temp_db) == []
        assert get_analysis_results(temp_db, symbol="NONEXISTENT") == []
