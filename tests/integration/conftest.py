"""Shared pytest configuration for integration tests."""

import pytest

# Automatically mark every test in this package as integration.
pytestmark = pytest.mark.integration

