"""
Tests for FinnhubClient HTTP wrapper.
Split from combined provider tests for clearer 1:1 mapping.
"""

import pytest

from config.providers.finnhub import FinnhubSettings
from config.retry import DEFAULT_DATA_RETRY
from data.providers.finnhub import FinnhubClient


class TestFinnhubClient:
    """Test FinnhubClient HTTP wrapper"""

    @pytest.mark.asyncio
    async def test_builds_url_correctly(self, monkeypatch):
        """Test that client builds correct URL from base_url + path"""
        settings = FinnhubSettings(api_key='test_key')
        client = FinnhubClient(settings)

        captured_args = {}
        async def mock_get_json(*args, **kwargs):
            captured_args['url'] = args[0]
            captured_args['params'] = kwargs.get('params', {})
            return {'status': 'ok'}

        monkeypatch.setattr('data.providers.finnhub.finnhub_client.get_json_with_retry', mock_get_json)

        await client.get('/quote')

        assert captured_args['url'] == 'https://finnhub.io/api/v1/quote'

    @pytest.mark.asyncio
    async def test_injects_token_into_params(self, monkeypatch):
        """Test that API token is added to params"""
        settings = FinnhubSettings(api_key='secret_token_123')
        client = FinnhubClient(settings)

        captured_args = {}
        async def mock_get_json(*args, **kwargs):
            captured_args['params'] = kwargs.get('params', {})
            return {'status': 'ok'}

        monkeypatch.setattr('data.providers.finnhub.finnhub_client.get_json_with_retry', mock_get_json)

        await client.get('/company-news', params={'symbol': 'AAPL', 'from': '2024-01-01'})

        assert captured_args['params'] == {
            'symbol': 'AAPL',
            'from': '2024-01-01',
            'token': 'secret_token_123'
        }

    @pytest.mark.asyncio
    async def test_forwards_timeout_settings(self, monkeypatch):
        """Test that retry config settings are forwarded correctly"""
        settings = FinnhubSettings(api_key='test_key')
        client = FinnhubClient(settings)

        captured_args = {}
        async def mock_get_json(*args, **kwargs):
            captured_args.update(kwargs)
            return {'status': 'ok'}

        monkeypatch.setattr('data.providers.finnhub.finnhub_client.get_json_with_retry', mock_get_json)

        await client.get('/quote')

        assert captured_args['timeout'] == DEFAULT_DATA_RETRY.timeout_seconds
        assert captured_args['max_retries'] == DEFAULT_DATA_RETRY.max_retries
        assert captured_args['base'] == DEFAULT_DATA_RETRY.base
        assert captured_args['mult'] == DEFAULT_DATA_RETRY.mult
        assert captured_args['jitter'] == DEFAULT_DATA_RETRY.jitter

