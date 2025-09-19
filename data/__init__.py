# Data module for trading bot - clean exports
# Components will be added as they're implemented

# Core abstractions (available immediately)
from data.base import DataSource, NewsDataSource, PriceDataSource

# Data models
from data.models import NewsItem, PriceData, AnalysisResult, Holdings, NewsLabel, Session, Stance, AnalysisType, NewsLabelType

# Storage operations
from data.storage import (
    init_database, finalize_database, store_news_items, store_news_labels, store_price_data,
    get_news_since, get_news_labels, get_price_data_since, upsert_analysis_result,
    upsert_holdings, get_all_holdings, get_analysis_results, connect,
    get_last_news_time, set_last_news_time,
    get_news_before, get_prices_before,
    commit_llm_batch,
)

__all__ = [
    'DataSource', 'NewsDataSource', 'PriceDataSource',
    'NewsItem', 'PriceData', 'AnalysisResult', 'Holdings', 'NewsLabel',
    'Session', 'Stance', 'AnalysisType', 'NewsLabelType',
    'init_database', 'finalize_database', 'store_news_items', 'store_news_labels', 'store_price_data',
    'get_news_since', 'get_news_labels', 'get_price_data_since', 'upsert_analysis_result',
    'upsert_holdings', 'get_all_holdings', 'get_analysis_results',
    'connect',
    'get_last_news_time', 'set_last_news_time',
    'get_news_before', 'get_prices_before',
    'commit_llm_batch',
]
