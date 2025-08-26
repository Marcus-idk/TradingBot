"""
Phase 4: Base Class Validation Tests

Tests for abstract base classes and their contracts:
- DataSource abstract base class 
- NewsDataSource and PriceDataSource subclasses
- Exception hierarchy (DataSourceError, RateLimitError)
- Abstract method enforcement
"""

import pytest
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from data.base import (
    DataSource, 
    NewsDataSource, 
    PriceDataSource,
    DataSourceError,
    RateLimitError
)
from data.models import NewsItem, PriceData


class TestDataSourceInitialization:
    """Test DataSource.__init__ validation rules"""
    
    def test_datasource_source_name_none(self):
        """source_name=None raises ValueError"""
        with pytest.raises(ValueError, match="source_name cannot be None"):
            class ConcreteSource(DataSource):
                async def validate_connection(self): return True
            ConcreteSource(None)
    
    def test_datasource_source_name_not_string(self):
        """Non-string source_name raises TypeError"""
        with pytest.raises(TypeError, match="source_name must be a string"):
            class ConcreteSource(DataSource):
                async def validate_connection(self): return True
            ConcreteSource(123)
        
        with pytest.raises(TypeError, match="source_name must be a string"):
            class ConcreteSource(DataSource):
                async def validate_connection(self): return True
            ConcreteSource(['list'])
    
    def test_datasource_source_name_empty(self):
        """Empty or whitespace-only source_name raises ValueError"""
        with pytest.raises(ValueError, match="source_name cannot be empty"):
            class ConcreteSource(DataSource):
                async def validate_connection(self): return True
            ConcreteSource("")
        
        with pytest.raises(ValueError, match="source_name cannot be empty"):
            class ConcreteSource(DataSource):
                async def validate_connection(self): return True
            ConcreteSource("   ")
    
    def test_datasource_source_name_too_long(self):
        """source_name > 100 chars raises ValueError"""
        long_name = "A" * 101
        with pytest.raises(ValueError, match="source_name too long.*101.*max 100"):
            class ConcreteSource(DataSource):
                async def validate_connection(self): return True
            ConcreteSource(long_name)
    
    def test_datasource_source_name_valid(self):
        """Valid source_name initializes correctly"""
        class ConcreteSource(DataSource):
            async def validate_connection(self): return True
        
        source = ConcreteSource("Finnhub")
        assert source.source_name == "Finnhub"
        assert source.last_fetch_time is None
        
        # Max length exactly 100 chars
        source2 = ConcreteSource("A" * 100)
        assert source2.source_name == "A" * 100
    
    def test_datasource_source_name_trimmed(self):
        """source_name whitespace is stripped"""
        class ConcreteSource(DataSource):
            async def validate_connection(self): return True
        
        source = ConcreteSource("  Reuters  ")
        assert source.source_name == "Reuters"


class TestUpdateLastFetchTime:
    """Test DataSource.update_last_fetch_time() method"""
    
    def setup_method(self):
        """Create a concrete DataSource for testing"""
        class ConcreteSource(DataSource):
            async def validate_connection(self): return True
        self.source = ConcreteSource("TestSource")
    
    def test_update_last_fetch_time_naive_normalized_to_utc(self):
        """Naive datetime should be normalized to UTC"""
        naive_time = datetime(2024, 1, 1, 12, 0, 0)  # Use fixed time for predictable test
        self.source.update_last_fetch_time(naive_time)
        
        # Should be stored as UTC
        expected_utc = naive_time.replace(tzinfo=timezone.utc)
        assert self.source.last_fetch_time == expected_utc
        assert self.source.get_last_fetch_time() == expected_utc
    
    def test_update_last_fetch_time_aware_converted_to_utc(self):
        """Timezone-aware datetimes are converted to UTC"""
        utc_time = datetime.now(timezone.utc) - timedelta(hours=1)
        self.source.update_last_fetch_time(utc_time)
        assert self.source.last_fetch_time == utc_time
        assert self.source.get_last_fetch_time() == utc_time
        
        # Test with non-UTC timezone (if zoneinfo available)
        try:
            import zoneinfo
            eastern = zoneinfo.ZoneInfo("America/New_York")  # Use canonical name
            eastern_time = datetime.now(eastern) - timedelta(hours=1)
            self.source.update_last_fetch_time(eastern_time)
            
            # Should be converted to UTC, not stored as Eastern
            expected_utc = eastern_time.astimezone(timezone.utc)
            assert self.source.last_fetch_time == expected_utc
            assert self.source.get_last_fetch_time() == expected_utc
        except (ImportError, zoneinfo.ZoneInfoNotFoundError):
            # Skip zoneinfo test if not available or timezone not found
            pass
    
    def test_update_last_fetch_time_future(self):
        """Future timestamp raises ValueError"""
        future = datetime.now(timezone.utc) + timedelta(hours=1)
        with pytest.raises(ValueError, match="timestamp cannot be in the future"):
            self.source.update_last_fetch_time(future)
    
    def test_update_last_fetch_time_none(self):
        """None timestamp raises ValueError"""
        with pytest.raises(ValueError, match="timestamp cannot be None"):
            self.source.update_last_fetch_time(None)
    
    def test_update_last_fetch_time_not_datetime(self):
        """Non-datetime types raise TypeError"""
        with pytest.raises(TypeError, match="timestamp must be a datetime object"):
            self.source.update_last_fetch_time("2024-01-01")
        
        with pytest.raises(TypeError, match="timestamp must be a datetime object"):
            self.source.update_last_fetch_time(123456789)


