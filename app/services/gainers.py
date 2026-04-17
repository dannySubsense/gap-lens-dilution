import asyncio
import re
import time
from datetime import datetime
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

    def __init__(self, dilution_service: DilutionService):
        self.dilution_service = dilution_service
        self._cache: dict[str, tuple[float, list]] = {}
        self._http = httpx.AsyncClient(timeout=15, follow_redirects=True)

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
        today = datetime.now().strftime("%Y-%m-%d")

        # 3 enrichment calls in parallel (news check is part of the news fetch)
        float_task = self.dilution_service._make_request_cached(
            "/enterprise/v1/float-outstanding", ticker, f"float:{ticker}"
        )
        dilution_task = self.dilution_service._make_request_cached(
            "/enterprise/v1/dilution-rating", ticker, f"dilution:{ticker}"
        )
        chart_task = self.dilution_service.get_chart_analysis(ticker)

        results = await asyncio.gather(float_task, dilution_task, chart_task, return_exceptions=True)

        float_data = results[0] if not isinstance(results[0], Exception) else None
        dilution_data = results[1] if not isinstance(results[1], Exception) else None
        chart_data = results[2] if not isinstance(results[2], Exception) else None

        # Build enriched entry
        entry = {
            "ticker": ticker,
            "todaysChangePerc": item.get("todaysChangePerc", 0),
            "price": item.get("price"),
            "volume": item.get("volume"),
            "float": float_data.get("float") if float_data else None,
            "marketCap": float_data.get("market_cap_final") if float_data else None,
            "sector": float_data.get("sector") if float_data else None,
            "country": float_data.get("country") if float_data else None,
            "risk": dilution_data.get("overall_offering_risk") if dilution_data else None,
            "chartRating": chart_data.get("rating") if chart_data else None,
            "newsToday": False,
        }

        # Check for news today (use the news endpoint directly, it's not cached)
        try:
            news = await self.dilution_service.get_news(ticker, limit=10)
            for n in news:
                ft = n.get("form_type")
                if ft in ("news", "8-K", "6-K"):
                    d = (n.get("created_at") or n.get("filed_at", ""))[:10]
                    if d == today:
                        entry["newsToday"] = True
                        break
        except Exception:
            pass

        return entry

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
