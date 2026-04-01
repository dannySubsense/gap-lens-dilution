import asyncio
import httpx
from typing import Dict, Any
from app.core.config import settings
from app.utils.errors import TickerNotFoundError, RateLimitError, ExternalAPIError


class DilutionService:
    """Service for interacting with Ask-Edgar API with retry logic."""

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=settings.request_timeout,
            headers={"API-KEY": settings.askedgar_api_key},
        )
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    async def _make_request(self, endpoint: str, ticker: str) -> Dict[str, Any]:
        """Make a request to the Ask-Edgar API with retry logic."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(
                    f"{settings.askedgar_url}{endpoint}?ticker={ticker}"
                )

                if response.status_code == 404:
                    raise TickerNotFoundError(f"Ticker '{ticker}' not found")
                elif response.status_code == 429:
                    if attempt == self.max_retries - 1:
                        raise RateLimitError("Rate limit exceeded")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                    continue
                elif response.status_code >= 400:
                    raise ExternalAPIError(
                        f"API request failed with status {response.status_code}"
                    )

                response.raise_for_status()
                data = response.json()
                return data.get("results", [{}])[0] if data.get("results") else {}

            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    raise ExternalAPIError(f"Request error: {str(e)}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise ExternalAPIError("Max retries exceeded")

    async def get_dilution_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch dilution data for a given ticker from both endpoints.

        Args:
            ticker (str): The stock ticker symbol

        Returns:
            Dict[str, Any]: Combined dilution data with camelCase keys

        Raises:
            TickerNotFoundError: If ticker is not found
            RateLimitError: If rate limit is exceeded
            ExternalAPIError: For other API errors
        """
        # Fetch both endpoints concurrently
        dilution_task = self._make_request("/v1/dilution-rating", ticker)
        float_task = self._make_request("/v1/float-outstanding", ticker)
        
        dilution_data, float_data = await asyncio.gather(dilution_task, float_task)
        
        # Merge and map to camelCase
        result = {}
        
        # Map dilution-rating fields
        result["offeringRisk"] = dilution_data.get("overall_offering_risk")
        result["offeringAbility"] = dilution_data.get("offering_ability")
        result["dilutionRisk"] = dilution_data.get("dilution")
        result["cashNeed"] = dilution_data.get("cash_remaining_months")
        result["cashRunway"] = dilution_data.get("cash_remaining_months")
        result["cashBurn"] = dilution_data.get("cash_burn")
        result["estimatedCash"] = dilution_data.get("estimated_cash")
        result["warrantExercise"] = dilution_data.get("warrant_exercise")
        result["warrantExerciseDesc"] = dilution_data.get("warrant_exercise_desc")
        
        # Map float-outstanding fields
        result["float"] = float_data.get("float")
        result["outstanding"] = float_data.get("outstanding")
        result["marketCap"] = float_data.get("market_cap_final")
        result["insiderOwnership"] = float_data.get("insider_percent")
        result["institutionalOwnership"] = float_data.get("institutions_percent")
        
        return result

    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()
