"""Common fixtures for data provider contract tests."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from config.providers.finnhub import FinnhubSettings
from config.retry import DataRetryConfig
from data import NewsDataSource, PriceDataSource
from data.providers.finnhub import (
    FinnhubMacroNewsProvider,
    FinnhubNewsProvider,
    FinnhubPriceProvider,
)
from data.providers.finnhub.finnhub_client import FinnhubClient


@dataclass(frozen=True)
class CompanyProviderSpec:
    name: str
    endpoint: str
    default_symbols: list[str]
    provider_factory: Callable[[list[str]], NewsDataSource]
    symbol_param_name: str
    article_factory: Callable[..., dict[str, Any]]

    def make_provider(self, symbols: list[str] | None = None) -> NewsDataSource:
        symbols_to_use = symbols if symbols is not None else list(self.default_symbols)
        return self.provider_factory(symbols_to_use)

    def wrap_response(self, payload: list[dict[str, Any]]) -> Any:
        return payload

    def malformed(self, *, as_type: type[Any]) -> Any:
        if as_type is dict:
            return {"unexpected": "structure"}
        return "unexpected"


@dataclass(frozen=True)
class MacroProviderSpec:
    name: str
    endpoint: str
    default_symbols: list[str]
    provider_factory: Callable[[list[str]], NewsDataSource]
    article_factory: Callable[..., dict[str, Any]]

    def make_provider(self, symbols: list[str] | None = None) -> NewsDataSource:
        symbols_to_use = symbols if symbols is not None else list(self.default_symbols)
        return self.provider_factory(symbols_to_use)

    def wrap_response(self, payload: list[dict[str, Any]]) -> Any:
        return payload

    def malformed(self, *, as_type: type[Any]) -> Any:
        if as_type is dict:
            return {"unexpected": "structure"}
        return "unexpected"


@dataclass(frozen=True)
class PriceProviderSpec:
    name: str
    endpoint: str
    default_symbols: list[str]
    provider_factory: Callable[[list[str]], PriceDataSource]

    def make_provider(self, symbols: list[str] | None = None) -> PriceDataSource:
        symbols_to_use = symbols if symbols is not None else list(self.default_symbols)
        return self.provider_factory(symbols_to_use)

    @staticmethod
    def quote(
        *,
        price: Any = Decimal("150.0"),
        timestamp: int | None = None,
        extras: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if price is not None:
            data["c"] = price
        if timestamp is not None:
            data["t"] = timestamp
        else:
            data["t"] = int(datetime.now(UTC).timestamp())
        if extras:
            data.update(extras)
        return data

    @staticmethod
    def malformed(*, as_type: type[Any]) -> Any:
        if as_type is dict:
            return {"unexpected": "structure"}
        return "unexpected"


@dataclass(frozen=True)
class ClientSpec:
    name: str
    module_path: str
    client_factory: Callable[[], Any]
    base_url: str
    sample_path: str
    sample_params: dict[str, Any]
    auth_param: str
    api_key: str
    retry_config: DataRetryConfig
    validation_path: str
    validation_params: dict[str, Any] | None

    def make_client(self) -> Any:
        return self.client_factory()


def _finnhub_settings() -> FinnhubSettings:
    return FinnhubSettings(api_key="test_key")


@pytest.fixture
def provider_spec_company() -> CompanyProviderSpec:
    """Parametrized company-news provider spec for Finnhub."""

    def finnhub_company_article_factory(**kwargs) -> dict[str, Any]:
        article: dict[str, Any] = {
            "headline": kwargs.get("headline", "Market rally"),
            "url": kwargs.get("url", "https://example.com/news"),
            "datetime": kwargs.get("epoch", int(datetime.now(UTC).timestamp())),
        }
        if "source" in kwargs and kwargs["source"] is not None:
            article["source"] = kwargs["source"]
        else:
            article["source"] = "Finnhub"
        if "summary" in kwargs and kwargs["summary"] is not None:
            article["summary"] = kwargs["summary"]
        else:
            article["summary"] = "Stocks up today"
        return article

    return CompanyProviderSpec(
        name="finnhub",
        endpoint="/company-news",
        default_symbols=["AAPL"],
        provider_factory=lambda symbols: FinnhubNewsProvider(_finnhub_settings(), symbols),
        symbol_param_name="symbol",
        article_factory=finnhub_company_article_factory,
    )


@pytest.fixture
def provider_spec_macro() -> MacroProviderSpec:
    """Parametrized macro-news provider spec for Finnhub."""

    def finnhub_article_factory(symbols: str | list[str] = "AAPL", **kwargs) -> dict[str, Any]:
        related_str = symbols if isinstance(symbols, str) else ",".join(symbols)
        article: dict[str, Any] = {
            "id": kwargs.get("article_id", 101),
            "headline": kwargs.get("headline", "Macro update"),
            "url": kwargs.get("url", "https://example.com/macro"),
            "datetime": kwargs.get("epoch", int(datetime.now(UTC).timestamp())),
            "related": related_str,
        }
        if "source" in kwargs and kwargs["source"] is not None:
            article["source"] = kwargs["source"]
        else:
            article["source"] = "Finnhub"
        if "summary" in kwargs and kwargs["summary"] is not None:
            article["summary"] = kwargs["summary"]
        else:
            article["summary"] = "Macro summary"
        return article

    return MacroProviderSpec(
        name="finnhub_macro",
        endpoint="/news",
        default_symbols=["AAPL"],
        provider_factory=lambda symbols: FinnhubMacroNewsProvider(_finnhub_settings(), symbols),
        article_factory=finnhub_article_factory,
    )


@pytest.fixture
def provider_spec_prices() -> PriceProviderSpec:
    """Price provider spec for Finnhub used by shared price contract tests."""
    return PriceProviderSpec(
        name="finnhub_prices",
        endpoint="/quote",
        default_symbols=["AAPL"],
        provider_factory=lambda symbols: FinnhubPriceProvider(_finnhub_settings(), symbols),
    )


@pytest.fixture
def client_spec() -> ClientSpec:
    """HTTP client spec for Finnhub client."""
    api_key = "finnhub_test_key"
    settings = FinnhubSettings(api_key=api_key)
    return ClientSpec(
        name="finnhub_client",
        module_path="data.providers.finnhub.finnhub_client",
        client_factory=lambda: FinnhubClient(settings),
        base_url=settings.base_url,
        sample_path="/company-news",
        sample_params={"symbol": "AAPL"},
        auth_param="token",
        api_key=api_key,
        retry_config=settings.retry_config,
        validation_path="/quote",
        validation_params={"symbol": "SPY"},
    )
