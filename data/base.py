from abc import ABC, abstractmethod
from datetime import datetime

from data.models import NewsItem, PriceData


class DataSource(ABC):
    """
    Abstract base class for all data providers (Finnhub, Polygon, Reddit, etc.)
    
    Defines the contract that every data source must implement:
    - Incremental fetching (only get new data since last fetch)
    - Connection validation 
    - Consistent error handling
    """
    
    def __init__(self, source_name: str) -> None:
        """
        Initialize data source with identifying name

        Args:
            source_name: Human-readable identifier (e.g., "Finnhub", "Polygon")

        Raises:
            ValueError: If source_name is invalid (None, empty, too long, or contains invalid characters)
            TypeError: If source_name is not a string
        """
        if source_name is None:
            raise ValueError("source_name cannot be None")
        if not isinstance(source_name, str):
            raise TypeError(f"source_name must be a string, got {type(source_name).__name__}")
        if not source_name.strip():
            raise ValueError("source_name cannot be empty or whitespace only")
        if len(source_name) > 100:
            raise ValueError(f"source_name too long: {len(source_name)} characters (max 100)")
        
        self.source_name = source_name.strip()
    
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Test if the data source is reachable and credentials work
        
        Returns:
            True if connection successful, False otherwise
            
        Note:
            Should not raise exceptions - return False for any connection issues
        """
        pass
    
    pass


class DataSourceError(Exception):
    """Base exception for data source related errors"""
    pass


class NewsDataSource(DataSource):
    """Abstract base class for data sources that provide news content"""

    @abstractmethod
    async def fetch_incremental(
        self,
        *,
        since: datetime | None = None,
        min_id: int | None = None
    ) -> list[NewsItem]:
        """
        Fetch new news items using incremental cursors.

        Args:
            since: Fetch items published after this timestamp (used by date-based providers)
            min_id: Fetch items with ID > min_id (used by ID-based providers)

        Returns:
            List of NewsItem objects

        Note:
            Implementations use whichever cursor makes sense for their API.
            Date-based providers (company news) use `since`, ignore `min_id`.
            ID-based providers (macro news) use `min_id`, ignore `since`.
        """
        pass


class PriceDataSource(DataSource):
    """Abstract base class for data sources that provide price/market data"""
    
    @abstractmethod
    async def fetch_incremental(self, since: datetime | None = None) -> list[PriceData]:
        """Fetch new price data since the specified timestamp"""
        pass
