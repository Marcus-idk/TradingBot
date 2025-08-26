"""
Shared pytest fixtures and utilities for all tests.
This file is automatically discovered by pytest and its contents are available to all test files.
"""

import os
import tempfile
import pytest
from data.storage import init_database
from tests.fixtures.database import cleanup_sqlite_artifacts


@pytest.fixture
def temp_db_path():
    """Provides temporary database file path with automatic cleanup"""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield db_path
    cleanup_sqlite_artifacts(db_path)


@pytest.fixture
def temp_db(temp_db_path):
    """Provides initialized temporary database with automatic cleanup"""
    init_database(temp_db_path)
    return temp_db_path


# Make cleanup_sqlite_artifacts available to all test files
__all__ = ['cleanup_sqlite_artifacts']