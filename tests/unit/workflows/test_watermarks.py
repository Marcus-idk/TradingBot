"""Unit tests for the WatermarkEngine (planning + commit behavior)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from config.providers.finnhub import FinnhubSettings
from config.providers.reddit import RedditSettings
from data.base import NewsDataSource
from data.providers.finnhub import FinnhubMacroNewsProvider, FinnhubNewsProvider
from data.providers.reddit import RedditSocialProvider
from data.storage import (
    get_last_seen_id,
    get_last_seen_timestamp,
    set_last_seen_id,
    set_last_seen_timestamp,
)
from data.storage.state_enums import Provider, Scope, Stream
from tests.factories import make_news_entry, make_social_discussion
from workflows import watermarks as watermarks_module
from workflows.watermarks import WatermarkEngine


def _make_engine(temp_db: str) -> WatermarkEngine:
    return WatermarkEngine(temp_db)


class TestWatermarkEngine:
    """Tests for WatermarkEngine planning and watermark commits."""

    def test_build_plan_finnhub_macro_uses_id_cursor(self, temp_db):
        """Build plan uses the stored macro ID watermark as min_id."""
        provider = FinnhubMacroNewsProvider(FinnhubSettings(api_key="test"), ["AAPL"])
        set_last_seen_id(temp_db, Provider.FINNHUB, Stream.MACRO, Scope.GLOBAL, 200)

        plan = _make_engine(temp_db).build_plan(provider)

        assert plan.min_id == 200
        assert plan.since is None
        assert plan.symbol_since_map is None

    def test_build_plan_finnhub_company_maps_each_symbol(self, temp_db, monkeypatch):
        """Build plan returns a per-symbol timestamp map for Finnhub company news."""
        provider = FinnhubNewsProvider(FinnhubSettings(api_key="test"), ["AAPL", "TSLA"])
        fixed_now = datetime(2024, 1, 20, 12, 0, tzinfo=UTC)
        monkeypatch.setattr(watermarks_module, "_utc_now", lambda: fixed_now)

        existing = datetime(2024, 1, 18, 9, 30, tzinfo=UTC)
        set_last_seen_timestamp(
            temp_db,
            Provider.FINNHUB,
            Stream.COMPANY,
            Scope.SYMBOL,
            existing,
            symbol="AAPL",
        )

        plan = _make_engine(temp_db).build_plan(provider)

        assert plan.since is None
        assert plan.min_id is None
        expected_tsla = fixed_now - timedelta(days=provider.settings.company_news_first_run_days)
        assert plan.symbol_since_map == {
            "AAPL": existing,
            "TSLA": expected_tsla,
        }

    def test_build_plan_reddit_social_uses_per_symbol_map(self, temp_db, monkeypatch):
        """Build plan omits new symbols for Reddit so provider can bootstrap."""
        settings = RedditSettings(client_id="id", client_secret="secret", user_agent="agent")
        provider = RedditSocialProvider(settings, ["AAPL", "TSLA"])
        fixed_now = datetime(2024, 4, 1, 12, 0, tzinfo=UTC)
        monkeypatch.setattr(watermarks_module, "_utc_now", lambda: fixed_now)

        existing = datetime(2024, 3, 31, 10, 0, tzinfo=UTC)
        set_last_seen_timestamp(
            temp_db,
            Provider.REDDIT,
            Stream.SOCIAL,
            Scope.SYMBOL,
            existing,
            symbol="AAPL",
        )

        plan = _make_engine(temp_db).build_plan(provider)

        assert plan.since is None
        assert plan.min_id is None
        assert plan.symbol_since_map == {
            "AAPL": existing,
        }

    def test_commit_updates_symbol_scope_clamps_future(self, temp_db, monkeypatch):
        """Commit updates clamps future timestamps for per-symbol streams."""
        provider = FinnhubNewsProvider(FinnhubSettings(api_key="test"), ["AAPL", "TSLA"])
        fixed_now = datetime(2024, 2, 1, 12, 0, tzinfo=UTC)
        monkeypatch.setattr(watermarks_module, "_utc_now", lambda: fixed_now)

        entries = [
            make_news_entry(
                symbol="AAPL",
                published=fixed_now + timedelta(minutes=5),
            ),
            make_news_entry(
                symbol="TSLA",
                published=fixed_now - timedelta(minutes=10),
            ),
        ]

        _make_engine(temp_db).commit_updates(provider, entries)

        aapl_ts = get_last_seen_timestamp(
            temp_db,
            Provider.FINNHUB,
            Stream.COMPANY,
            Scope.SYMBOL,
            symbol="AAPL",
        )
        tsla_ts = get_last_seen_timestamp(
            temp_db,
            Provider.FINNHUB,
            Stream.COMPANY,
            Scope.SYMBOL,
            symbol="TSLA",
        )

        assert aapl_ts == fixed_now + timedelta(seconds=60)
        assert tsla_ts == fixed_now - timedelta(minutes=10)

    def test_commit_updates_id_scope_writes_last_fetched_max(self, temp_db):
        """Commit updates persists last_fetched_max_id for ID-based streams."""
        provider = FinnhubMacroNewsProvider(FinnhubSettings(api_key="test"), ["AAPL"])
        provider.last_fetched_max_id = 250

        _make_engine(temp_db).commit_updates(provider, [])

        assert (
            get_last_seen_id(
                temp_db,
                Provider.FINNHUB,
                Stream.MACRO,
                Scope.GLOBAL,
            )
            == 250
        )

    def test_commit_updates_id_scope_noop_without_last_fetched(self, temp_db):
        """Commit updates does nothing when last_fetched_max_id is missing."""
        provider = FinnhubMacroNewsProvider(FinnhubSettings(api_key="test"), ["AAPL"])
        provider.last_fetched_max_id = None

        _make_engine(temp_db).commit_updates(provider, [])

        assert (
            get_last_seen_id(
                temp_db,
                Provider.FINNHUB,
                Stream.MACRO,
                Scope.GLOBAL,
            )
            is None
        )

    def test_commit_updates_social_scope_commits_per_symbol_and_clamps_future(
        self, temp_db, monkeypatch, caplog
    ):
        """Commit updates tracks Reddit social timestamps per symbol and clamps future."""
        settings = RedditSettings(client_id="id", client_secret="secret", user_agent="agent")
        provider = RedditSocialProvider(settings, ["AAPL", "TSLA"])
        fixed_now = datetime(2024, 4, 2, 12, 0, tzinfo=UTC)
        monkeypatch.setattr(watermarks_module, "_utc_now", lambda: fixed_now)
        caplog.set_level("WARNING")

        future_entry = make_social_discussion(
            symbol="AAPL",
            published=fixed_now + timedelta(minutes=5),
        )
        past_entry = make_social_discussion(
            symbol="TSLA",
            source_id="t3_tsla",
            published=fixed_now - timedelta(minutes=10),
        )

        engine = _make_engine(temp_db)
        engine.commit_updates(provider, [future_entry, past_entry])

        aapl_ts = get_last_seen_timestamp(
            temp_db,
            Provider.REDDIT,
            Stream.SOCIAL,
            Scope.SYMBOL,
            symbol="AAPL",
        )
        tsla_ts = get_last_seen_timestamp(
            temp_db,
            Provider.REDDIT,
            Stream.SOCIAL,
            Scope.SYMBOL,
            symbol="TSLA",
        )

        assert aapl_ts == fixed_now + timedelta(seconds=60)
        assert tsla_ts == past_entry.published
        assert "Clamped future watermark provider=REDDIT" in caplog.text

        older_entry = make_social_discussion(
            symbol="AAPL",
            source_id="t3_aapl_old",
            published=fixed_now - timedelta(minutes=30),
        )
        engine.commit_updates(provider, [older_entry])

        assert (
            get_last_seen_timestamp(
                temp_db,
                Provider.REDDIT,
                Stream.SOCIAL,
                Scope.SYMBOL,
                symbol="AAPL",
            )
            == aapl_ts
        )

    def test_get_settings_missing_attribute_raises(self, temp_db):
        """_get_settings raises when provider has no settings attribute."""
        engine = _make_engine(temp_db)

        class DummyProvider(NewsDataSource):
            async def validate_connection(self) -> bool:  # pragma: no cover - trivial
                return True

            async def fetch_incremental(self, **_kwargs):  # pragma: no cover - trivial
                return []

        provider = DummyProvider("Dummy")

        with pytest.raises(RuntimeError, match="missing required 'settings'"):
            engine._get_settings(provider)
