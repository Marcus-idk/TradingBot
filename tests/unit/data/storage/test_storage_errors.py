"""
Tests error handling and edge cases in storage operations.
"""

import pytest
import sqlite3
from datetime import datetime, timezone

from data.storage import store_news_items, get_news_since, get_price_data_since, get_all_holdings, get_analysis_results, get_news_before, get_prices_before

from data.models import NewsItem

class TestErrorHandling:
    """Test comprehensive error handling and edge cases"""
    
    def test_database_operations_with_nonexistent_db(self):
        """Test operations fail gracefully with non-existent database"""
        nonexistent_path = "/nonexistent/path/database.db"
        
        # Create test data to force actual database connection attempt
        test_item = NewsItem(
            symbol="AAPL",
            url="https://example.com/test",
            headline="Test News",
            source="Test",
            published=datetime.now(timezone.utc)
        )
        
        # Operations should raise appropriate database errors
        with pytest.raises((sqlite3.OperationalError, FileNotFoundError)):
            store_news_items(nonexistent_path, [test_item])  # Forces DB connection
            
        with pytest.raises((sqlite3.OperationalError, FileNotFoundError)):
            get_news_since(nonexistent_path, datetime.now(timezone.utc))
    
    def test_query_operations_with_empty_database(self, temp_db):
        """Test query operations return empty results with empty database"""
        # All query operations should return empty lists
        now = datetime.now(timezone.utc)
        assert get_news_since(temp_db, now) == []
        assert get_price_data_since(temp_db, now) == []
        assert get_news_before(temp_db, now) == []
        assert get_prices_before(temp_db, now) == []
        assert get_all_holdings(temp_db) == []
        assert get_analysis_results(temp_db) == []
        assert get_analysis_results(temp_db, symbol="NONEXISTENT") == []