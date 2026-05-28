import asyncio
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Annotated, Any, Optional
import httpx
from fastapi import Query
from app.services.dilution import DilutionService
from app.core.config import settings


@dataclass
class GainerFilterParams:
    price_min: float = 1.0
    price_max: float = 20.0
    volume_min: int = 1_000_000
    change_pct_min: float = 15.0
    mcap_max: Optional[float] = None   # None means no ceiling (frontend owns the 500M default)
    float_max: Optional[float] = None  # None means no ceiling (frontend owns the 50M default)
    sector_exclude: list[str] = field(default_factory=list)
    country_exclude: list[str] = field(default_factory=list)
    watchlist: frozenset[str] = field(default_factory=frozenset)


def gainer_filter_params(
    price_min: float = Query(default=1.0),
    price_max: float = Query(default=20.0),
    volume_min: int = Query(default=1_000_000),
    change_pct_min: float = Query(default=15.0),
    mcap_max: Optional[float] = Query(default=None),
    float_max: Optional[float] = Query(default=None),
    sector_exclude: list[str] = Query(default=[]),
    country_exclude: list[str] = Query(default=[]),
    watchlist: str = Query(default=""),
) -> GainerFilterParams:
    return GainerFilterParams(
        price_min=price_min,
        price_max=price_max,
        volume_min=volume_min,
        change_pct_min=change_pct_min,
        mcap_max=mcap_max,
        float_max=float_max,
        sector_exclude=[s.lower() for s in sector_exclude],
        country_exclude=[c.lower() for c in country_exclude],
        watchlist=frozenset(t.strip().upper() for t in watchlist.split(",") if t.strip()),
    )


