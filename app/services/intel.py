import asyncio
import time
from typing import Any

from app.core.config import settings
from app.services.dilution import DilutionService

CACHE_TTL_DEFAULT = 1800  # 30 min
CACHE_TTL_PD_LIST = 300   # 5 min


class IntelService:
    def __init__(self, dilution_service: DilutionService):
        self.client = dilution_service.client  # reuse shared httpx.AsyncClient
        self._cache: dict[str, tuple[float, Any]] = {}

    def _cache_get(self, key: str, ttl: int = CACHE_TTL_DEFAULT) -> Any | None:
        if key in self._cache:
            stored_at, value = self._cache[key]
            if time.time() - stored_at < ttl:
                return value
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        if value is not None:
            self._cache[key] = (time.time(), value)

    async def get_market_strength(self) -> dict | None:
        cache_key = "mkt_strength"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/market-strength",
                params={"latest": "true"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            results = data.get("results")
            result = results[0] if results else data
            self._cache_set(cache_key, result)
            return result
        except Exception:
            return None

    async def get_pump_and_dump(self, ticker: str) -> dict | None:
        upper = ticker.upper()
        cache_key = f"pd:{upper}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/pump-and-dump-tracker",
                params={"ticker": upper},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            results = data.get("results")
            result = results[0] if results else None
            self._cache_set(cache_key, result)
            return result
        except Exception:
            return None

    async def get_pump_and_dump_list(self) -> list:
        cache_key = "pd_list"
        cached = self._cache_get(cache_key, ttl=CACHE_TTL_PD_LIST)
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/pump-and-dump-tracker",
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except Exception:
            return []

    async def get_nasdaq_compliance(self, ticker: str) -> list:
        upper = ticker.upper()
        cache_key = f"compliance:{upper}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/nasdaq-compliance",
                params={"ticker": upper},
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except Exception:
            return []

    async def get_reverse_splits(self, ticker: str) -> list:
        upper = ticker.upper()
        cache_key = f"revsplit:{upper}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/reverse-splits",
                params={"ticker": upper},
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except Exception:
            return []

    async def get_filing_titles(self, ticker: str) -> list:
        upper = ticker.upper()
        cache_key = f"filingtitles:{upper}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/filing-titles",
                params={"ticker": upper},
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except Exception:
            return []

    async def get_historical_float(self, ticker: str) -> list:
        upper = ticker.upper()
        cache_key = f"histfloat:{upper}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/historical-float-pro",
                params={"ticker": upper},
            )
            if response.status_code == 404:
                return []
            response.raise_for_status()
            data = response.json()
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except Exception:
            return []

    async def get_research_report(self, ticker: str) -> dict | None:
        upper = ticker.upper()
        cache_key = f"report:{upper}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/research-reports-short",
                params={"ticker": upper},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            results = data.get("results")
            result = results[0] if results else None
            self._cache_set(cache_key, result)
            return result
        except Exception:
            return None

    async def get_batch_enrichment(self, tickers: list[str]) -> dict[str, dict]:
        semaphore = asyncio.Semaphore(20)

        async def fetch_ticker(ticker: str):
            async with semaphore:
                pd, compliance, splits = await asyncio.gather(
                    self.get_pump_and_dump(ticker),
                    self.get_nasdaq_compliance(ticker),
                    self.get_reverse_splits(ticker),
                    return_exceptions=True,
                )
                return ticker, pd, compliance, splits

        tasks = [fetch_ticker(t.upper()) for t in tickers]
        results_raw = await asyncio.gather(*tasks, return_exceptions=True)

        output: dict[str, dict] = {}
        for item in results_raw:
            if isinstance(item, Exception):
                continue
            ticker, pd, compliance, splits = item
            # Omit tickers where all three are exceptions
            if isinstance(pd, Exception) and isinstance(compliance, Exception) and isinstance(splits, Exception):
                continue
            output[ticker] = {
                "pumpdump": pd if not isinstance(pd, Exception) else None,
                "hasComplianceDeficiency": bool(compliance) if not isinstance(compliance, Exception) else False,
                "hasReverseSplits": bool(splits) if not isinstance(splits, Exception) else False,
            }

        return output
