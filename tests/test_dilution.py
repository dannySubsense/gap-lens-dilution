import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.utils.validation import validate_ticker, is_valid_ticker_format
from app.utils.formatting import format_number, format_currency, format_percentage


class TestValidateTicker:
    """Test cases for validate_ticker function"""

    def test_validate_ticker_with_valid_ticker(self):
        """Test validate_ticker with valid ticker symbols"""
        assert validate_ticker("AAPL") == "AAPL"
        assert validate_ticker("aapl") == "AAPL"
        assert validate_ticker(" goog ") == "GOOG"

    def test_validate_ticker_with_invalid_ticker(self):
        """Test validate_ticker with invalid ticker symbols"""
        with pytest.raises(ValueError, match="Ticker symbol must be a string"):
            validate_ticker(123)

        with pytest.raises(ValueError, match="Invalid ticker format"):
            validate_ticker("123456")  # Too long

        with pytest.raises(ValueError, match="Invalid ticker format"):
            validate_ticker("ABC DEF")  # Contains space

        with pytest.raises(ValueError, match="Invalid ticker format"):
            validate_ticker("")  # Empty string

    def test_is_valid_ticker_format(self):
        """Test is_valid_ticker_format function"""
        assert is_valid_ticker_format("AAPL") is True
        assert is_valid_ticker_format("GOOGL") is True
        assert is_valid_ticker_format("123") is False
        assert is_valid_ticker_format("ABC DEF") is False
        assert is_valid_ticker_format("") is False
        assert is_valid_ticker_format(None) is False


class TestFormatting:
    """Test cases for formatting functions"""

    def test_format_number(self):
        """Test format_number function"""
        assert format_number(1000) == "1.00K"
        assert format_number(1500) == "1.50K"
        assert format_number(1000000) == "1.00M"
        assert format_number(1000000000) == "1.00B"
        assert format_number(123.45) == "123.45"

    def test_format_currency(self):
        """Test format_currency function"""
        assert format_currency(1000) == "$1.00K"
        assert format_currency(1500) == "$1.50K"
        assert format_currency(1000000) == "$1.00M"
        assert format_currency(1000000000) == "$1.00B"
        assert format_currency(123.45) == "$123.45"

    def test_format_percentage(self):
        """Test format_percentage function"""
        assert format_percentage(10.5) == "10.50%"
        assert format_percentage(0) == "0.00%"
        assert format_percentage(100.0) == "100.00%"


class TestDilutionEndpoint:
    """Test cases for the /api/dilution/{ticker} endpoint"""

    @pytest.mark.asyncio
    async def test_endpoint_bad_request_invalid_ticker(self):
        """Test endpoint returns 400 for a syntactically invalid ticker."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/dilution/123456")
            assert response.status_code == 400