class GainersService:
    TRADINGVIEW_URL = "https://scanner.tradingview.com/america/scan"
    MASSIVE_GAINERS_URL = "https://api.massive.com/v2/snapshot/locale/us/markets/stocks/gainers"
    MASSIVE_TICKER_URL = "https://api.massive.com/v3/reference/tickers"
    TICKER_RE = re.compile(r'^[A-Z]{2,4}$')
    CACHE_TTL_SECS = 60
    FMP_ENRICH_TTL: int = 300  # 5-minute TTL for gainer FMP enrichment cache

    def __init__(self, dilution_service: DilutionService):
        self.dilution_service = dilution_service
        self._cache: dict[str, tuple[float, list]] = {}
        self._fmp_enrich_cache: dict[str, tuple[float, Any]] = {}
        self._http = httpx.AsyncClient(timeout=15, follow_redirects=True)

    def _fmp_enrich_cache_get(self, key: str) -> Any | None:
        """Return cached FMP enrichment value if within TTL, else None."""
        if key in self._fmp_enrich_cache:
            stored_at, value = self._fmp_enrich_cache[key]
            if time.time() - stored_at < self.FMP_ENRICH_TTL:
                return value
        return None

    def _fmp_enrich_cache_set(self, key: str, value: Any) -> None:
        """Store FMP enrichment value. Never store None or an all-None dict."""
        if value is None:
            return
        if isinstance(value, dict) and all(v is None for v in value.values()):
            return
        self._fmp_enrich_cache[key] = (time.time(), value)

    def _filter_cache_key(self, fp: GainerFilterParams) -> str:
        """Stable ASCII string derived from all filter fields.

        Uses sorted representation to ensure field-order independence.
        Excludes watchlist (watchlist changes should not bust gainer cache —
        the exemption logic is applied at enrichment time from the live
        frozenset in fp.watchlist, not from cached data).
        """
        parts = [
            f"pmin={fp.price_min}",
            f"pmax={fp.price_max}",
            f"vmin={fp.volume_min}",
            f"cmin={fp.change_pct_min}",
            f"mmax={fp.mcap_max}",
            f"fmax={fp.float_max}",
            f"sex={','.join(sorted(fp.sector_exclude))}",
            f"cex={','.join(sorted(fp.country_exclude))}",
        ]
        return "|".join(parts)

    def _apply_stage0_filter(self, item: dict, fp: GainerFilterParams) -> bool:
        """Return True if item passes price, volume, change_pct criteria.

        Watchlist tickers always pass (exemption).
        """
        ticker = item.get("ticker", "").upper()
        if ticker in fp.watchlist:
            return True
        price = item.get("price") or 0
        volume = item.get("volume") or 0
        change_pct = item.get("todaysChangePerc") or 0
        if not (fp.price_min <= price <= fp.price_max):
            return False
        if volume < fp.volume_min:
            return False
        if change_pct < fp.change_pct_min:
            return False
        return True

    def _apply_stage1_filter(
        self, fmp_fields: dict, fp: GainerFilterParams, ticker: str
    ) -> bool:
        """Return True if FMP-derived fields pass mcap, float, sector, country criteria.

        Null/zero values pass through (no data = do not exclude).
        Watchlist tickers always pass (exemption).
        """
        if ticker.upper() in fp.watchlist:
            return True
        mcap = fmp_fields.get("marketCap")
        if mcap is not None and fp.mcap_max is not None:
            if mcap > fp.mcap_max:
                return False
        float_val = fmp_fields.get("float")
        if float_val is not None and float_val > 0 and fp.float_max is not None:
            if float_val > fp.float_max:
                return False
        sector = fmp_fields.get("sector")
        if sector is not None and fp.sector_exclude:
            if sector.lower() in fp.sector_exclude:
                return False
        country = fmp_fields.get("country")
        if country is not None and fp.country_exclude:
            if country.lower() in fp.country_exclude:
                return False
        return True

    async def _fetch_fmp_float_for_gainer(self, ticker: str) -> float | None:
        """FMP /api/v4/shares_float — returns floatShares (treats 0 as None).

        Mirrors WatchlistService._fetch_fmp_float exactly.
        Returns None on any failure (non-200, empty list, 0 value, exception).
        No retry on 429.
        """
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
                if float_shares in (None, 0, 0.0):
                    return None
                return float_shares
        except Exception:
            pass
        return None

    async def _fetch_fmp_profile_for_gainer(self, ticker: str) -> dict | None:
        """FMP /api/v3/profile — returns sector, country, mktCap.

        Mirrors WatchlistService._fetch_fmp_profile exactly.
        Returns None on any failure (non-200, empty list, exception). No retry on 429.
        NOTE: market cap field is 'mktCap' in FMP profile response (not 'marketCap').
        """
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

    async def get_gainers(self, fp: GainerFilterParams) -> list:
        # Check cache
        cache_key = "gainers:" + self._filter_cache_key(fp)
        if cache_key in self._cache:
            stored_at, data = self._cache[cache_key]
            if time.time() - stored_at < self.CACHE_TTL_SECS:
                return data

        try:
            raw = await self._fetch_from_tradingview()
            # Stage 0: filter before enrichment fan-out
            filtered = [item for item in raw[:30] if self._apply_stage0_filter(item, fp)]
            # Enrich in parallel
            tasks = [self._enrich_gainer(item, fp) for item in filtered]
            enriched = await asyncio.gather(*tasks, return_exceptions=True)
            result = [r for r in enriched if r is not None and not isinstance(r, Exception)]
            # Sort by change % descending
            result.sort(key=lambda x: x.get("todaysChangePerc", 0), reverse=True)
            self._cache[cache_key] = (time.time(), result)
            return result
        except Exception:
            return []

    async def _fetch_from_tradingview(self) -> list:
        try:
            resp = await self._http.post(
                self.TRADINGVIEW_URL,
                json={
                    "markets": ["america"],
                    "symbols": {"query": {"types": ["stock"]}, "tickers": []},
                    "options": {"lang": "en"},
                    "columns": ["name", "close", "premarket_change", "premarket_change_abs",
                                "premarket_close", "premarket_volume", "volume", "market_cap_basic"],
                    "sort": {"sortBy": "premarket_change", "sortOrder": "desc"},
                    "range": [0, 30],
                },
            )
            data = resp.json()
        except Exception:
            return []

        tickers = []
        for row in data.get("data", []):
            d = row.get("d", [])
            if len(d) < 8:
                continue
            ticker = d[0]
            if not self.TICKER_RE.match(ticker):
                continue
            pct = d[2] or 0
            tickers.append({
                "ticker": ticker,
                "todaysChangePerc": pct,
                "price": d[4] or d[1] or 0,
                "volume": int(d[5] or d[6] or 0),
            })
        return tickers

    async def _enrich_gainer(self, item: dict, fp: GainerFilterParams) -> dict | None:
        ticker = item["ticker"]
        upper = ticker.upper()

        # Step 1: FMP enrichment (float + profile) — check cache first
        cached_fmp = self._fmp_enrich_cache_get(f"fmpenrich:{upper}")
        if cached_fmp is None:
            float_result, profile_result = await asyncio.gather(
                self._fetch_fmp_float_for_gainer(upper),
                self._fetch_fmp_profile_for_gainer(upper),
                return_exceptions=True,
            )
            fmp_float = float_result if not isinstance(float_result, Exception) else None
            fmp_profile = profile_result if not isinstance(profile_result, Exception) else None
            fmp_fields = {
                "float": fmp_float,
                "marketCap": fmp_profile.get("mktCap") if fmp_profile else None,
                "sector": fmp_profile.get("sector") if fmp_profile else None,
                "country": fmp_profile.get("country") if fmp_profile else None,
            }
            self._fmp_enrich_cache_set(f"fmpenrich:{upper}", fmp_fields)
        else:
            fmp_fields = cached_fmp

        # Stage 1: FMP-derived filter — short-circuit before AskEdgar calls
        if not self._apply_stage1_filter(fmp_fields, fp, upper):
            if upper not in fp.watchlist:
                return None

        # Step 2: AskEdgar enrichment (dilution-rating + ai-chart-analysis) — concurrent
        dilution_task = self.dilution_service._make_request_cached(
            "/v1/dilution-rating", upper, f"dilution:{upper}"
        )
        chart_task = self.dilution_service.get_chart_analysis(upper)
        dilution_result, chart_result = await asyncio.gather(
            dilution_task, chart_task, return_exceptions=True
        )
        dilution_data = dilution_result if not isinstance(dilution_result, Exception) else None
        chart_data = chart_result if not isinstance(chart_result, Exception) else None

        # Step 3: newsToday — delegate to DilutionService two-tier cache
        try:
            news_today = await self.dilution_service.get_news_today_cached(upper)
        except Exception:
            news_today = False

        return {
            "ticker": upper,
            "todaysChangePerc": item.get("todaysChangePerc", 0),
            "price": item.get("price"),
            "volume": item.get("volume"),
            "float": fmp_fields.get("float"),
            "marketCap": fmp_fields.get("marketCap"),
            "sector": fmp_fields.get("sector"),
            "country": fmp_fields.get("country"),
            "risk": dilution_data.get("overall_offering_risk") if dilution_data else None,
            "chartRating": chart_data.get("rating") if chart_data else None,
            "newsToday": news_today,
        }

    # ── Massive / Polygon API ─────────────────────────────────────────────

    async def get_massive_gainers(self, fp: GainerFilterParams) -> list:
        """Fetch top gainers from Massive (Polygon) API, filtered to CS type."""
        cache_key = "massive_gainers:" + self._filter_cache_key(fp)
        if cache_key in self._cache:
            stored_at, data = self._cache[cache_key]
            if time.time() - stored_at < self.CACHE_TTL_SECS:
                return data

        api_key = settings.massive_api_key
        if not api_key:
            return []

        try:
            raw = await self._fetch_from_massive(api_key)
            # Filter to CS (common stock), then apply Stage 0
            cs_filtered = await self._filter_cs_tickers(raw[:30], api_key)
            stage0_filtered = [item for item in cs_filtered if self._apply_stage0_filter(item, fp)]
            tasks = [self._enrich_gainer(item, fp) for item in stage0_filtered]
            enriched = await asyncio.gather(*tasks, return_exceptions=True)
            result = [r for r in enriched if r is not None and not isinstance(r, Exception)]
            result.sort(key=lambda x: x.get("todaysChangePerc", 0), reverse=True)
            self._cache[cache_key] = (time.time(), result)
            return result
        except Exception:
            return []

    async def _fetch_from_massive(self, api_key: str) -> list:
        """Fetch raw gainers from Massive API."""
        try:
            resp = await self._http.get(
                self.MASSIVE_GAINERS_URL,
                params={"apiKey": api_key},
            )
            data = resp.json()
        except Exception:
            return []

        tickers = []
        for t in data.get("tickers", []):
            ticker = t.get("ticker", "")
            if not self.TICKER_RE.match(ticker):
                continue
            pct = t.get("todaysChangePerc", 0) or 0
            day = t.get("day", {}) or {}
            min_bar = t.get("min", {}) or {}
            prev_day = t.get("prevDay", {}) or {}

            # Price: min.c (nonzero) -> day.c (nonzero) -> prevDay.c -> 0
            min_c = min_bar.get("c")
            day_c = day.get("c")
            prev_c = prev_day.get("c")

            if min_c is not None and min_c != 0:
                price_val = min_c
            elif day_c is not None and day_c != 0:
                price_val = day_c
            elif prev_c is not None:
                price_val = prev_c
            else:
                price_val = 0

            # Volume: day.v (nonzero) -> min.v -> prevDay.v -> 0
            day_v = day.get("v")
            min_v = min_bar.get("v")
            prev_v = prev_day.get("v")

            if day_v is not None and day_v != 0:
                volume_val = int(day_v)
            elif min_v is not None:
                volume_val = int(min_v)
            elif prev_v is not None:
                volume_val = int(prev_v)
            else:
                volume_val = 0

            tickers.append({
                "ticker": ticker,
                "todaysChangePerc": pct,
                "price": price_val,
                "volume": volume_val,
            })
        return tickers

    # ── FMP (Financial Modeling Prep) API ────────────────────────────────

    FMP_GAINERS_URL = "https://financialmodelingprep.com/stable/biggest-gainers"

    async def get_fmp_gainers(self, fp: GainerFilterParams) -> list:
        """Fetch top gainers from FMP API."""
        cache_key = "fmp_gainers:" + self._filter_cache_key(fp)
        if cache_key in self._cache:
            stored_at, data = self._cache[cache_key]
            if time.time() - stored_at < self.CACHE_TTL_SECS:
                return data

        api_key = settings.fmp_api_key
        if not api_key:
            return []

        try:
            raw = await self._fetch_from_fmp(api_key)
            # Stage 0: filter after _fetch_from_fmp returns (volume already enriched)
            stage0_filtered = [item for item in raw[:30] if self._apply_stage0_filter(item, fp)]
            tasks = [self._enrich_gainer(item, fp) for item in stage0_filtered]
            enriched = await asyncio.gather(*tasks, return_exceptions=True)
            result = [r for r in enriched if r is not None and not isinstance(r, Exception)]
            result.sort(key=lambda x: x.get("todaysChangePerc", 0), reverse=True)
            self._cache[cache_key] = (time.time(), result)
            return result
        except Exception:
            return []

    async def _fetch_from_fmp(self, api_key: str) -> list:
        """Fetch raw gainers from FMP stable endpoint."""
        try:
            resp = await self._http.get(
                self.FMP_GAINERS_URL,
                params={"apikey": api_key},
            )
            data = resp.json()
        except Exception:
            return []

        tickers = []
        for item in data if isinstance(data, list) else []:
            ticker = item.get("symbol", "")
            if not self.TICKER_RE.match(ticker):
                continue
            pct = item.get("changesPercentage", 0) or 0
            tickers.append({
                "ticker": ticker,
                "todaysChangePerc": pct,
                "price": item.get("price", 0),
                "volume": int(item.get("volume", 0) or 0),
            })

        # Enrich with real-time price and volume from 1-minute intraday bars
        symbols = [t["ticker"] for t in tickers]
        rt_prices = await self._fetch_fmp_realtime_prices(symbols, api_key)

        result = []
        for t in tickers:
            sym = t["ticker"]
            rt = rt_prices.get(sym, {})
            price_val = rt.get("price") if rt.get("price") is not None else t.get("price", 0)
            vol_raw = rt.get("volume")
            volume_val = int(vol_raw) if vol_raw is not None else 0
            result.append({
                "ticker": sym,
                "todaysChangePerc": t["todaysChangePerc"],
                "price": price_val,
                "volume": volume_val,
            })
        return result

    async def _fetch_fmp_realtime_prices(
        self,
        symbols: list[str],
        api_key: str,
    ) -> dict[str, dict[str, float | None]]:
        """
        Fetch the most recent 1-minute bar for each symbol from FMP,
        including extended-hours data.
        Returns dict[symbol -> {"price": float|None, "volume": float|None}].
        Uses self._http (shared client). All requests are concurrent.
        Non-200 responses (including 429) are treated as failures — no retry.
        """
        async def fetch_one(symbol: str) -> tuple[str, dict]:
            try:
                resp = await self._http.get(
                    f"https://financialmodelingprep.com/api/v3/historical-chart/1min/{symbol}",
                    params={"apikey": api_key, "extended": "true", "limit": "1"},
                )
                # Per §11.6: treat non-200 (including 429) as failure, do NOT parse JSON
                if resp.status_code != 200:
                    return symbol, {}
                bars = resp.json()
                if isinstance(bars, list) and bars:
                    bar = bars[0]
                    return symbol, {"price": bar.get("close"), "volume": bar.get("volume")}
            except Exception:
                pass
            return symbol, {}

        results = await asyncio.gather(*[fetch_one(s) for s in symbols], return_exceptions=True)
        return {
            sym: data
            for item in results
            if not isinstance(item, Exception)
            for sym, data in [item]
            if data
        }

    async def _filter_cs_tickers(self, items: list, api_key: str) -> list:
        """Filter to common stock (CS) type using Massive ticker reference API."""
        async def check_cs(item: dict) -> dict | None:
            ticker = item["ticker"]
            try:
                resp = await self._http.get(
                    f"{self.MASSIVE_TICKER_URL}/{ticker}",
                    params={"apiKey": api_key},
                )
                data = resp.json()
                if data.get("results", {}).get("type") == "CS":
                    return item
            except Exception:
                pass
            return None

        results = await asyncio.gather(*[check_cs(i) for i in items], return_exceptions=True)
        return [r for r in results if r is not None and not isinstance(r, Exception)]
