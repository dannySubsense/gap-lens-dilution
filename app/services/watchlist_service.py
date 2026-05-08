"""
WatchlistService — FMP-first / AskEdgar-fallback quote enrichment for watchlist
tickers that may be absent from the gainer panels.

Architecture: see docs/specs/watchlist-quote-fallback/02-ARCHITECTURE.md

Cache strategy:
  - FMP-derived fields (price, todaysChangePerc, volume, marketCap, sector,
    country, float): in-process dict with 60-second TTL keyed by
    "wlq:fmp:{TICKER}".
  - AskEdgar-derived fields (risk, chartRating, newsToday): delegated to
    DilutionService cache (30-minute TTL); not duplicated here.

httpx client lifecycle: process-lifetime (matches GainersService._http pattern).
No shutdown hook is registered — this is the accepted pattern for this codebase.
"""

import asyncio
import time
from typing import Any

import httpx

from app.core.config import settings
from app.services.dilution import DilutionService


class WatchlistService:
    """Per-ticker quote enrichment for watchlist cards.

    Fans out FMP /quote, /profile, /shares_float concurrently and delegates
    risk/chartRating/newsToday to DilutionService (cached 30 min).
    Returns a WatchlistQuoteRecord dict with camelCase keys per ticker.
    """

    FMP_QUOTE_TTL: int = 60          # seconds
    WATCHLIST_BATCH_SEMAPHORE: int = 10
    ASKEDGAR_TTL: int = 1800         # documentation only — managed by DilutionService._cache

    def __init__(self, dilution_service: DilutionService) -> None:
        # The DilutionService singleton is also created at module-level in
        # routes.py; we reuse it for AskEdgar calls.
        self._dilution = dilution_service
        # Own httpx.AsyncClient for FMP only — DilutionService.client carries
        # the AskEdgar API-KEY header and must not be reused.
        self._http = httpx.AsyncClient(timeout=15, follow_redirects=True)
        self._fmp_cache: dict[str, tuple[float, Any]] = {}

    # ── FMP cache helpers ───────────────────────────────────────────────────

    def _fmp_cache_get(self, key: str) -> Any | None:
        """Return cached value if within TTL, else None."""
        if key in self._fmp_cache:
            stored_at, value = self._fmp_cache[key]
            if time.time() - stored_at < self.FMP_QUOTE_TTL:
                return value
        return None

    def _fmp_cache_set(self, key: str, value: Any) -> None:
        """Store value. Never store None (mirrors DilutionService._cache_set)."""
        if value is not None:
            self._fmp_cache[key] = (time.time(), value)

    # ── FMP sub-fetchers ────────────────────────────────────────────────────

    async def _fetch_fmp_quote(self, ticker: str) -> dict | None:
        """FMP /api/v3/quote — returns dict with price, changesPercentage, volume, marketCap.

        Returns None on any failure or unrecognised ticker.
        """
        api_key = settings.fmp_api_key
        if not api_key:
            return None
        try:
            resp = await self._http.get(
                f"https://financialmodelingprep.com/api/v3/quote/{ticker}",
                params={"apikey": api_key},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0]
        except Exception:
            pass
        return None

    async def _fetch_fmp_profile(self, ticker: str) -> dict | None:
        """FMP /api/v3/profile — returns dict with sector, country."""
        api_key = settings.fmp_api_key
        if not api_key:
            return None
        try:
            resp = await self._http.get(
                f"https://financialmodelingprep.com/api/v3/profile/{ticker}",
                params={"apikey": api_key},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0]
        except Exception:
            pass
        return None

    async def _fetch_fmp_float(self, ticker: str) -> float | None:
        """FMP /api/v4/shares_float — returns floatShares (treats 0 as None)."""
        api_key = settings.fmp_api_key
        if not api_key:
            return None
        try:
            resp = await self._http.get(
                "https://financialmodelingprep.com/api/v4/shares_float",
                params={"symbol": ticker, "apikey": api_key},
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            if isinstance(data, list) and data:
                float_shares = data[0].get("floatShares")
                # Edge case: float = 0 from FMP is data-quality noise → None
                if float_shares in (None, 0, 0.0):
                    return None
                return float_shares
        except Exception:
            pass
        return None

    # ── Per-ticker assembly ─────────────────────────────────────────────────

    async def _get_ticker_quote(self, ticker: str) -> dict[str, Any]:
        """Assemble full WatchlistQuoteRecord for a single ticker.

        Step 1 — FMP fields (cached per ticker for FMP_QUOTE_TTL seconds).
        Step 2 — AskEdgar fields (delegated to DilutionService; 30-min TTL).
        Both groups use asyncio.gather(return_exceptions=True) so partial
        failures degrade gracefully.
        """
        upper = ticker.upper()
        cache_key = f"wlq:fmp:{upper}"

        # ── Step 1: FMP fields ──
        cached_fmp = self._fmp_cache_get(cache_key)
        if cached_fmp is not None:
            fmp_fields = cached_fmp
        else:
            quote_data, profile_data, float_value = await asyncio.gather(
                self._fetch_fmp_quote(upper),
                self._fetch_fmp_profile(upper),
                self._fetch_fmp_float(upper),
                return_exceptions=True,
            )
            # Normalise exceptions to None
            if isinstance(quote_data, Exception):
                quote_data = None
            if isinstance(profile_data, Exception):
                profile_data = None
            if isinstance(float_value, Exception):
                float_value = None

            # Extract fields
            if isinstance(quote_data, dict):
                price = quote_data.get("price")
                change_perc = quote_data.get("changesPercentage")
                volume = quote_data.get("volume")
                market_cap = quote_data.get("marketCap")
            else:
                price = change_perc = volume = market_cap = None

            if isinstance(profile_data, dict):
                sector = profile_data.get("sector") or None
                country = profile_data.get("country") or None
            else:
                sector = country = None

            # Coerce volume to int when present
            if volume is not None:
                try:
                    volume = int(volume)
                except (TypeError, ValueError):
                    volume = None

            fmp_fields = {
                "price": price,
                "todaysChangePerc": change_perc,
                "volume": volume,
                "marketCap": market_cap,
                "sector": sector,
                "country": country,
                "float": float_value,
            }
            # Cache only when we got something useful (any non-null FMP field)
            if any(v is not None for v in fmp_fields.values()):
                self._fmp_cache_set(cache_key, fmp_fields)

        # ── Step 2: AskEdgar fields ──
        dilution_data, chart_data, news_today_result = await asyncio.gather(
            self._dilution._make_request_cached(
                "/enterprise/v1/dilution-rating", upper, f"dilution:{upper}"
            ),
            self._dilution.get_chart_analysis(upper),
            self._dilution.get_news_today_cached(upper),
            return_exceptions=True,
        )

        risk: Any = None
        if isinstance(dilution_data, dict):
            risk = dilution_data.get("overall_offering_risk")

        chart_rating: Any = None
        if isinstance(chart_data, dict):
            chart_rating = chart_data.get("rating")

        news_today = news_today_result if isinstance(news_today_result, bool) else False

        # ── Assemble record ──
        return {
            "ticker": upper,
            "price": fmp_fields["price"],
            "todaysChangePerc": fmp_fields["todaysChangePerc"],
            "volume": fmp_fields["volume"],
            "marketCap": fmp_fields["marketCap"],
            "float": fmp_fields["float"],
            "sector": fmp_fields["sector"],
            "country": fmp_fields["country"],
            "risk": risk,
            "chartRating": chart_rating,
            "newsToday": news_today,
        }

    # ── Public batch API ────────────────────────────────────────────────────

    async def get_batch(self, tickers: list[str]) -> dict[str, dict[str, Any]]:
        """Fan-out per-ticker enrichment under a Semaphore for bounded concurrency.

        Tickers that raise are omitted from the result dict — never raised.
        """
        if not tickers:
            return {}

        semaphore = asyncio.Semaphore(self.WATCHLIST_BATCH_SEMAPHORE)

        async def guarded(ticker: str) -> tuple[str, dict[str, Any] | None]:
            async with semaphore:
                try:
                    record = await self._get_ticker_quote(ticker)
                    return ticker.upper(), record
                except Exception:
                    return ticker.upper(), None

        results = await asyncio.gather(
            *[guarded(t) for t in tickers], return_exceptions=True
        )
        out: dict[str, dict[str, Any]] = {}
        for item in results:
            if isinstance(item, Exception):
                continue
            tkr, record = item
            if record is not None:
                out[tkr] = record
        return out
