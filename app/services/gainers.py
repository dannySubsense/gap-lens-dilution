import asyncio
import re
import time
from datetime import datetime
from typing import Any
import httpx
from app.services.dilution import DilutionService
from app.core.config import settings


class GainersService:
    TRADINGVIEW_URL = "https://scanner.tradingview.com/america/scan"
    MASSIVE_GAINERS_URL = "https://api.massive.com/v2/snapshot/locale/us/markets/stocks/gainers"
    MASSIVE_TICKER_URL = "https://api.massive.com/v3/reference/tickers"
    MIN_CHANGE_PCT = 15.0
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
        """Store FMP enrichment value. Never store None."""
        if value is not None:
            self._fmp_enrich_cache[key] = (time.time(), value)

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

    async def get_gainers(self) -> list:
        # Check cache
        if "gainers" in self._cache:
            stored_at, data = self._cache["gainers"]
            if time.time() - stored_at < self.CACHE_TTL_SECS:
                return data

        try:
            raw = await self._fetch_from_tradingview()
            # Enrich in parallel
            tasks = [self._enrich_gainer(item) for item in raw[:30]]
            enriched = await asyncio.gather(*tasks, return_exceptions=True)
            result = [r for r in enriched if not isinstance(r, Exception)]
            # Sort by change % descending
            result.sort(key=lambda x: x.get("todaysChangePerc", 0), reverse=True)
            self._cache["gainers"] = (time.time(), result)
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
            if pct < self.MIN_CHANGE_PCT:
                continue
            tickers.append({
                "ticker": ticker,
                "todaysChangePerc": pct,
                "price": d[4] or d[1] or 0,
                "volume": int(d[5] or d[6] or 0),
            })
        return tickers

    async def _enrich_gainer(self, item: dict) -> dict:
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

        # Step 2: AskEdgar enrichment (dilution-rating + ai-chart-analysis) — concurrent
        dilution_task = self.dilution_service._make_request_cached(
            "/enterprise/v1/dilution-rating", upper, f"dilution:{upper}"
        )
        chart_task = self.dilution_service.get_chart_analysis(upper)
        dilution_result, chart_result = await asyncio.gather(
            dilution_task, chart_task, return_exceptions=True
        )
        dilution_data = dilution_result if not isinstance(dilution_result, Exception) else None
        chart_data = chart_result if not isinstance(chart_result, Exception) else None

        # Step 3: newsToday — check two-tier cache first, then fetch on miss
        cached_news_today = self.dilution_service._cache_get(f"newsToday:{upper}")
        if isinstance(cached_news_today, bool):
            news_today = cached_news_today
        else:
            try:
                from zoneinfo import ZoneInfo
                ET = ZoneInfo("America/New_York")
                from datetime import datetime as dt
                today_et = dt.now(ET).strftime("%Y-%m-%d")
                news = await self.dilution_service.get_news(upper, limit=10)
                news_today = any(
                    n.get("form_type") in ("news", "8-K", "6-K")
                    and (n.get("created_at") or n.get("filed_at", ""))[:10] == today_et
                    for n in news
                )
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

    async def get_massive_gainers(self) -> list:
        """Fetch top gainers from Massive (Polygon) API, filtered to CS type."""
        if "massive_gainers" in self._cache:
            stored_at, data = self._cache["massive_gainers"]
            if time.time() - stored_at < self.CACHE_TTL_SECS:
                return data

        api_key = settings.massive_api_key
        if not api_key:
            return []

        try:
            raw = await self._fetch_from_massive(api_key)
            # Filter to CS (common stock) and enrich in parallel
            cs_filtered = await self._filter_cs_tickers(raw[:30], api_key)
            tasks = [self._enrich_gainer(item) for item in cs_filtered]
            enriched = await asyncio.gather(*tasks, return_exceptions=True)
            result = [r for r in enriched if not isinstance(r, Exception)]
            result.sort(key=lambda x: x.get("todaysChangePerc", 0), reverse=True)
            self._cache["massive_gainers"] = (time.time(), result)
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

    async def get_fmp_gainers(self) -> list:
        """Fetch top gainers from FMP API."""
        if "fmp_gainers" in self._cache:
            stored_at, data = self._cache["fmp_gainers"]
            if time.time() - stored_at < self.CACHE_TTL_SECS:
                return data

        api_key = settings.fmp_api_key
        if not api_key:
            return []

        try:
            raw = await self._fetch_from_fmp(api_key)
            tasks = [self._enrich_gainer(item) for item in raw[:30]]
            enriched = await asyncio.gather(*tasks, return_exceptions=True)
            result = [r for r in enriched if not isinstance(r, Exception)]
            result.sort(key=lambda x: x.get("todaysChangePerc", 0), reverse=True)
            self._cache["fmp_gainers"] = (time.time(), result)
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
            if pct < self.MIN_CHANGE_PCT:
                continue
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