class TestAbstractMethodEnforcement:
    """Test that abstract classes cannot be instantiated without implementing required methods"""
    
    def test_datasource_cannot_instantiate(self):
        """DataSource is abstract and cannot be instantiated directly"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class DataSource"):
            DataSource("Test")
    
    def test_newsdata_source_requires_fetch_incremental(self):
        """NewsDataSource requires fetch_incremental implementation"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class.*fetch_incremental"):
            class IncompleteNews(NewsDataSource):
                async def validate_connection(self): return True
            IncompleteNews("Test")
    
    def test_pricedata_source_requires_fetch_incremental(self):
        """PriceDataSource requires fetch_incremental implementation"""
        with pytest.raises(TypeError, match="Can't instantiate abstract class.*fetch_incremental"):
            class IncompletePrice(PriceDataSource):
                async def validate_connection(self): return True
            IncompletePrice("Test")
    
    def test_concrete_implementation_works(self):
        """Properly implemented concrete classes can be instantiated"""
        
        # Complete NewsDataSource implementation
        class ConcreteNews(NewsDataSource):
            async def validate_connection(self) -> bool:
                return True
            
            async def fetch_incremental(self, since: Optional[datetime] = None) -> List[NewsItem]:
                return []
        
        news_source = ConcreteNews("NewsTest")
        assert news_source.source_name == "NewsTest"
        
        # Complete PriceDataSource implementation  
        class ConcretePrice(PriceDataSource):
            async def validate_connection(self) -> bool:
                return True
            
            async def fetch_incremental(self, since: Optional[datetime] = None) -> List[PriceData]:
                return []
        
        price_source = ConcretePrice("PriceTest")
        assert price_source.source_name == "PriceTest"


class TestExceptionHierarchy:
    """Test exception class inheritance structure"""
    
    def test_exception_inheritance(self):
        """Verify exception class hierarchy"""
        # DataSourceError inherits from Exception
        assert issubclass(DataSourceError, Exception)
        
        # RateLimitError inherits from DataSourceError
        assert issubclass(RateLimitError, DataSourceError)
        assert issubclass(RateLimitError, Exception)
        
        # Can raise and catch appropriately
        error = DataSourceError("Test error")
        assert isinstance(error, DataSourceError)
        assert isinstance(error, Exception)
        
        rate_error = RateLimitError("Rate limit exceeded")
        assert isinstance(rate_error, RateLimitError)
        assert isinstance(rate_error, DataSourceError)
        assert isinstance(rate_error, Exception)
    
    def test_ratelimit_is_datasource_error(self):
        """RateLimitError can be caught as DataSourceError"""
        try:
            raise RateLimitError("API limit reached")
        except DataSourceError as e:
            # Should catch RateLimitError as DataSourceError
            assert isinstance(e, RateLimitError)
            assert str(e) == "API limit reached"
        except Exception:
            pytest.fail("RateLimitError should be caught as DataSourceError")


class TestDataSourceMethods:
    """Test other DataSource methods"""
    
    def test_get_last_fetch_time_initially_none(self):
        """get_last_fetch_time returns None before any updates"""
        class ConcreteSource(DataSource):
            async def validate_connection(self): return True
        
        source = ConcreteSource("Test")
        assert source.get_last_fetch_time() is None
    
    def test_get_last_fetch_time_after_update(self):
        """get_last_fetch_time returns the last set timestamp"""
        class ConcreteSource(DataSource):
            async def validate_connection(self): return True
        
        source = ConcreteSource("Test")
        
        # Set first timestamp
        time1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        source.update_last_fetch_time(time1)
        assert source.get_last_fetch_time() == time1
        
        # Update to newer timestamp
        time2 = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)
        source.update_last_fetch_time(time2)
        assert source.get_last_fetch_time() == time2