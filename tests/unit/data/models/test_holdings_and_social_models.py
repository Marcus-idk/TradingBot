"""Holdings and social discussion model validation tests."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from data.models import Holdings, SocialDiscussion


class TestHoldings:
    """Test Holdings model validation"""

    def test_holdings_symbol_uppercasing(self):
        """Test symbol is automatically uppercased"""
        holding = Holdings(
            symbol="aapl",
            quantity=Decimal("100"),
            break_even_price=Decimal("150.00"),
            total_cost=Decimal("15000.00"),
        )
        assert holding.symbol == "AAPL"

        # Test mixed case
        holding2 = Holdings(
            symbol="nVdA",
            quantity=Decimal("50"),
            break_even_price=Decimal("500.00"),
            total_cost=Decimal("25000.00"),
            notes="Test holding",
        )
        assert holding2.symbol == "NVDA"

    def test_holdings_financial_values_positive(self):
        """Test quantity > 0, break_even_price > 0, total_cost > 0"""
        base_data = {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "break_even_price": Decimal("150.00"),
            "total_cost": Decimal("15000.00"),
        }

        # Valid positive values
        item = Holdings(**base_data)
        assert item.quantity == Decimal("100")
        assert item.break_even_price == Decimal("150.00")
        assert item.total_cost == Decimal("15000.00")

        for field, value in [
            ("quantity", Decimal("0")),
            ("quantity", Decimal("-10")),
            ("break_even_price", Decimal("0")),
            ("break_even_price", Decimal("-50.00")),
            ("total_cost", Decimal("0")),
            ("total_cost", Decimal("-1000.00")),
        ]:
            with pytest.raises(ValueError, match=f"{field} must be > 0"):
                Holdings(**{**base_data, field: value})

    def test_holdings_decimal_precision(self):
        """Test all financial fields maintain Decimal precision"""
        item = Holdings(
            symbol="AAPL",
            quantity=Decimal("123.456789"),
            break_even_price=Decimal("987.654321"),
            total_cost=Decimal("121932.100508"),
        )

        # Verify all are Decimal types with exact precision
        assert isinstance(item.quantity, Decimal)
        assert isinstance(item.break_even_price, Decimal)
        assert isinstance(item.total_cost, Decimal)
        assert item.quantity == Decimal("123.456789")
        assert item.break_even_price == Decimal("987.654321")
        assert item.total_cost == Decimal("121932.100508")

    def test_holdings_timezone_normalization(self):
        """Test timezone normalization for created_at and updated_at"""
        naive_dt = datetime(2024, 1, 15, 10, 30)
        base_data = {
            "symbol": "AAPL",
            "quantity": Decimal("100"),
            "break_even_price": Decimal("150.00"),
            "total_cost": Decimal("15000.00"),
        }

        # Test created_at timezone normalization when provided
        item = Holdings(**{**base_data, "created_at": naive_dt})
        assert item.created_at is not None
        assert item.created_at.tzinfo == UTC

        # Test updated_at timezone normalization when provided
        item = Holdings(**{**base_data, "updated_at": naive_dt})
        assert item.updated_at is not None
        assert item.updated_at.tzinfo == UTC

        # Test both fields together
        item = Holdings(**{**base_data, "created_at": naive_dt, "updated_at": naive_dt})
        assert item.created_at is not None
        assert item.created_at.tzinfo == UTC
        assert item.updated_at is not None
        assert item.updated_at.tzinfo == UTC

    def test_holdings_symbol_validation(self):
        """Test symbol stripping and empty validation"""
        base_data = {
            "quantity": Decimal("100"),
            "break_even_price": Decimal("150.00"),
            "total_cost": Decimal("15000.00"),
        }

        # Symbol with whitespace should be trimmed
        item = Holdings(
            symbol="  AAPL  ",
            quantity=base_data["quantity"],
            break_even_price=base_data["break_even_price"],
            total_cost=base_data["total_cost"],
        )
        assert item.symbol == "AAPL"

        # Empty symbol after strip should raise ValueError
        with pytest.raises(ValueError, match="symbol cannot be empty"):
            Holdings(
                symbol="   ",
                quantity=base_data["quantity"],
                break_even_price=base_data["break_even_price"],
                total_cost=base_data["total_cost"],
            )

    def test_holdings_notes_trimming(self):
        """Test notes field trimming when provided"""
        item = Holdings(
            symbol="AAPL",
            quantity=Decimal("100"),
            break_even_price=Decimal("150.00"),
            total_cost=Decimal("15000.00"),
            notes="  Buy more shares  ",
        )

        # Notes should be trimmed
        assert item.notes == "Buy more shares"


class TestSocialDiscussion:
    """SocialDiscussion model validation and normalization."""

    @pytest.mark.parametrize(
        "field, value, message",
        [
            ("source", "  ", "source cannot be empty"),
            ("source_id", "", "source_id cannot be empty"),
            ("symbol", " ", "symbol cannot be empty"),
            ("community", "", "community cannot be empty"),
            ("title", " ", "title cannot be empty"),
            ("url", "not-a-url", "url must be http"),
        ],
    )
    def test_required_fields_raise_value_error(self, field, value, message):
        """Empty or invalid fields raise ValueError."""
        kwargs = {
            "source": "reddit",
            "source_id": "t3_1",
            "symbol": "AAPL",
            "community": "stocks",
            "title": "Title",
            "url": "https://reddit.com",
            "published": datetime(2024, 1, 15, 12, 0),
            "content": "Body",
        }
        kwargs[field] = value

        with pytest.raises(ValueError, match=message):
            SocialDiscussion(**kwargs)  # type: ignore[arg-type]

    def test_non_datetime_published_raises(self):
        """Non-datetime published values raise ValueError."""
        with pytest.raises(ValueError):
            SocialDiscussion(
                source="reddit",
                source_id="t3_1",
                symbol="AAPL",
                community="stocks",
                title="Title",
                url="https://reddit.com",
                published="2024-01-01",  # type: ignore[arg-type]
            )

    def test_normalization_strips_and_uppercases(self):
        """Whitespace trimmed; symbol uppercased; published normalized to UTC."""
        naive_time = datetime(2024, 1, 15, 9, 30)
        discussion = SocialDiscussion(
            source=" reddit ",
            source_id=" t3_123 ",
            symbol="aapl",
            community=" stocks ",
            title=" Title ",
            url=" https://reddit.com/r/stocks ",
            published=naive_time,
            content=" Keep spacing ",
        )

        assert discussion.source == "reddit"
        assert discussion.source_id == "t3_123"
        assert discussion.symbol == "AAPL"
        assert discussion.community == "stocks"
        assert discussion.title == "Title"
        assert discussion.url == "https://reddit.com/r/stocks"
        assert discussion.published.tzinfo is UTC
        assert discussion.content == " Keep spacing "
