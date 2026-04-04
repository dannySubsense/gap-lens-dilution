import asyncio
import re
import time
from datetime import datetime
import httpx
from app.services.dilution import DilutionService


class GainersService:
    TRADINGVIEW_URL = "https://scanner.tradingview.com/america/scan"
    MIN_CHANGE_PCT = 15.0
    TICKER_RE = re.compile(r'^[A-Z]{2,4}$')
    CACHE_TTL_SECS = 60

    def __init__(self, dilution_service: DilutionService):
        self.dilution_service = dilution_service
        self._cache: dict[str, tuple[float, list]] = {}
        self._http = httpx.AsyncClient(timeout=15)

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
