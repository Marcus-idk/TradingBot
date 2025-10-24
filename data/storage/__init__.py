"""Public facade for trading bot data storage helpers."""

# Core database functions
# Batch operations and watermarks
from data.storage.storage_batch import (
    commit_llm_batch,
    get_last_macro_min_id,
    get_last_news_time,
    get_last_seen,
    get_news_before,
    get_prices_before,
    set_last_macro_min_id,
    set_last_news_time,
    set_last_seen,
)
from data.storage.storage_core import (
    connect,
    finalize_database,
    init_database,
)

# CRUD operations
from data.storage.storage_crud import (
    get_all_holdings,
    get_analysis_results,
    get_news_labels,
    get_news_since,
    get_price_data_since,
    store_news_items,
    store_news_labels,
    store_price_data,
    upsert_analysis_result,
    upsert_holdings,
)

# All public functions (for backward compatibility)
__all__ = [
    # Core database
    "connect",
    "init_database",
    "finalize_database",
    # CRUD operations
    "store_news_items",
    "store_news_labels",
    "store_price_data",
    "get_news_since",
    "get_news_labels",
    "get_price_data_since",
    "get_all_holdings",
    "get_analysis_results",
    "upsert_analysis_result",
    "upsert_holdings",
    # Batch and watermarks
    "get_last_seen",
    "set_last_seen",
    "get_last_news_time",
    "set_last_news_time",
    "get_last_macro_min_id",
    "set_last_macro_min_id",
    "get_news_before",
    "get_prices_before",
    "commit_llm_batch",
]
