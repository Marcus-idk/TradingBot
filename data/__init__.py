# Data module for trading bot - clean exports
# Components will be added as they're implemented

# Core abstractions (available immediately)
from data.base import DataSource, DataSourceError, NewsDataSource, PriceDataSource

# Data models
from data.models import (
    AnalysisResult,
    AnalysisType,
    Holdings,
    NewsItem,
    NewsLabel,
    NewsLabelType,
    PriceData,
    Session,
    Stance,
)

# Storage operations
from data.storage import (
    commit_llm_batch,
    connect,
    finalize_database,
    get_all_holdings,
    get_analysis_results,
    get_last_news_time,
    get_news_before,
    get_news_labels,
    get_news_since,
    get_price_data_since,
    get_prices_before,
    init_database,
    set_last_news_time,
    store_news_items,
    store_news_labels,
    store_price_data,
    upsert_analysis_result,
    upsert_holdings,
)

__all__ = [
    "DataSource",
    "NewsDataSource",
    "PriceDataSource",
    "DataSourceError",
    "NewsItem",
    "PriceData",
    "AnalysisResult",
    "Holdings",
    "NewsLabel",
    "Session",
    "Stance",
    "AnalysisType",
    "NewsLabelType",
    "init_database",
    "finalize_database",
    "store_news_items",
    "store_news_labels",
    "store_price_data",
    "get_news_since",
    "get_news_labels",
    "get_price_data_since",
    "upsert_analysis_result",
    "upsert_holdings",
    "get_all_holdings",
    "get_analysis_results",
    "connect",
    "get_last_news_time",
    "set_last_news_time",
    "get_news_before",
    "get_prices_before",
    "commit_llm_batch",
]
