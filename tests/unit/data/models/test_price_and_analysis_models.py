"""Price and analysis model validation tests."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from data.models import AnalysisResult, AnalysisType, PriceData, Session, Stance


class TestPriceData:
    """Test PriceData model validation"""

    def test_pricedata_symbol_uppercasing(self):
        """Test symbol is automatically uppercased"""
        price = PriceData(symbol="aapl", timestamp=datetime.now(), price=Decimal("150.50"))
        assert price.symbol == "AAPL"

        # Test mixed case
        price2 = PriceData(
            symbol="mSfT", timestamp=datetime.now(), price=Decimal("400.00"), volume=1000
        )
        assert price2.symbol == "MSFT"

    @pytest.mark.parametrize(
        "price",
        [Decimal("150.00"), Decimal("0"), Decimal("-10.50")],
    )
    def test_pricedata_price_must_be_positive(self, price):
        """price must be > 0."""
        base = {"symbol": "AAPL", "timestamp": datetime.now()}
        if price > 0:
            item = PriceData(**{**base, "price": price})
            assert item.price == price
        else:
            with pytest.raises(ValueError, match="price must be > 0"):
                PriceData(**{**base, "price": price})

    def test_pricedata_volume_validation(self):
        """Test volume >= 0 validation (can be None)"""
        base_data = {"symbol": "AAPL", "timestamp": datetime.now(), "price": Decimal("150.00")}

        # Volume can be None
        item = PriceData(**base_data)
        assert item.volume is None

        # Volume can be zero
        item = PriceData(**{**base_data, "volume": 0})
        assert item.volume == 0

        # Volume can be positive
        item = PriceData(**{**base_data, "volume": 1000})
        assert item.volume == 1000

        # Negative volume should raise ValueError
        with pytest.raises(ValueError, match="volume must be >= 0"):
            PriceData(**{**base_data, "volume": -100})

    def test_pricedata_session_enum_validation(self):
        """Test Session enum validation"""
        base_data = {"symbol": "AAPL", "timestamp": datetime.now(), "price": Decimal("150.00")}

        # Valid enum values
        for session in [Session.REG, Session.PRE, Session.POST, Session.CLOSED]:
            item = PriceData(**{**base_data, "session": session})
            assert item.session == session

        for bad_session in ["REG", "INVALID"]:
            with pytest.raises(ValueError, match="session must be a Session enum value"):
                PriceData(**{**base_data, "session": bad_session})

    def test_pricedata_decimal_precision(self):
        """Test Decimal type preservation"""
        item = PriceData(symbol="AAPL", timestamp=datetime.now(), price=Decimal("123.456789"))

        # Verify Decimal type preserved
        assert isinstance(item.price, Decimal)
        assert item.price == Decimal("123.456789")

    def test_pricedata_timezone_normalization(self):
        """Test timestamp timezone normalization"""
        naive_dt = datetime(2024, 1, 15, 10, 30)
        item = PriceData(symbol="AAPL", timestamp=naive_dt, price=Decimal("150.00"))

        # Should be converted to UTC
        assert item.timestamp.tzinfo == UTC
        assert item.timestamp.year == 2024
        assert item.timestamp.month == 1
        assert item.timestamp.day == 15

    def test_pricedata_symbol_validation(self):
        """Test symbol stripping and empty validation"""
        base_data = {"timestamp": datetime.now(), "price": Decimal("150.00")}

        # Symbol with whitespace should be trimmed
        item = PriceData(symbol="  AAPL  ", **base_data)
        assert item.symbol == "AAPL"

        # Empty symbol after strip should raise ValueError
        with pytest.raises(ValueError, match="symbol cannot be empty"):
            PriceData(symbol="   ", **base_data)


class TestAnalysisResult:
    """Test AnalysisResult model validation"""

    def test_analysisresult_symbol_uppercasing(self):
        """Test symbol is automatically uppercased"""
        result = AnalysisResult(
            symbol="aapl",
            analysis_type=AnalysisType.NEWS_ANALYSIS,
            model_name="gpt-4",
            stance=Stance.BULL,
            confidence_score=0.85,
            last_updated=datetime.now(),
            result_json='{"test": "data"}',
        )
        assert result.symbol == "AAPL"

        # Test mixed case
        result2 = AnalysisResult(
            symbol="gOoGl",
            analysis_type=AnalysisType.SENTIMENT_ANALYSIS,
            model_name="gemini",
            stance=Stance.NEUTRAL,
            confidence_score=0.5,
            last_updated=datetime.now(),
            result_json='{"analysis": "neutral"}',
        )
        assert result2.symbol == "GOOGL"

    def test_analysisresult_json_validation(self):
        """Test result_json must be valid JSON object"""
        base_data = {
            "symbol": "AAPL",
            "analysis_type": AnalysisType.NEWS_ANALYSIS,
            "model_name": "gpt-4",
            "stance": Stance.BULL,
            "confidence_score": 0.85,
            "last_updated": datetime.now(),
            "result_json": '{"key": "value"}',
        }

        # Valid JSON object
        item = AnalysisResult(**base_data)
        assert item.result_json == '{"key": "value"}'

        # Invalid JSON string (not JSON)
        with pytest.raises(ValueError, match="result_json must be valid JSON"):
            AnalysisResult(**{**base_data, "result_json": "not-json"})

        # JSON that is not an object (e.g., list)
        with pytest.raises(ValueError, match="result_json must be a JSON object"):
            AnalysisResult(**{**base_data, "result_json": '["not", "an", "object"]'})

    def test_analysisresult_confidence_score_validation(self):
        """Test confidence_score range validation"""
        base_data = {
            "symbol": "AAPL",
            "analysis_type": AnalysisType.NEWS_ANALYSIS,
            "model_name": "gpt-4",
            "stance": Stance.BULL,
            "last_updated": datetime.now(),
            "result_json": '{"key": "value"}',
        }

        # Valid boundary values
        valid_scores = [0.0, 0.5, 1.0, 0.1234, 0.9999]
        for score in valid_scores:
            item = AnalysisResult(**{**base_data, "confidence_score": score})
            assert item.confidence_score == score

        # Invalid values outside range
        for score in [-0.1, -1.0, 1.1, 2.0]:
            with pytest.raises(ValueError, match="confidence_score must be between 0.0 and 1.0"):
                AnalysisResult(**{**base_data, "confidence_score": score})

    def test_analysisresult_enum_validation(self):
        """Test AnalysisType and Stance enum validation"""
        base_data = {
            "symbol": "AAPL",
            "analysis_type": AnalysisType.NEWS_ANALYSIS,
            "model_name": "gpt-4",
            "stance": Stance.BULL,
            "confidence_score": 0.5,
            "last_updated": datetime.now(),
            "result_json": '{"key": "value"}',
        }

        # Valid AnalysisType values
        for analysis_type in [
            AnalysisType.NEWS_ANALYSIS,
            AnalysisType.SENTIMENT_ANALYSIS,
            AnalysisType.SEC_FILINGS,
            AnalysisType.HEAD_TRADER,
        ]:
            item = AnalysisResult(**{**base_data, "analysis_type": analysis_type})
            assert item.analysis_type == analysis_type

        # Valid Stance values
        for stance in [Stance.BULL, Stance.BEAR, Stance.NEUTRAL]:
            item = AnalysisResult(**{**base_data, "stance": stance})
            assert item.stance == stance

        with pytest.raises(ValueError, match="analysis_type must be an AnalysisType enum value"):
            AnalysisResult(**{**base_data, "analysis_type": "news_analysis"})

        with pytest.raises(ValueError, match="stance must be a Stance enum value"):
            AnalysisResult(**{**base_data, "stance": "BULL"})

    def test_analysisresult_timezone_normalization(self):
        """Test timezone normalization for last_updated and created_at"""
        naive_dt = datetime(2024, 1, 15, 10, 30)
        base_data = {
            "symbol": "AAPL",
            "analysis_type": AnalysisType.NEWS_ANALYSIS,
            "model_name": "gpt-4",
            "stance": Stance.BULL,
            "confidence_score": 0.5,
            "result_json": '{"key": "value"}',
        }

        # Test last_updated timezone normalization
        item = AnalysisResult(**{**base_data, "last_updated": naive_dt})
        assert item.last_updated is not None
        assert item.last_updated.tzinfo == UTC

        # Test created_at timezone normalization when provided
        item_with_created = AnalysisResult(
            **{**base_data, "last_updated": naive_dt, "created_at": naive_dt}
        )
        assert item_with_created.created_at is not None
        assert item_with_created.created_at.tzinfo == UTC
        assert item_with_created.last_updated is not None
        assert item_with_created.last_updated.tzinfo == UTC

    def test_analysisresult_symbol_validation(self):
        """Test symbol stripping and empty validation"""
        base_data = {
            "analysis_type": AnalysisType.NEWS_ANALYSIS,
            "model_name": "gpt-4",
            "stance": Stance.BULL,
            "confidence_score": 0.5,
            "last_updated": datetime.now(),
            "result_json": '{"key": "value"}',
        }

        # Symbol with whitespace should be trimmed
        item = AnalysisResult(symbol="  AAPL  ", **base_data)
        assert item.symbol == "AAPL"

        with pytest.raises(ValueError, match="symbol cannot be empty"):
            AnalysisResult(symbol="   ", **base_data)

    def test_analysisresult_empty_string_validation(self):
        """Test model_name and result_json empty string validation"""
        base_data = {
            "symbol": "AAPL",
            "analysis_type": AnalysisType.NEWS_ANALYSIS,
            "stance": Stance.BULL,
            "confidence_score": 0.5,
            "last_updated": datetime.now(),
            "result_json": '{"key": "value"}',
        }

        with pytest.raises(ValueError, match="model_name cannot be empty"):
            AnalysisResult(**{**base_data, "model_name": "   "})

        with pytest.raises(ValueError, match="result_json cannot be empty"):
            AnalysisResult(**{**base_data, "model_name": "gpt-4", "result_json": "   "})
