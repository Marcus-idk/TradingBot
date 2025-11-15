"""Batch operations for trading bot data."""

from datetime import datetime

from data.models import NewsEntry, PriceData
from data.storage.db_context import _cursor_context
from data.storage.storage_utils import (
    _datetime_to_iso,
    _row_to_news_entry,
    _row_to_price_data,
)


def get_news_before(db_path: str, cutoff: datetime) -> list[NewsEntry]:
    """
    Get news entries created at or before the cutoff for LLM processing.

    Args:
        cutoff: Include items with created_at_iso <= this timestamp

    Returns:
        List of NewsEntry domain objects with datetime fields in UTC
    """
    iso_cutoff = _datetime_to_iso(cutoff)
    with _cursor_context(db_path, commit=False) as cursor:
        cursor.execute(
            """
            SELECT
                ni.url,
                ni.headline,
                ni.content,
                ni.published_iso,
                ni.source,
                ni.news_type,
                ns.symbol,
                ns.is_important
            FROM news_items AS ni
            JOIN news_symbols AS ns ON ns.url = ni.url
            WHERE ni.created_at_iso <= ?
            ORDER BY ni.created_at_iso ASC, ni.url ASC, ns.symbol ASC
        """,
            (iso_cutoff,),
        )

        return [_row_to_news_entry(dict(row)) for row in cursor.fetchall()]


def get_prices_before(db_path: str, cutoff: datetime) -> list[PriceData]:
    """
    Get price data created at or before the cutoff for LLM processing.

    Args:
        cutoff: Include items with created_at_iso <= this timestamp

    Returns:
        List of PriceData model objects with datetime fields in UTC
    """
    iso_cutoff = _datetime_to_iso(cutoff)
    with _cursor_context(db_path, commit=False) as cursor:
        cursor.execute(
            """
            SELECT symbol, timestamp_iso, price, volume, session, created_at_iso
            FROM price_data
            WHERE created_at_iso <= ?
            ORDER BY created_at_iso ASC, symbol ASC
        """,
            (iso_cutoff,),
        )

        return [_row_to_price_data(dict(row)) for row in cursor.fetchall()]


def commit_llm_batch(db_path: str, cutoff: datetime) -> dict[str, int]:
    """
    Atomically prune processed raw data up to a cutoff.

    This performs, in a single transaction, the following:
      - DELETE from `news_symbols`, `news_items`, and `price_data`
        where `created_at_iso <= cutoff`.

    Args:
        db_path: Path to the SQLite database
        cutoff: The snapshot cutoff used for the LLM batch

    Returns:
        Dict with counts of deleted rows:
        {"symbols_deleted": int, "news_deleted": int, "prices_deleted": int}
    """
    iso_cutoff = _datetime_to_iso(cutoff)
    with _cursor_context(db_path) as cursor:
        # Prune items processed in this batch
        # Note: ON DELETE CASCADE should auto-delete news_symbols when news_items are deleted,
        # but we explicitly delete here for clarity and to track the count.
        cursor.execute(
            """
            DELETE FROM news_symbols
            WHERE url IN (
                SELECT url
                FROM news_items
                WHERE created_at_iso <= ?
            )
        """,
            (iso_cutoff,),
        )
        symbols_deleted = cursor.rowcount

        cursor.execute("DELETE FROM news_items WHERE created_at_iso <= ?", (iso_cutoff,))
        news_deleted = cursor.rowcount

        cursor.execute("DELETE FROM price_data WHERE created_at_iso <= ?", (iso_cutoff,))
        prices_deleted = cursor.rowcount

    return {
        "symbols_deleted": symbols_deleted,
        "news_deleted": news_deleted,
        "prices_deleted": prices_deleted,
    }
