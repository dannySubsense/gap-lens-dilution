import asyncio
import hashlib
import time
import xml.etree.ElementTree as _ET
from datetime import datetime
from urllib.parse import urlparse, urlencode, parse_qs
from zoneinfo import ZoneInfo
from typing import Any

import httpx

from app.core.config import settings

# US/Eastern timezone — used for all newsToday date comparisons per requirements
ET = ZoneInfo("America/New_York")

# TTL constants (mirroring DilutionService TTL map values)
TTL_24H: int = 86400
TTL_30M: int = 1800

# SEC EDGAR concurrency limit — rate compliance decision, not a performance one.
# EDGAR's stated rate limit is 10 req/sec per IP. asyncio.Semaphore(10) enforces
# 10 *concurrent* coroutines, not 10 req/sec — under fast response times, concurrent=10
# can fire well over 10 req/sec in a burst.
# Correct enforcement: Semaphore(3) is intentionally conservative.
# At 300ms average EDGAR response time: 3 concurrent = ~10 req/sec max.
# At 600ms average: ~5 req/sec. Our call pattern is single-ticker-at-a-time,
# so Semaphore(3) is always within the rate limit and eliminates 503/429 risk.
EDGAR_SEMAPHORE_SIZE: int = 3  # conservative concurrency, not 10 req/sec burst

# FMP endpoints
FMP_STOCK_NEWS_URL = "https://financialmodelingprep.com/api/v3/stock_news"
FMP_PRESS_RELEASE_URL = "https://financialmodelingprep.com/api/v3/press-releases/{ticker}"

# EDGAR 8-K Atom feed — confirmed canonical URL (browse-edgar?output=atom).
# The efts.sec.gov/LATEST/search-index URL returns JSON (not Atom XML) and is NOT used.
# This URL returns valid Atom XML parsed by xml.etree.ElementTree (stdlib, no new deps).
# Entry fields used: <title>, <updated>, <link href="">.
# newsToday check: compare <updated> date to today in US/Eastern.
EDGAR_ATOM_URL = (
    "https://www.sec.gov/cgi-bin/browse-edgar"
    "?action=getcompany&company=&CIK={ticker}&type=8-K"
    "&dateb=&owner=include&count=10&search_text=&output=atom"
)

# Required by SEC EDGAR policy — automated tools must declare themselves or receive 403
EDGAR_USER_AGENT = "GapLens danny@dannyclarke.art"

# Tracking query params stripped during URL normalization
_TRACKING_PARAMS = frozenset({
    "utm_source", "utm_medium", "utm_campaign", "utm_content",
    "utm_term", "fbclid", "gclid", "_ga",
})

# Atom XML namespace
_ATOM_NS = "{http://www.w3.org/2005/Atom}"

# Source tier order: lower number = higher priority
_TIER: dict[str, int] = {"8-K": 1, "press-release": 2, "news": 3}


