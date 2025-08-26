"""
Shared pytest fixtures and utilities for all tests.
This file is automatically discovered by pytest and its contents are available to all test files.
"""

# Import shared database utilities
from tests.fixtures.database import cleanup_sqlite_artifacts

# Make cleanup_sqlite_artifacts available to all test files
__all__ = ['cleanup_sqlite_artifacts']