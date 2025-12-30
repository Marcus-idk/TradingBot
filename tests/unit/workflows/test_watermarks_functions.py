"""Unit tests for pure helper functions in workflows.watermarks."""

from config.providers.finnhub import FinnhubSettings
from config.providers.reddit import RedditSettings
from data.providers.finnhub import FinnhubMacroNewsProvider, FinnhubNewsProvider
from data.providers.reddit import RedditSocialProvider
from workflows.watermarks import is_macro_stream


def test_is_macro_stream_matches_rule():
    """is_macro_stream is True only for providers configured as macro stream."""
    finnhub_macro = FinnhubMacroNewsProvider(FinnhubSettings(api_key="test"), ["AAPL"])
    finnhub_company = FinnhubNewsProvider(FinnhubSettings(api_key="test"), ["AAPL"])
    reddit_social = RedditSocialProvider(
        RedditSettings(client_id="id", client_secret="secret", user_agent="agent"),
        ["AAPL"],
    )

    assert is_macro_stream(finnhub_macro) is True
    assert is_macro_stream(finnhub_company) is False
    assert is_macro_stream(reddit_social) is False
