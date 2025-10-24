"""
Tests for _cursor_context() internal database context manager.

Tests commit/rollback behavior, cleanup, and row_factory configuration.
"""

import sqlite3

import pytest

from data.storage.db_context import _cursor_context


class TestCursorContext:
    """Test _cursor_context() context manager behavior"""

    def test_cursor_context_commit_true_commits_on_success(self, temp_db):
        """Test that commit=True (default) commits on successful operations"""
        # Insert data with commit=True (default)
        with _cursor_context(temp_db) as cursor:
            cursor.execute(
                (
                    "INSERT INTO news_items (symbol, url, headline, published_iso, source) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("AAPL", "https://test.com/1", "Test", "2024-01-01T00:00:00Z", "Test"),
            )

        # Verify data was committed by reading in a new connection
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("SELECT symbol FROM news_items WHERE url = ?", ("https://test.com/1",))
            result = cursor.fetchone()
            assert result is not None
            assert result["symbol"] == "AAPL"

    def test_cursor_context_commit_false_no_commit(self, temp_db):
        """Test that commit=False does not commit changes"""
        # Try to insert with commit=False
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute(
                (
                    "INSERT INTO news_items (symbol, url, headline, published_iso, source) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("TSLA", "https://test.com/2", "Test", "2024-01-01T00:00:00Z", "Test"),
            )

        # Verify data was NOT committed (should rollback on exit)
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("SELECT symbol FROM news_items WHERE url = ?", ("https://test.com/2",))
            result = cursor.fetchone()
            assert result is None

    def test_cursor_context_rollback_on_exception(self, temp_db):
        """Test that exceptions trigger rollback"""
        # Insert should be rolled back due to exception
        with pytest.raises(ValueError):
            with _cursor_context(temp_db) as cursor:
                cursor.execute(
                    (
                        "INSERT INTO news_items (symbol, url, headline, published_iso, source) "
                        "VALUES (?, ?, ?, ?, ?)"
                    ),
                    ("MSFT", "https://test.com/3", "Test", "2024-01-01T00:00:00Z", "Test"),
                )
                raise ValueError("Intentional error")

        # Verify rollback happened - no data should exist
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("SELECT symbol FROM news_items WHERE url = ?", ("https://test.com/3",))
            result = cursor.fetchone()
            assert result is None

    def test_cursor_context_rollback_on_base_exception(self, temp_db):
        """Test that BaseException (like SystemExit) also triggers rollback"""
        # BaseException should also trigger rollback
        with pytest.raises(SystemExit):
            with _cursor_context(temp_db) as cursor:
                cursor.execute(
                    (
                        "INSERT INTO news_items (symbol, url, headline, published_iso, source) "
                        "VALUES (?, ?, ?, ?, ?)"
                    ),
                    ("GOOGL", "https://test.com/4", "Test", "2024-01-01T00:00:00Z", "Test"),
                )
                raise SystemExit("Simulated system exit")

        # Verify rollback happened
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("SELECT symbol FROM news_items WHERE url = ?", ("https://test.com/4",))
            result = cursor.fetchone()
            assert result is None

    def test_cursor_context_sets_row_factory(self, temp_db):
        """Test that sqlite3.Row factory is set for dict-like access"""
        # Insert a row
        with _cursor_context(temp_db) as cursor:
            cursor.execute(
                (
                    "INSERT INTO news_items (symbol, url, headline, published_iso, source) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                ("AMZN", "https://test.com/5", "Test Headline", "2024-01-01T00:00:00Z", "Reuters"),
            )

        # Verify row_factory enables dict-like access
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute(
                "SELECT symbol, headline, source FROM news_items WHERE url = ?",
                ("https://test.com/5",),
            )
            row = cursor.fetchone()

            # Test dict-like access
            assert row["symbol"] == "AMZN"
            assert row["headline"] == "Test Headline"
            assert row["source"] == "Reuters"

            # Also test tuple-style access
            assert row[0] == "AMZN"
            assert row[1] == "Test Headline"
            assert row[2] == "Reuters"

    def test_cursor_context_cleanup_on_cursor_error(self, temp_db):
        """Test that connection cleanup happens even if cursor operations fail"""
        # Intentionally cause a SQL error
        with pytest.raises(sqlite3.OperationalError):
            with _cursor_context(temp_db) as cursor:
                cursor.execute("SELECT * FROM nonexistent_table")

        # Verify we can still use the database (connection was closed properly)
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            assert len(tables) > 0  # Should still work

    def test_cursor_context_cleanup_in_finally(self, temp_db):
        """Test that connection is always closed via finally block"""
        # First, verify successful path closes connection
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("SELECT 1")
            # Connection should close after this block

        # Then verify error path also closes connection
        with pytest.raises(RuntimeError):
            with _cursor_context(temp_db) as cursor:
                cursor.execute(
                    (
                        "INSERT INTO news_items (symbol, url, headline, published_iso, source) "
                        "VALUES (?, ?, ?, ?, ?)"
                    ),
                    ("FB", "https://test.com/6", "Test", "2024-01-01T00:00:00Z", "Test"),
                )
                raise RuntimeError("Test error")

        # Verify we can still access database (connections were properly closed)
        with _cursor_context(temp_db, commit=False) as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM news_items")
            result = cursor.fetchone()
            assert result is not None  # Should still work
