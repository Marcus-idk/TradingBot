"""Shared pytest configuration for integration tests."""

import pytest

from config.providers.finnhub import FinnhubSettings
from config.providers.reddit import RedditSettings

pytestmark = pytest.mark.integration


@pytest.fixture
def finnhub_settings() -> FinnhubSettings:
    """Load FinnhubSettings from the environment or skip when unavailable."""
    try:
        return FinnhubSettings.from_env()
    except ValueError as exc:
        pytest.skip(f"FINNHUB settings unavailable: {exc}")


@pytest.fixture
def reddit_settings() -> RedditSettings:
    """Load RedditSettings from the environment or skip when unavailable."""
    try:
        return RedditSettings.from_env()
    except ValueError as exc:
        pytest.skip(f"REDDIT settings unavailable: {exc}")
