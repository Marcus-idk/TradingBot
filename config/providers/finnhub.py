"""Finnhub provider configuration settings."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from config.retry import DEFAULT_DATA_RETRY, DataRetryConfig


@dataclass(frozen=True)
class FinnhubSettings:
    """Configuration settings for Finnhub API integration.

    API precision: Finnhub /company-news uses date-only from/to params (YYYY-MM-DD).
    We query full days, then filter by timestamp in code. Overlap re-scans a buffer
    window; DB dedupes on insert.
    """

    api_key: str
    base_url: str = "https://finnhub.io/api/v1"
    retry_config: DataRetryConfig = DEFAULT_DATA_RETRY
    company_news_overlap_minutes: int = 2
    company_news_first_run_days: int = 7
    macro_news_overlap_minutes: int = 2
    macro_news_first_run_days: int = 7

    @staticmethod
    def from_env(env: Mapping[str, str] | None = None) -> "FinnhubSettings":
        """Load Finnhub settings from environment variables."""
        if env is None:
            env = os.environ
        key = (env.get("FINNHUB_API_KEY") or "").strip()
        if not key:
            raise ValueError("FINNHUB_API_KEY environment variable not found or empty")
        return FinnhubSettings(api_key=key)
