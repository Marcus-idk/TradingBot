"""Reddit provider configuration settings."""

import os
from collections.abc import Mapping
from dataclasses import dataclass

from config.retry import DEFAULT_DATA_RETRY, DataRetryConfig


@dataclass(frozen=True)
class RedditSettings:
    """Configuration for Reddit OAuth and polling behavior.

    API precision: Reddit search uses coarse time_filter ("hour", "day", "week")
    and a result limit. We filter by exact timestamp in code after fetching.
    Overlap re-scans a buffer window; DB dedupes on insert.
    """

    client_id: str
    client_secret: str
    user_agent: str
    retry_config: DataRetryConfig = DEFAULT_DATA_RETRY
    search_limit: int = 50
    comments_limit: int = 20
    social_news_overlap_minutes: int = 2
    social_news_first_run_days: int = 7
    bootstrap_time_filter: str = "week"
    incremental_time_filter: str = "hour"

    @staticmethod
    def from_env(env: Mapping[str, str] | None = None) -> "RedditSettings":
        """Load Reddit settings from environment variables."""
        if env is None:
            env = os.environ

        client_id = (env.get("REDDIT_CLIENT_ID") or "").strip()
        client_secret = (env.get("REDDIT_CLIENT_SECRET") or "").strip()
        user_agent = (env.get("REDDIT_USER_AGENT") or "").strip()

        if not client_id:
            raise ValueError("REDDIT_CLIENT_ID environment variable not found or empty")
        if not client_secret:
            raise ValueError("REDDIT_CLIENT_SECRET environment variable not found or empty")
        if not user_agent:
            raise ValueError("REDDIT_USER_AGENT environment variable not found or empty")

        return RedditSettings(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
