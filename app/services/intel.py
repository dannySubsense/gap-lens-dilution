import asyncio
import logging
import time
import httpx
from typing import TYPE_CHECKING, Any, Optional

from app.core.config import settings
from app.services.dilution import DilutionService

if TYPE_CHECKING:
    from app.services.usage_capture_service import UsageCaptureService

logger = logging.getLogger(__name__)

TTL_24H: int = 86400
TTL_30M: int = 1800
TTL_BACKOFF: int = 300  # 5-minute backoff for timeout/network-error sentinel entries

CACHE_TTL_MAP: dict[str, int] = {
    "mkt_strength":  TTL_24H,
    "pd":            TTL_30M,
    "compliance":    TTL_24H,
    "revsplit":      TTL_24H,
    "filingtitles":  TTL_24H,
    "histfloat":     TTL_24H,
    "report":        TTL_24H,
}

CACHE_TTL_PD_LIST = 300  # 5 min — explicit override for pump-and-dump list (more aggressive)

# Sentinel for confirmed-empty AskEdgar responses. Must not be imported or referenced outside this module.
_CACHE_EMPTY = object()


class IntelService:
    def __init__(
        self,
        dilution_service: DilutionService,
        market_strength_service=None,
        usage_capture_service: Optional["UsageCaptureService"] = None,
    ) -> None:
        self.client = dilution_service.client  # reuse shared httpx.AsyncClient
        self._market_strength_service = market_strength_service
        self._cache: dict[str, tuple[float, Any, int | None]] = {}
        self._usage_capture = usage_capture_service

    def _cache_get(self, key: str, ttl: int | None = None) -> Any | None:
        """Return cached value within TTL.

        Returns _CACHE_EMPTY sentinel if an empty response was previously cached.
        Returns None on miss or expiry.
        Callers within this module must check `is _CACHE_EMPTY` before returning to routes.

        TTL priority:
        1. Stored 3-tuple override (backoff sentinel written by timeout handler).
        2. Caller-supplied ttl argument (preserves get_pump_and_dump_list's ttl=CACHE_TTL_PD_LIST path).
        3. CACHE_TTL_MAP prefix lookup, falling back to TTL_24H.
        """
        if key not in self._cache:
            return None
        entry = self._cache[key]
        stored_at, value = entry[0], entry[1]
        ttl_entry_override = entry[2] if len(entry) > 2 else None
        if ttl_entry_override is not None:
            effective_ttl = ttl_entry_override
        elif ttl is not None:
            effective_ttl = ttl
        else:
            prefix = key.split(":")[0]
            effective_ttl = CACHE_TTL_MAP.get(prefix, TTL_24H)
        if time.time() - stored_at < effective_ttl:
            return value
        del self._cache[key]
        return None

    def _cache_set(self, key: str, value: Any, ttl_override: int | None = None) -> None:
        """Cache a value. Stores _CACHE_EMPTY sentinel in place of None.
        When ttl_override is provided, it is stored as the third tuple element and takes
        priority over all other TTL resolution in _cache_get (used for backoff sentinels)."""
        stored = _CACHE_EMPTY if value is None else value
        self._cache[key] = (time.time(), stored, ttl_override)

    async def get_market_strength(self) -> dict | None:
        cache_key = "mkt_strength"
        cached = self._cache_get(cache_key)
        if cached is _CACHE_EMPTY:
            return None
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
            if self._usage_capture is not None:
                usage = data.get("usage")
                if usage:
                    self._usage_capture.capture("/v1/market-strength", None, usage)
                else:
                    logger.warning(
                        "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                        "/v1/market-strength", None,
                    )
            results = data.get("results")
            result = results[0] if results else data
            self._cache_set(cache_key, result)
            return result
        except (asyncio.TimeoutError, httpx.RequestError):
            self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
            if self._market_strength_service is not None:
                fallback = self._market_strength_service.get_latest_snapshot()
                if fallback is not None:
                    return fallback.__dict__
            return None
        except Exception:
            return None

    async def get_pump_and_dump(self, ticker: str) -> dict | None:
        upper = ticker.upper()
        cache_key = f"pd:{upper}"
        cached = self._cache_get(cache_key)
        if cached is _CACHE_EMPTY:
            return None
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
            if self._usage_capture is not None:
                usage = data.get("usage")
                if usage:
                    self._usage_capture.capture("/v1/pump-and-dump-tracker", upper, usage)
                else:
                    logger.warning(
                        "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                        "/v1/pump-and-dump-tracker", upper,
                    )
            results = data.get("results")
            result = results[0] if results else None
            self._cache_set(cache_key, result)
            return result
        except (asyncio.TimeoutError, httpx.RequestError):
            self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
            return None
        except Exception:
            return None

    async def get_pump_and_dump_list(self) -> list:
        cache_key = "pd_list"
        cached = self._cache_get(cache_key, ttl=CACHE_TTL_PD_LIST)
        if cached is _CACHE_EMPTY:
            return []
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
            if self._usage_capture is not None:
                usage = data.get("usage")
                if usage:
                    self._usage_capture.capture("/v1/pump-and-dump-tracker", None, usage)
                else:
                    logger.warning(
                        "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                        "/v1/pump-and-dump-tracker", None,
                    )
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except (asyncio.TimeoutError, httpx.RequestError):
            self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
            return []
        except Exception:
            return []

    async def get_nasdaq_compliance(self, ticker: str) -> list:
        upper = ticker.upper()
        cache_key = f"compliance:{upper}"
        cached = self._cache_get(cache_key)
        if cached is _CACHE_EMPTY:
            return []
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
            if self._usage_capture is not None:
                usage = data.get("usage")
                if usage:
                    self._usage_capture.capture("/v1/nasdaq-compliance", upper, usage)
                else:
                    logger.warning(
                        "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                        "/v1/nasdaq-compliance", upper,
                    )
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except (asyncio.TimeoutError, httpx.RequestError):
            self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
            return []
        except Exception:
            return []

    async def get_reverse_splits(self, ticker: str) -> list:
        upper = ticker.upper()
        cache_key = f"revsplit:{upper}"
        cached = self._cache_get(cache_key)
        if cached is _CACHE_EMPTY:
            return []
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
            if self._usage_capture is not None:
                usage = data.get("usage")
                if usage:
                    self._usage_capture.capture("/v1/reverse-splits", upper, usage)
                else:
                    logger.warning(
                        "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                        "/v1/reverse-splits", upper,
                    )
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except (asyncio.TimeoutError, httpx.RequestError):
            self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
            return []
        except Exception:
            return []

    async def get_filing_titles(self, ticker: str) -> list:
        upper = ticker.upper()
        cache_key = f"filingtitles:{upper}"
        cached = self._cache_get(cache_key)
        if cached is _CACHE_EMPTY:
            return []
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
            if self._usage_capture is not None:
                usage = data.get("usage")
                if usage:
                    self._usage_capture.capture("/v1/filing-titles", upper, usage)
                else:
                    logger.warning(
                        "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                        "/v1/filing-titles", upper,
                    )
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except (asyncio.TimeoutError, httpx.RequestError):
            self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
            return []
        except Exception:
            return []

    async def get_historical_float(self, ticker: str) -> list:
        upper = ticker.upper()
        cache_key = f"histfloat:{upper}"
        cached = self._cache_get(cache_key)
        if cached is _CACHE_EMPTY:
            return []
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
            if self._usage_capture is not None:
                usage = data.get("usage")
                if usage:
                    self._usage_capture.capture("/v1/historical-float-pro", upper, usage)
                else:
                    logger.warning(
                        "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                        "/v1/historical-float-pro", upper,
                    )
            result = data.get("results", [])
            self._cache_set(cache_key, result)
            return result
        except (asyncio.TimeoutError, httpx.RequestError):
            self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
            return []
        except Exception:
            return []

    async def get_research_report(self, ticker: str) -> dict | None:
        upper = ticker.upper()
        cache_key = f"report:{upper}"
        cached = self._cache_get(cache_key)
        if cached is _CACHE_EMPTY:
            return None
        if cached is not None:
            return cached
        try:
            response = await self.client.get(
                f"{settings.askedgar_url}/v1/research-reports",
                params={"ticker": upper},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            if self._usage_capture is not None:
                usage = data.get("usage")
                if usage:
                    self._usage_capture.capture("/v1/research-reports", upper, usage)
                else:
                    logger.warning(
                        "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                        "/v1/research-reports", upper,
                    )
            results = data.get("results")
            result = results[0] if results else None
            self._cache_set(cache_key, result)
            return result
        except (asyncio.TimeoutError, httpx.RequestError):
            self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
            return None
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
