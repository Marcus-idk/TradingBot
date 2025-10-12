"""
Tests for PolygonSettings configuration.
Tests environment variable loading and validation.
"""

import pytest
from config.providers.polygon import PolygonSettings
from config.retry import DEFAULT_DATA_RETRY


class TestPolygonSettings:
    """Test PolygonSettings.from_env() method"""

    def test_from_env_success(self, monkeypatch):
        """Test successful loading when POLYGON_API_KEY is set"""
        monkeypatch.setenv('POLYGON_API_KEY', 'test_key_123')

        settings = PolygonSettings.from_env()

        assert settings.api_key == 'test_key_123'
        assert settings.base_url == 'https://api.polygon.io'
        assert settings.retry_config == DEFAULT_DATA_RETRY

    def test_from_env_missing_key(self, monkeypatch):
        """Test raises ValueError when POLYGON_API_KEY is not set"""
        monkeypatch.delenv('POLYGON_API_KEY', raising=False)

        with pytest.raises(ValueError) as exc_info:
            PolygonSettings.from_env()

        assert 'POLYGON_API_KEY environment variable not found or empty' in str(exc_info.value)

    def test_from_env_empty_key(self, monkeypatch):
        """Test raises ValueError when POLYGON_API_KEY is empty string"""
        monkeypatch.setenv('POLYGON_API_KEY', '')

        with pytest.raises(ValueError) as exc_info:
            PolygonSettings.from_env()

        assert 'POLYGON_API_KEY environment variable not found or empty' in str(exc_info.value)

    def test_from_env_whitespace_key(self, monkeypatch):
        """Test raises ValueError when POLYGON_API_KEY is only whitespace"""
        monkeypatch.setenv('POLYGON_API_KEY', '   ')

        with pytest.raises(ValueError) as exc_info:
            PolygonSettings.from_env()

        assert 'POLYGON_API_KEY environment variable is empty or whitespace' in str(exc_info.value)

    def test_from_env_strips_whitespace(self, monkeypatch):
        """Test that whitespace is stripped from API key"""
        monkeypatch.setenv('POLYGON_API_KEY', '  test_key_with_spaces  ')

        settings = PolygonSettings.from_env()

        assert settings.api_key == 'test_key_with_spaces'

    def test_from_env_custom_env_dict(self):
        """Test using custom environment dictionary instead of os.environ"""
        custom_env = {'POLYGON_API_KEY': 'custom_key'}

        settings = PolygonSettings.from_env(env=custom_env)

        assert settings.api_key == 'custom_key'
        assert settings.base_url == 'https://api.polygon.io'
        assert settings.retry_config == DEFAULT_DATA_RETRY