class NewsService:
    """
    Free-source news aggregation: SEC EDGAR Atom feeds + FMP news/press-releases.

    Two-tier cache (process-local dict):
      newsToday:{TICKER}  24h TTL  bool
      news:{TICKER}       30m TTL  list[NewsItem]

    Both keys are populated from the same live fetch when either misses.
    """

    # Required by SEC EDGAR policy — automated tools must declare themselves or receive 403
    EDGAR_USER_AGENT = "GapLens danny@dannyclarke.art"

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=15, follow_redirects=True)
        self._cache: dict[str, tuple[float, Any]] = {}
        self._edgar_semaphore = asyncio.Semaphore(EDGAR_SEMAPHORE_SIZE)

    # ── Cache helpers ────────────────────────────────────────────────────────

    def _cache_get(self, key: str, ttl: int) -> Any | None:
        """Return cached value if within ttl, else None."""
        if key not in self._cache:
            return None
        stored_at, value = self._cache[key]
        if time.time() - stored_at < ttl:
            return value
        return None

    def _cache_set(self, key: str, value: Any) -> None:
        """Store value. Never store None. bool (including False) is permitted."""
        if value is None:
            return
        self._cache[key] = (time.time(), value)

    # ── Deduplication ────────────────────────────────────────────────────────

    @staticmethod
    def _url_hash(url: str) -> str:
        """Normalize and hash a URL for deduplication.

        Normalization: lowercase, strip trailing slash, strip query params that
        are tracking-only (utm_*, fbclid, gclid, _ga). Hash with SHA-256, return
        first 16 hex chars — collision-resistant enough for this dataset size.
        """
        parsed = urlparse(url.lower().rstrip("/"))
        qs = {k: v for k, v in parse_qs(parsed.query).items()
              if k not in _TRACKING_PARAMS}
        normalized = parsed._replace(query=urlencode(qs, doseq=True)).geturl()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    # ── Source fetchers ──────────────────────────────────────────────────────

    async def _fetch_edgar_8k(self, ticker: str) -> list[dict]:
        """
        Fetch SEC EDGAR 8-K filings for ticker using Atom feed.

        Rate-limited via self._edgar_semaphore (EDGAR_SEMAPHORE_SIZE = 3 concurrent).
        Conservative concurrency limit for EDGAR rate compliance — at 300ms average
        response time, 3 concurrent ~= 10 req/sec max; at 600ms ~= 5 req/sec.
        User-Agent header is required by SEC EDGAR policy — omitting it returns 403.
        Returns list of NewsItem-shaped dicts with form_type="8-K".
        Returns [] on any error (non-200, XML parse failure, timeout).
        Never raises.
        """
        async with self._edgar_semaphore:
            try:
                url = EDGAR_ATOM_URL.format(ticker=ticker)
                resp = await self._http.get(
                    url,
                    headers={"User-Agent": self.EDGAR_USER_AGENT},
                )
                if resp.status_code != 200:
                    return []
                return self._parse_edgar_atom(resp.text)
            except Exception:
                return []

    def _parse_edgar_atom(self, xml_text: str) -> list[dict]:
        """
        Parse EDGAR Atom feed XML into list of NewsItem dicts.

        Uses stdlib xml.etree.ElementTree (no new dependency).
        Atom namespace: http://www.w3.org/2005/Atom
        Entry fields used: <title>, <updated>, <link href="">.

        Date conversion: parse full ISO timestamp from <updated>, convert to
        US/Eastern via ZoneInfo, then take .date() as string — NOT raw [:10]
        slice of the UTC string.

        Returns [] on any parse error — caller always receives a safe value.
        """
        try:
            root = _ET.fromstring(xml_text)
        except _ET.ParseError:
            return []

        items = []
        for entry in root.findall(f"{_ATOM_NS}entry"):
            link_el = entry.find(f"{_ATOM_NS}link")
            url = link_el.get("href", "") if link_el is not None else ""
            if not url:
                continue

            updated_el = entry.find(f"{_ATOM_NS}updated")
            published_at = ""
            if updated_el is not None and updated_el.text:
                try:
                    dt_utc = datetime.fromisoformat(
                        updated_el.text.replace("Z", "+00:00")
                    )
                    published_at = str(dt_utc.astimezone(ET).date())
                except (ValueError, TypeError):
                    published_at = ""

            title_el = entry.find(f"{_ATOM_NS}title")
            headline = ""
            if title_el is not None and title_el.text:
                headline = title_el.text

            items.append({
                "form_type": "8-K",
                "headline": headline,
                "url": url,
                "published_at": published_at,
            })
        return items

    async def _fetch_fmp_news(self, ticker: str) -> list[dict]:
        """
        FMP /api/v3/stock_news?tickers={ticker}&limit=10
        Returns list of NewsItem-shaped dicts with form_type="news".
        Returns [] on non-200 (including 429) or exception.
        No retry on 429.

        Date conversion: parse publishedDate as full ISO timestamp, convert to
        US/Eastern — NOT raw [:10]. Fallback: if parse fails, use raw_pub[:10].
        """
        api_key = settings.fmp_api_key
        if not api_key:
            return []
        try:
            resp = await self._http.get(
                FMP_STOCK_NEWS_URL,
                params={"tickers": ticker, "limit": 10, "apikey": api_key},
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            if not isinstance(data, list):
                return []
            items = []
            for item in data:
                raw_pub = item.get("publishedDate") or item.get("published_date") or ""
                published_at = ""
                if raw_pub:
                    try:
                        dt_utc = datetime.fromisoformat(
                            raw_pub.replace("Z", "+00:00")
                        )
                        if dt_utc.tzinfo is None:
                            dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))
                        published_at = str(dt_utc.astimezone(ET).date())
                    except (ValueError, TypeError):
                        published_at = raw_pub[:10]  # fallback: date-only string from FMP
                items.append({
                    "form_type": "news",
                    "headline": item.get("title") or item.get("headline") or "",
                    "url": item.get("url") or "",
                    "published_at": published_at,
                    "text": item.get("text") or "",
                    "site": item.get("site") or "",
                })
            return items
        except Exception:
            return []

    async def _fetch_fmp_press_releases(self, ticker: str) -> list[dict]:
        """
        FMP /api/v3/press-releases/{ticker}?limit=5
        Returns list of NewsItem-shaped dicts with form_type="press-release".
        Returns [] on non-200 (including 429) or exception.
        No retry on 429.

        Date conversion: same pattern as FMP news, field is `date` or `publishedDate`.
        """
        api_key = settings.fmp_api_key
        if not api_key:
            return []
        try:
            url = FMP_PRESS_RELEASE_URL.format(ticker=ticker)
            resp = await self._http.get(
                url,
                params={"limit": 5, "apikey": api_key},
            )
            if resp.status_code != 200:
                return []
            data = resp.json()
            if not isinstance(data, list):
                return []
            items = []
            for item in data:
                raw_pub = item.get("date") or item.get("publishedDate") or ""
                published_at = ""
                if raw_pub:
                    try:
                        dt_utc = datetime.fromisoformat(
                            raw_pub.replace("Z", "+00:00")
                        )
                        if dt_utc.tzinfo is None:
                            dt_utc = dt_utc.replace(tzinfo=ZoneInfo("UTC"))
                        published_at = str(dt_utc.astimezone(ET).date())
                    except (ValueError, TypeError):
                        published_at = raw_pub[:10]  # fallback: date-only string from FMP
                items.append({
                    "form_type": "press-release",
                    "headline": item.get("title") or "",
                    "url": item.get("url") or "",
                    "published_at": published_at,
                    "text": item.get("text") or "",
                    "site": item.get("site") or "",
                })
            return items
        except Exception:
            return []

    # ── Merge and rank ───────────────────────────────────────────────────────

    def _merge_and_rank(
        self,
        edgar_items: list[dict],
        pr_items: list[dict],
        news_items: list[dict],
    ) -> list[dict]:
        """
        Deduplicate by URL hash, then rank by source tier + recency.

        Tier order (ascending priority number = shown first):
          1. SEC EDGAR 8-K  (form_type == "8-K")
          2. FMP press releases (form_type == "press-release")
          3. FMP stock news  (form_type == "news")

        Within each tier: sort by published_at descending.
        Deduplication: when two items share the same URL hash, keep the one from
        the higher-priority tier (lower tier number). The FMP copy of an EDGAR
        filing is discarded.

        Two-pass stable sort (simpler than character-code negation):
          Pass 1: recency descending
          Pass 2: tier ascending (Python sort is stable, preserves recency order
                  within each tier)
        """
        all_items: list[dict] = edgar_items + pr_items + news_items
        seen: dict[str, dict] = {}
        for item in all_items:
            url = item.get("url") or ""
            if not url:
                continue
            h = NewsService._url_hash(url)
            if h not in seen:
                seen[h] = item
            else:
                # Keep higher-priority (lower tier number) item
                existing_tier = _TIER.get(seen[h].get("form_type", ""), 99)
                new_tier = _TIER.get(item.get("form_type", ""), 99)
                if new_tier < existing_tier:
                    seen[h] = item

        deduped = list(seen.values())
        # Pass 1: sort by recency descending
        deduped.sort(key=lambda x: x.get("published_at", ""), reverse=True)
        # Pass 2: sort by tier ascending (stable — preserves recency within each tier)
        deduped.sort(key=lambda x: _TIER.get(x.get("form_type", ""), 99))
        return deduped

    # ── Public API ───────────────────────────────────────────────────────────

    async def get_news(self, ticker: str, limit: int = 10) -> list[dict]:
        """
        Primary public method. Drop-in replacement for DilutionService.get_news.

        Cache read order:
          1. news:{TICKER} (30 min TTL) — return directly if hit.
          2. Cache miss: fetch all three sources concurrently, merge/rank,
             write news:{TICKER} (TTL_30M) and newsToday:{TICKER} (TTL_24H).

        Returns list of NewsItem dicts (same shape as AskEdgar /enterprise/v1/news).
        Returns [] if all sources fail. Never raises.

        Limit: truncate to `limit` items after ranking.
        """
        upper = ticker.upper()
        news_key = f"news:{upper}"
        news_today_key = f"newsToday:{upper}"

        cached = self._cache_get(news_key, TTL_30M)
        if cached is not None:
            return cached[:limit]

        edgar_items, pr_items, news_items = await asyncio.gather(
            self._fetch_edgar_8k(upper),
            self._fetch_fmp_press_releases(upper),
            self._fetch_fmp_news(upper),
            return_exceptions=True,
        )
        if isinstance(edgar_items, Exception):
            edgar_items = []
        if isinstance(pr_items, Exception):
            pr_items = []
        if isinstance(news_items, Exception):
            news_items = []

        merged = self._merge_and_rank(
            edgar_items,  # type: ignore[arg-type]
            pr_items,     # type: ignore[arg-type]
            news_items,   # type: ignore[arg-type]
        )

        # Populate both cache keys from the same fetch.
        # _cache_set never stores None; [] is a valid list and IS stored,
        # preventing repeat lookups for tickers with no news.
        self._cache_set(news_key, merged)

        # Derive newsToday bool using US/Eastern date comparison.
        # False is not None, so _cache_set will store it correctly.
        today_et = datetime.now(ET).date()
        news_today = any(
            n.get("form_type") in ("8-K", "6-K", "news", "press-release")
            and (n.get("published_at") or "")[:10] == str(today_et)
            for n in merged
        )
        self._cache_set(news_today_key, news_today)

        return merged[:limit]

    async def get_news_today(self, ticker: str) -> bool:
        """
        Returns newsToday bool for the 24h badge cache key.

        Cache read order:
          1. newsToday:{TICKER} (24h TTL) — return directly if hit.
          2. Cache miss: call get_news (which populates both keys).
        Returns False on any error.
        """
        upper = ticker.upper()
        news_today_key = f"newsToday:{upper}"

        cached = self._cache_get(news_today_key, TTL_24H)
        if cached is not None:
            return cached

        # get_news populates newsToday key as a side-effect
        await self.get_news(upper)
        result = self._cache_get(news_today_key, TTL_24H)
        return result if isinstance(result, bool) else False
