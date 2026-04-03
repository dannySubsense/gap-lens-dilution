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

    async def _make_request_list(self, endpoint: str, params: Dict[str, Any]) -> list:
        """Make a request to the Ask-Edgar API and return list results."""
        for attempt in range(self.max_retries):
            try:
                response = await self.client.get(
                    f"{settings.askedgar_url}{endpoint}",
                    params=params
                )

                if response.status_code == 404:
                    return []
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
                return data.get("results", [])

            except httpx.RequestError as e:
                if attempt == self.max_retries - 1:
                    raise ExternalAPIError(f"Request error: {str(e)}")
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        raise ExternalAPIError("Max retries exceeded")

    async def get_news(self, ticker: str, limit: int = 10) -> list:
        """
        Fetch news and filings for a given ticker.

        Args:
            ticker (str): The stock ticker symbol
            limit (int): Maximum number of results to return

        Returns:
            list: News and filings data
        """
        params = {"ticker": ticker, "limit": limit}
        return await self._make_request_list("/v1/news", params)

    async def get_registrations(self, ticker: str) -> list:
        """
        Fetch registration data (shelf, ATM, equity line, S-1) for a given ticker.

        Args:
            ticker (str): The stock ticker symbol

        Returns:
            list: Registration data
        """
        params = {"ticker": ticker}
        return await self._make_request_list("/v1/registrations", params)

    async def get_dilution_detail(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch detailed dilution data (warrants and convertibles) for a given ticker.

        Args:
            ticker (str): The stock ticker symbol

        Returns:
            Dict[str, Any]: Detailed dilution data including warrants and convertibles
        """
        params = {"ticker": ticker}
        results = await self._make_request_list("/v1/dilution-data", params)

        # The API returns a list, we'll organize by type
        warrants = []
        convertibles = []

        for item in results:
            if item.get("warrants_amount") or item.get("warrants_remaining"):
                warrants.append(item)
            if item.get("convertible_debt_remaining") or item.get("offering_amount"):
                convertibles.append(item)

        return {
            "warrants": warrants,
            "convertibles": convertibles
        }

    async def get_dilution_data(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch comprehensive dilution data for a given ticker from all endpoints.

        Args:
            ticker (str): The stock ticker symbol

        Returns:
            Dict[str, Any]: Combined dilution data with camelCase keys

        Raises:
            TickerNotFoundError: If ticker is not found
            RateLimitError: If rate limit is exceeded
            ExternalAPIError: For other API errors
        """
        # Fetch all endpoints concurrently
        dilution_task = self._make_request("/v1/dilution-rating", ticker)
        float_task = self._make_request("/v1/float-outstanding", ticker)
        news_task = self.get_news(ticker, limit=10)
        registrations_task = self.get_registrations(ticker)
        dilution_detail_task = self.get_dilution_detail(ticker)

        dilution_data, float_data, news_data, registrations_data, dilution_detail_data = await asyncio.gather(
            dilution_task, float_task, news_task, registrations_task, dilution_detail_task
        )

        # Merge and map to camelCase
        result = {}

        # Map dilution-rating fields
        result["ticker"] = ticker.upper()
        result["offeringRisk"] = dilution_data.get("overall_offering_risk")
        result["offeringAbility"] = dilution_data.get("offering_ability")
        result["offeringAbilityDesc"] = dilution_data.get("offering_ability_desc")
        result["dilutionRisk"] = dilution_data.get("dilution")
        result["dilutionDesc"] = dilution_data.get("dilution_desc")
        result["offeringFrequency"] = dilution_data.get("offering_frequency")
        result["cashNeed"] = dilution_data.get("cash_need")
        result["cashNeedDesc"] = dilution_data.get("cash_need_desc")
        result["cashRunway"] = dilution_data.get("cash_remaining_months")
        result["cashBurn"] = dilution_data.get("cash_burn")
        result["estimatedCash"] = dilution_data.get("estimated_cash")
        result["warrantExercise"] = dilution_data.get("warrant_exercise")
        result["warrantExerciseDesc"] = dilution_data.get("warrant_exercise_desc")

        # Map float-outstanding fields
        result["float"] = float_data.get("float")
        result["outstanding"] = float_data.get("outstanding")
        result["marketCap"] = float_data.get("market_cap_final")
        result["industry"] = float_data.get("industry")
        result["sector"] = float_data.get("sector")
        result["country"] = float_data.get("country")
        result["insiderOwnership"] = float_data.get("insider_percent")
        result["institutionalOwnership"] = float_data.get("institutions_percent")

        # Add news data
        result["news"] = news_data

        # Add registrations data
        result["registrations"] = registrations_data

        # Add detailed dilution data
        result["warrants"] = dilution_detail_data.get("warrants", [])
        result["convertibles"] = dilution_detail_data.get("convertibles", [])

        return result

    async def close(self):
        """Close the HTTP client session."""
        await self.client.aclose()
