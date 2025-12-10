"""News-related data model validation tests."""

from datetime import UTC, datetime

import pytest

from data.models import NewsEntry, NewsItem, NewsSymbol, NewsType


class TestNewsItem:
    """Test NewsItem model validation."""

    def test_newsitem_valid_creation(self):
        """Valid NewsItem requires url/headline/source/news_type."""
        item = NewsItem(
            url="https://example.com/news/1",
            headline="Apple Stock Rises",
            source="Reuters",
            published=datetime(2024, 1, 15, 10, 30),
            news_type=NewsType.COMPANY_SPECIFIC,
            content="Optional content here",
        )
        assert item.url == "https://example.com/news/1"
        assert item.headline == "Apple Stock Rises"
        assert item.source == "Reuters"
        assert item.published.tzinfo == UTC
        assert item.content == "Optional content here"
        assert item.news_type is NewsType.COMPANY_SPECIFIC

    @pytest.mark.parametrize(
        "url",
        [
            "http://example.com",
            "https://example.com",
            "https://example.com/path?param=value",
        ],
    )
    def test_newsitem_url_validation_accepts_http(self, url):
        """URL must allow http/https."""
        base = {
            "headline": "Test",
            "source": "Test Source",
            "published": datetime.now(),
            "news_type": NewsType.COMPANY_SPECIFIC,
        }
        item = NewsItem(url=url, **base)
        assert item.url == url

    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com",
            "file:///path/to/file",
            "data:text/plain;base64,SGVsbG8=",
            "javascript:alert(1)",
            "invalid-url",
            "",
        ],
    )
    def test_newsitem_url_validation_rejects_non_http(self, url):
        """URL must be http(s)."""
        base = {
            "headline": "Test Headline",
            "source": "Test Source",
            "published": datetime.now(),
            "news_type": NewsType.MACRO,
        }
        with pytest.raises(ValueError, match="url must be http\\(s\\)"):
            NewsItem(url=url, **base)

    @pytest.mark.parametrize(
        "field, value, message",
        [
            ("headline", "\t\n", "headline cannot be empty"),
            ("source", "", "source cannot be empty"),
        ],
    )
    def test_newsitem_empty_field_validation(self, field, value, message):
        """headline and source required after strip()."""
        base = {
            "url": "https://example.com",
            "headline": "Test Headline",
            "source": "Test Source",
            "published": datetime.now(),
            "news_type": NewsType.MACRO,
            "content": "  \n  ",
        }
        base[field] = value
        with pytest.raises(ValueError, match=message):
            NewsItem(**base)

        item = NewsItem(**{**base, field: "Ok"})
        assert item.content == "  \n  "

    def test_newsitem_news_type_variants(self):
        """news_type accepts enum instances or exact strings."""
        item_enum = NewsItem(
            url="https://example.com/enum",
            headline="Enum",
            source="Source",
            published=datetime.now(),
            news_type=NewsType.MACRO,
        )
        assert item_enum.news_type is NewsType.MACRO

        item_str = NewsItem(
            url="https://example.com/string",
            headline="String",
            source="Source",
            published=datetime.now(),
            news_type="company_specific",
        )
        assert item_str.news_type is NewsType.COMPANY_SPECIFIC

        with pytest.raises(ValueError, match="valid NewsType"):
            NewsItem(
                url="https://example.com/invalid",
                headline="Invalid",
                source="Source",
                published=datetime.now(),
                news_type="invalid",
            )

    def test_newsitem_timezone_normalization(self):
        """Naive datetimes converted to UTC."""
        naive_dt = datetime(2024, 1, 15, 10, 30)
        item = NewsItem(
            url="https://example.com",
            headline="Test",
            source="Source",
            published=naive_dt,
            news_type=NewsType.COMPANY_SPECIFIC,
        )

        assert item.published.tzinfo == UTC
        assert item.published.year == 2024
        assert item.published.month == 1
        assert item.published.day == 15


class TestNewsEntry:
    """Tests for NewsEntry wrapper semantics."""

    @staticmethod
    def _article() -> NewsItem:
        return NewsItem(
            url="https://example.com/news",
            headline="Headline",
            source="Source",
            published=datetime(2024, 1, 15, 9, 0),
            news_type=NewsType.COMPANY_SPECIFIC,
        )

    def test_newsentry_symbol_uppercasing_and_passthrough(self):
        """Test newsentry symbol uppercasing and passthrough."""
        article = self._article()
        entry = NewsEntry(article=article, symbol="aapl", is_important=None)

        assert entry.symbol == "AAPL"
        assert entry.url == article.url
        assert entry.headline == article.headline
        assert entry.source == article.source
        assert entry.published == article.published
        assert entry.news_type is NewsType.COMPANY_SPECIFIC

    def test_newsentry_is_important_accepts_bool_or_none(self):
        """Test newsentry is important accepts bool or none."""
        article = self._article()
        assert NewsEntry(article=article, symbol="MSFT", is_important=True).is_important is True
        assert NewsEntry(article=article, symbol="TSLA", is_important=False).is_important is False
        assert NewsEntry(article=article, symbol="GOOG", is_important=None).is_important is None

    def test_newsentry_requires_non_empty_symbol(self):
        """Test newsentry requires non empty symbol."""
        article = self._article()
        with pytest.raises(ValueError, match="symbol cannot be empty"):
            NewsEntry(article=article, symbol="  ", is_important=None)

    def test_newsentry_invalid_is_important_value(self):
        """Test newsentry invalid is important value."""
        article = self._article()
        with pytest.raises(ValueError, match="is_important must be True, False, or None"):
            NewsEntry(article=article, symbol="AAPL", is_important="yes")  # type: ignore[arg-type]


class TestNewsSymbol:
    """Tests for NewsSymbol link validation."""

    def test_newssymbol_valid_creation(self):
        """Test newssymbol valid creation."""
        link = NewsSymbol(url="https://example.com/news", symbol="aapl", is_important=None)
        assert link.url == "https://example.com/news"
        assert link.symbol == "AAPL"
        assert link.is_important is None

    def test_newssymbol_importance_bool_conversion(self):
        """Test newssymbol importance bool conversion."""
        assert (
            NewsSymbol(
                url="https://example.com/news", symbol="msft", is_important=True
            ).is_important
            is True
        )
        assert (
            NewsSymbol(
                url="https://example.com/news", symbol="msft", is_important=False
            ).is_important
            is False
        )

    def test_newssymbol_invalid_inputs_raise(self):
        """Test newssymbol invalid inputs raise."""
        with pytest.raises(ValueError, match="url must be http\\(s\\)"):
            NewsSymbol(url="ftp://example.com", symbol="AAPL")

        with pytest.raises(ValueError, match="symbol cannot be empty"):
            NewsSymbol(url="https://example.com", symbol="  ")

        with pytest.raises(ValueError, match="is_important must be True, False, or None"):
            NewsSymbol(url="https://example.com", symbol="AAPL", is_important=2)  # type: ignore[arg-type]
