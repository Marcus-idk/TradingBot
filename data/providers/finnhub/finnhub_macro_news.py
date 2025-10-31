"""Macro news provider implementation."""

import logging
from datetime import (
    UTC,
    datetime,
    timedelta,
    timezone,  # noqa: F401 - used by tests via monkeypatch
)
from typing import Any

from config.providers.finnhub import FinnhubSettings
from data import DataSourceError, NewsDataSource
from data.models import NewsEntry, NewsItem, NewsType
from data.providers.finnhub.finnhub_client import FinnhubClient
from data.storage.storage_utils import _datetime_to_iso
from utils.symbols import parse_symbols

logger = logging.getLogger(__name__)


class FinnhubMacroNewsProvider(NewsDataSource):
    """Fetches market-wide macro news from Finnhub's /news endpoint.

    Fetches general market news using ID-based pagination and maps articles to watchlist
    symbols based on the related field in each article. Falls back to 'MARKET' for
    articles that don't match any watchlist symbols.

    Rate Limits:
        Free tier: 60 calls/min.
        Each poll cycle makes one call (no per-symbol iteration for macro news).
    """

    def __init__(
        self, settings: FinnhubSettings, symbols: list[str], source_name: str = "Finnhub Macro"
    ) -> None:
        super().__init__(source_name)
        self.symbols = [s.strip().upper() for s in symbols if s.strip()]
        self.client = FinnhubClient(settings)
        self.last_fetched_max_id: int | None = None

    async def validate_connection(self) -> bool:
        return await self.client.validate_connection()

    async def fetch_incremental(
        self,
        *,
        min_id: int | None = None,
    ) -> list[NewsEntry]:
        now_utc = datetime.now(UTC)

        if min_id is None:
            buffer_time = now_utc - timedelta(days=2)
        else:
            buffer_time = None

        news_entries: list[NewsEntry] = []
        params: dict[str, Any] = {"category": "general"}

        if min_id is not None:
            params["minId"] = min_id

        articles = await self.client.get("/news", params)

        if not isinstance(articles, list):
            raise DataSourceError(f"Finnhub API returned {type(articles).__name__} instead of list")

        if min_id is not None:
            filtered_articles = [
                article
                for article in articles
                if isinstance(article.get("id"), int) and article["id"] > min_id
            ]
            if len(filtered_articles) < len(articles):
                logger.debug(
                    f"Filtered {len(articles) - len(filtered_articles)} articles "
                    f"with id <= {min_id}"
                )
            articles = filtered_articles

        for article in articles:
            try:
                items = self._parse_article(article, buffer_time)
                news_entries.extend(items)
            except (ValueError, TypeError, KeyError, AttributeError) as exc:
                logger.debug(
                    f"Failed to parse macro news article {article.get('id', 'unknown')}: {exc}"
                )
                continue

        ids = [
            article["id"]
            for article in articles
            if isinstance(article.get("id"), int) and article["id"] > 0
        ]
        self.last_fetched_max_id = max(ids) if ids else None

        return news_entries

    def _parse_article(
        self,
        article: dict[str, Any],
        buffer_time: datetime | None,
    ) -> list[NewsEntry]:
        headline = article.get("headline", "").strip()
        url = article.get("url", "").strip()
        datetime_epoch = article.get("datetime", 0)

        if not headline or not url or datetime_epoch <= 0:
            return []

        try:
            published = datetime.fromtimestamp(datetime_epoch, tz=UTC)
        except (ValueError, OSError) as exc:
            logger.debug(
                f"Skipping macro news article due to invalid epoch {datetime_epoch}: {exc}"
            )
            return []

        if buffer_time and published <= buffer_time:
            logger.warning(
                f"Finnhub API returned article with published={published.isoformat()} "
                f"at/before cutoff {_datetime_to_iso(buffer_time)} despite default lookback"
            )
            return []

        related = article.get("related", "").strip()
        symbols = self._extract_symbols_from_related(related)
        source = article.get("source", "").strip() or "Finnhub"
        summary = article.get("summary", "").strip()
        content = summary if summary else None

        entries: list[NewsEntry] = []
        try:
            article_model = NewsItem(
                url=url,
                headline=headline,
                published=published,
                source=source,
                news_type=NewsType.MACRO,
                content=content,
            )
        except ValueError as exc:
            logger.debug(f"NewsItem validation failed (url={url}): {exc}")
            return []
        for symbol in symbols:
            try:
                entries.append(NewsEntry(article=article_model, symbol=symbol, is_important=None))
            except ValueError as exc:
                logger.debug(f"NewsEntry validation failed for {symbol} (url={url}): {exc}")
                continue

        return entries

    def _extract_symbols_from_related(self, related: str | None) -> list[str]:
        if not related or not related.strip():
            return ["MARKET"]

        symbols = parse_symbols(
            related,
            filter_to=self.symbols,
            validate=True,
            log_label="RELATED",
        )

        if not symbols:
            return ["MARKET"]

        return symbols
