import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import create_app, app
from app.utils.validation import validate_ticker, is_valid_ticker_format
from app.utils.formatting import format_number, format_currency, format_percentage
from app.services.dilution import DilutionService
from app.utils.errors import TickerNotFoundError, RateLimitError, ExternalAPIError


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


class TestDilutionService:
    """Test cases for DilutionService"""

    @pytest.mark.asyncio
    async def test_dilution_service_success(self):
        """Test DilutionService successful API call"""
        service = DilutionService()
        service.client = AsyncMock()

        # Mock successful responses from both endpoints
        mock_dilution_response = AsyncMock()
        mock_dilution_response.status_code = 200
        mock_dilution_response.json.return_value = {
            "results": [{
                "overall_offering_risk": "Medium",
                "offering_ability": "High",
                "dilution": "Low",
                "cash_remaining_months": 12,
                "cash_burn": 1000000,
                "estimated_cash": 50000000
            }]
        }

        mock_float_response = AsyncMock()
        mock_float_response.status_code = 200
        mock_float_response.json.return_value = {
            "results": [{
                "float": 1000000000,
                "outstanding": 2000000000,
                "market_cap_final": 100000000000,
                "insider_percent": 0.15,
                "institutions_percent": 0.45
            }]
        }

        # Provide responses for both concurrent calls
        service.client.get = AsyncMock(side_effect=[mock_dilution_response, mock_float_response])

        result = await service.get_dilution_data("AAPL")

        # Verify camelCase mapping
        assert result["offeringRisk"] == "Medium"
        assert result["offeringAbility"] == "High"
        assert result["dilutionRisk"] == "Low"
        assert result["cashNeed"] == 12
        assert result["cashBurn"] == 1000000
        assert result["estimatedCash"] == 50000000
        assert result["float"] == 1000000000
        assert result["outstanding"] == 2000000000
        assert result["marketCap"] == 100000000000
        assert result["insiderOwnership"] == 0.15
        assert result["institutionalOwnership"] == 0.45

    @pytest.mark.asyncio
    async def test_dilution_service_ticker_not_found(self):
        """Test DilutionService handling of 404 response"""
        service = DilutionService()
        service.client = AsyncMock()
        
        # Mock 404 response
        mock_response = AsyncMock()
        mock_response.status_code = 404
        service.client.get = AsyncMock(return_value=mock_response)
        
        with pytest.raises(TickerNotFoundError):
            await service.get_dilution_data("INVALID")

    @pytest.mark.asyncio
    async def test_dilution_service_rate_limit(self):
        """Test DilutionService handling of rate limit response"""
        service = DilutionService()
        service.client = AsyncMock()

        # Mock 429 response
        mock_response = AsyncMock()
        mock_response.status_code = 429

        # Set up retry behavior - need enough responses for concurrent calls
        # Both endpoints are called concurrently, so we need 6 responses (3 retries each)
        service.client.get = AsyncMock()
        service.client.get.side_effect = [
            mock_response,  # dilution-rating: attempt 1
            mock_response,  # float-outstanding: attempt 1
            mock_response,  # dilution-rating: attempt 2
            mock_response,  # float-outstanding: attempt 2
            mock_response,  # dilution-rating: attempt 3
            mock_response,  # float-outstanding: attempt 3
        ]

        with pytest.raises(RateLimitError):
            await service.get_dilution_data("AAPL")


class TestDilutionEndpoint:
    """Test cases for the /api/dilution/{ticker} endpoint"""
    
    @pytest.mark.asyncio
    async def test_endpoint_success(self):
        """Test successful endpoint call"""
        with patch('app.api.v1.routes.dilution_service.get_dilution_data', new_callable=AsyncMock) as mock_service:
            mock_service.return_value = {
                "offeringRisk": "Medium",
                "offeringAbility": "High",
                "dilutionRisk": "Low",
                "cashNeed": 12,
                "cashBurn": 1000000,
                "estimatedCash": 50000000,
                "float": 1000000000,
                "outstanding": 2000000000,
                "marketCap": 100000000000,
                "insiderOwnership": 0.15,
                "institutionalOwnership": 0.45
            }
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/dilution/AAPL")
                assert response.status_code == 200
                data = response.json()
                assert "offeringRisk" in data
                assert data["offeringRisk"] == "Medium"
    
    @pytest.mark.asyncio
    async def test_endpoint_bad_request_invalid_ticker(self):
        """Test endpoint with invalid ticker"""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/dilution/123456")
            assert response.status_code == 400
        
    @pytest.mark.asyncio
    async def test_endpoint_not_found(self):
        """Test endpoint with valid but non-existent ticker"""
        with patch('app.api.v1.routes.dilution_service.get_dilution_data', new_callable=AsyncMock) as mock_service:
            mock_service.side_effect = TickerNotFoundError("Ticker not found")
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/dilution/XXXX")
                assert response.status_code == 404
            
    @pytest.mark.asyncio
    async def test_endpoint_rate_limit(self):
        """Test endpoint when rate limited"""
        with patch('app.api.v1.routes.dilution_service.get_dilution_data', new_callable=AsyncMock) as mock_service:
            mock_service.side_effect = RateLimitError("Rate limit exceeded")
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/dilution/AAPL")
                assert response.status_code == 429
            
    @pytest.mark.asyncio
    async def test_endpoint_internal_error(self):
        """Test endpoint when internal server error occurs"""
        with patch('app.api.v1.routes.dilution_service.get_dilution_data', new_callable=AsyncMock) as mock_service:
            mock_service.side_effect = Exception("Internal server error")
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/v1/dilution/AAPL")
                assert response.status_code == 500
