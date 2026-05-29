# AskEdgar Caching Guideline

Developer reference for the in-process cache layer that wraps all AskEdgar V2 API calls.
Last updated: 2026-05-29. Reflects timeout-sentinel-gap sprint (commit 6479eb5).

---

## Overview

The backend proxies a paid, metered AskEdgar V2 API. Every call costs money.
AskEdgar refreshes its data once per night (except news, which is real-time and
not server-cached). To match that update cadence, all four backend services use
an in-process Python dict cache keyed by `"<prefix>:<TICKER>"` (or `"<prefix>"`
for no-ticker endpoints like market-strength).

**Cache structure (DilutionService and IntelService):** `dict[str, tuple[float, Any, int | None]]`
Each entry is `(stored_at_epoch_float, value, ttl_override)`.
The third element is either `None` (use map/prefix lookup for TTL) or an explicit
integer TTL in seconds (used exclusively for backoff sentinels — see below).

**Cache structure (NewsService):** `dict[str, tuple[float, Any]]`
NewsService uses a plain 2-tuple `(stored_at, value)` — no sentinel or TTL override.

**Cache key format:**
- Per-ticker: `"<prefix>:<TICKER>"` — ticker is always uppercased at call time
- No-ticker: `"<prefix>"` (e.g., `"mkt_strength"`, `"pd_list"`)

**TTL dispatch in DilutionService and IntelService:**
`_cache_get(key)` splits the key on `":"`, takes the prefix, looks it up in
`CACHE_TTL_MAP`, and falls back to `TTL_24H` (86400 s) for any prefix not
explicitly listed. This means unregistered prefixes are safely overcached —
they will not cause surprise short-expiry calls.

---

## The `_CACHE_EMPTY` Sentinel and Backoff TTL (timeout-sentinel-gap sprint)

This is the most important behavioural change since the initial guideline was written.

### Confirmed-empty sentinel

DilutionService and IntelService both define a module-level `_CACHE_EMPTY = object()`
sentinel. When `_cache_set(key, None)` is called, the value stored is `_CACHE_EMPTY`
(not `None`). This means a confirmed-empty AskEdgar response (e.g. 200 OK with no
results for an unknown ticker) is cached and does not re-fire the live call until TTL
expires.

**The two-check caller pattern is mandatory in both services:**
```python
cached = self._cache_get(cache_key)
if cached is _CACHE_EMPTY:          # must come FIRST — _CACHE_EMPTY is truthy
    return None   # (or [] for list methods)
if cached is not None:
    return cached
# cache miss — proceed to live fetch
```
If the `is _CACHE_EMPTY` check is placed after `is not None`, a sentinel hit will
be treated as a cache miss and the live request fires every time. This is a latent
bug, not a runtime crash.

### Backoff sentinel

When a live fetch raises `asyncio.TimeoutError` or `httpx.RequestError`, the handler
calls `_cache_set(cache_key, None, ttl_override=TTL_BACKOFF)` (300 s, 5 min).

The 3-tuple TTL override takes priority over all other TTL resolution. On the next
call within the 5-minute window, `_cache_get` reads the override from `entry[2]`
and returns `_CACHE_EMPTY` — preventing a flood of retries against a temporarily
unreachable endpoint.

After 5 minutes the entry expires and the live call is attempted again.

**TTL priority order in IntelService._cache_get:**
1. Stored 3-tuple override (backoff sentinel written by timeout handler)
2. Caller-supplied `ttl` argument (used by `get_pump_and_dump_list` for CACHE_TTL_PD_LIST)
3. CACHE_TTL_MAP prefix lookup, falling back to TTL_24H

**NewsService does NOT use this pattern.** NewsService._cache_set silently drops
`None`. It has no sentinel and no backoff TTL. Callers handle errors inline.

---

## Service Map

| Service | File | Cache store | What it caches | TTL authority |
|---|---|---|---|---|
| `DilutionService` | `app/services/dilution.py` | `self._cache` | dilution, float, ownership, registrations, offerings, dilutiondata, gapstats, chart, screener | `CACHE_TTL_MAP` in dilution.py |
| `IntelService` | `app/services/intel.py` | `self._cache` | mkt_strength, pd, compliance, revsplit, filingtitles, histfloat, report, pd_list | `CACHE_TTL_MAP` in intel.py |
| `NewsService` | `app/services/news_service.py` | `self._cache` | news, newsToday | Explicit TTL constants in news_service.py |
| `WatchlistService` | `app/services/watchlist_service.py` | `self._fmp_cache` | FMP quote fields only (wlq:fmp prefix) | `FMP_QUOTE_TTL = 60 s` (class constant) |
| `GainersService` | `app/services/gainers.py` | `self._cache` + `self._fmp_enrich_cache` | gainer lists (TV/Massive/FMP) + per-ticker FMP enrichment | `CACHE_TTL_SECS = 60 s` (gainer lists); `FMP_ENRICH_TTL = 300 s` (enrichment) |

`IntelService` shares `DilutionService.client` (the httpx.AsyncClient that carries the
AskEdgar API key). `WatchlistService` and `GainersService` create their own separate
httpx clients for FMP calls and delegate all AskEdgar calls to `DilutionService` — they
never write to DilutionService's cache directly.

---

## AskEdgar TTL Reference

### DilutionService `CACHE_TTL_MAP` (`app/services/dilution.py`)

| Cache key prefix | AskEdgar endpoint | TTL |
|---|---|---|
| `dilution` | `/v1/dilution-rating` | 24 h |
| `float` | `/v1/float-outstanding` | 24 h |
| `ownership` | `/v1/ownership` | 24 h |
| `registrations` | `/v1/registrations` | 24 h |
| `offerings` | `/v1/offerings` | 24 h |
| `dilutiondata` | `/v1/dilution-data` | 24 h |
| `gapstats` | `/v1/gap-stats` | 24 h |
| `chart` | `/v1/ai-chart-analysis` | 24 h (+ explicit 10 s asyncio.wait_for) |
| `screener` | `/v1/screener` | 24 h |
| _(any other prefix)_ | _(fallback)_ | 24 h |

News keys (`news:*`, `newsToday:*`) are **not** in this map. DilutionService delegates
`get_news` and `get_news_today_cached` entirely to `NewsService` and does not write to
its own `_cache` for news.

### IntelService `CACHE_TTL_MAP` (`app/services/intel.py`)

| Cache key prefix | AskEdgar endpoint | TTL |
|---|---|---|
| `mkt_strength` | `/v1/market-strength` | 24 h |
| `pd` | `/v1/pump-and-dump-tracker` (per-ticker) | 30 m |
| `compliance` | `/v1/nasdaq-compliance` | 24 h |
| `revsplit` | `/v1/reverse-splits` | 24 h |
| `filingtitles` | `/v1/filing-titles` | 24 h |
| `histfloat` | `/v1/historical-float-pro` | 24 h |
| `report` | `/v1/research-reports` | 24 h |
| _(any other prefix)_ | _(fallback)_ | 24 h |

**Special case — `pd_list`:** `get_pump_and_dump_list` passes an explicit
`ttl=CACHE_TTL_PD_LIST` (300 s, 5 min) directly to `_cache_get`. This bypasses
`CACHE_TTL_MAP` entirely. The `pd_list` prefix is intentionally absent from the map.

`pd` per-ticker uses the `CACHE_TTL_MAP` lookup (30 m). `pd_list` (no-ticker, full
list) uses the explicit 5-minute override.

### NewsService (`app/services/news_service.py`)

| Cache key prefix | Content | TTL |
|---|---|---|
| `news` | Merged ranked news list (EDGAR 8-K + FMP stock_news + FMP press-releases) | 30 m |
| `newsToday` | Bool — any item with today's ET date | 24 h |

Both keys are populated from the same live fetch. When `get_news` is called and
`news:{TICKER}` misses, it fetches all three sources, writes `news:{TICKER}` (30 m),
and derives and writes `newsToday:{TICKER}` (24 h) as a side-effect.

`NewsService._cache_get` takes an explicit `ttl` argument — there is no map lookup.
Each call site passes the correct constant.

### WatchlistService (`app/services/watchlist_service.py`)

| Cache key prefix | Content | TTL |
|---|---|---|
| `wlq:fmp` | FMP quote + profile + float per ticker | 60 s |

`ASKEDGAR_TTL = 86400` is a documentation-only class constant; no code path reads it.
The actual AskEdgar TTL for WatchlistService-originated calls is whatever
DilutionService enforces (24 h for dilution-rating, 24 h for ai-chart-analysis,
24 h for newsToday via NewsService). WatchlistService cannot override those TTLs.

---

## Non-AskEdgar API Sources

All four sources below are free (no per-call charge) but subject to their own rate limits.

### TradingView Scanner (`scanner.tradingview.com/america/scan`)

- **Called by:** `GainersService._fetch_from_tradingview()`
- **Payload:** Top 30 US stocks by premarket % change — ticker, premarket price, volume, market cap
- **Backend cache:** `gainers:{filter_key}` — 60-second TTL (simple 2-tuple, no sentinel)
- **Not an AskEdgar endpoint — zero API cost**

### Massive API (Polygon) (`api.massive.com`)

Two endpoints, both in `GainersService`:

| Endpoint | Called by | Purpose | Cached? |
|---|---|---|---|
| `GET /v2/snapshot/locale/us/markets/stocks/gainers` | `_fetch_from_massive()` | Top gainer list with price/volume | `massive_gainers:{filter_key}` — 60 s |
| `GET /v3/reference/tickers/{ticker}` | `_filter_cs_tickers()` | Verify ticker is common stock (CS type) | Not cached — called once per gainer in the list |

The `_filter_cs_tickers` CS-check fires on every `get_massive_gainers()` call (after the 60-second list cache expires) for each ticker in the raw list. Each check is one HTTP request. No deduplication or per-ticker caching.

### FMP (financialmodelingprep.com)

FMP is used in four distinct contexts. All FMP calls are free tier (paid subscription, but not per-call metered like AskEdgar).

#### Gainer enrichment (GainersService)

| Endpoint | Called by | Purpose | Cached |
|---|---|---|---|
| `GET /stable/biggest-gainers` | `_fetch_from_fmp()` | FMP gainer list | `fmp_gainers:{filter_key}` — 60 s |
| `GET /api/v3/historical-chart/1min/{symbol}?extended=true&limit=1` | `_fetch_fmp_realtime_prices()` | Real-time price + volume per FMP gainer | Inside `_fetch_from_fmp()` (inherits 60 s list cache) |
| `GET /api/v3/profile/{ticker}` | `_fetch_fmp_profile_for_gainer()` | sector, country for Stage 1 filter | `fmpenrich:{TICKER}` — 5 min |

`fmpenrich:{TICKER}` is stored in `GainersService._fmp_enrich_cache` (separate from the gainer list cache). Shape is `{sector, country}` only. It is a simple 2-tuple with a fixed 5-minute TTL — no sentinel, no backoff.

#### Stage 2 AskEdgar enrichment (GainersService)

| Endpoint | Called by | Purpose | Cached |
|---|---|---|---|
| `GET /v1/dilution-rating` | `DilutionService._make_request_cached` | Dilution risk badge | `dilution:{TICKER}` — 24 h (shared with dilution panel) |
| `GET /v1/ai-chart-analysis` | `DilutionService.get_chart_analysis` | Chart rating badge | `chart:{TICKER}` — 24 h (shared with dilution panel) |
| `GET /v1/float-outstanding` | `DilutionService._make_request_cached` | Float shares + market cap for GainerRow | `float:{TICKER}` — 24 h (shared with dilution panel) |

All three are called concurrently via `asyncio.gather` in Stage 2 of `_enrich_gainer()`. The cache keys are shared with the dilution panel — a ticker selected after appearing on a gainer card will not re-fire these calls.

#### Watchlist quote enrichment (WatchlistService)

| Endpoint | Called by | Purpose | Cached |
|---|---|---|---|
| `GET /api/v3/quote/{ticker}` | `_fetch_fmp_quote()` | price, changesPercentage, volume, marketCap | `wlq:fmp:{TICKER}` — 60 s |
| `GET /api/v3/profile/{ticker}` | `_fetch_fmp_profile()` | sector, country | `wlq:fmp:{TICKER}` — 60 s (combined with quote + float) |
| `GET /api/v4/shares_float?symbol={ticker}` | `_fetch_fmp_float()` | Float shares | `wlq:fmp:{TICKER}` — 60 s (combined) |

All three are fetched concurrently and stored under a single `wlq:fmp:{TICKER}` key.

#### News (NewsService)

| Endpoint | Called by | Purpose | Cached |
|---|---|---|---|
| `GET /api/v3/stock_news?tickers={ticker}&limit=10` | `_fetch_fmp_news()` | General news articles | `news:{TICKER}` — 30 m (merged with EDGAR + press releases) |
| `GET /api/v3/press-releases/{ticker}?limit=5` | `_fetch_fmp_press_releases()` | Press releases | `news:{TICKER}` — 30 m (merged) |

### SEC EDGAR (sec.gov Atom feed)

- **Endpoint:** `GET https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={ticker}&type=8-K&output=atom`
- **Called by:** `NewsService._fetch_edgar_8k()`
- **Purpose:** SEC 8-K filings — highest priority news source (tier 1)
- **Cached:** `news:{TICKER}` — 30 m (merged with FMP news and press releases)
- **Rate limit:** `asyncio.Semaphore(3)` — conservative compliance with EDGAR's 10 req/sec policy
- **Required header:** `User-Agent: GapLens danny@dannyclarke.art` — EDGAR returns 403 without it
- **Not an AskEdgar endpoint — zero API cost**

---

## UI Field Provenance

Which field the frontend displays and which API ultimately provides it.

### GainerRow (gainer cards in all three panels)

| UI field | Source | Backend path |
|---|---|---|
| Ticker, price, volume, % change | TradingView / Massive / FMP | `_fetch_from_tradingview()` / `_fetch_from_massive()` / `_fetch_from_fmp()` |
| Float | AskEdgar `/v1/float-outstanding` | `DilutionService._cache` `float:` key |
| Market cap | AskEdgar `/v1/float-outstanding` (`market_cap_final`) | `DilutionService._cache` `float:` key |
| Sector | FMP `/api/v3/profile` | `GainersService._fmp_enrich_cache` |
| Country | FMP `/api/v3/profile` | `GainersService._fmp_enrich_cache` |
| Risk (dilution rating badge) | AskEdgar `/v1/dilution-rating` (`overall_offering_risk`) | `DilutionService._cache` `dilution:` key |
| Chart rating badge | AskEdgar `/v1/ai-chart-analysis` (`rating`) | `DilutionService._cache` `chart:` key |
| News today badge | EDGAR + FMP news (NewsService) | `NewsService._cache` `newsToday:` key |

### WatchlistColumn (watchlist ticker cards)

| UI field | Source | Backend path |
|---|---|---|
| Price, % change, volume, market cap | FMP `/api/v3/quote` | `WatchlistService._fmp_cache` `wlq:fmp:` |
| Float | FMP `/api/v4/shares_float` | `WatchlistService._fmp_cache` `wlq:fmp:` |
| Sector, country | FMP `/api/v3/profile` | `WatchlistService._fmp_cache` `wlq:fmp:` |
| Risk badge | AskEdgar `/v1/dilution-rating` | `DilutionService._cache` `dilution:` key |
| Chart rating badge | AskEdgar `/v1/ai-chart-analysis` | `DilutionService._cache` `chart:` key |
| News today badge | EDGAR + FMP (NewsService) | `NewsService._cache` `newsToday:` key |

### Dilution panel (shown when a ticker is selected)

All fields below come from `DilutionService.get_dilution_data_v2()`, which fans out
9 sub-calls concurrently.

| UI field(s) | Source | Cache key |
|---|---|---|
| Offering risk, dilution risk, cash need/runway, offering frequency, warrant exercise, mgmt commentary | AskEdgar `/v1/dilution-rating` | `dilution:{TICKER}` |
| Float, outstanding, market cap, industry, sector, country, insider %, institutional % | AskEdgar `/v1/float-outstanding` | `float:{TICKER}` |
| Warrants list, convertibles list (filtered by 4× price) | AskEdgar `/v1/dilution-data` | `dilutiondata:{TICKER}` |
| Gap stats table | AskEdgar `/v1/gap-stats` | `gapstats:{TICKER}` |
| Offerings list | AskEdgar `/v1/offerings` | `offerings:{TICKER}` |
| Registrations list | AskEdgar `/v1/registrations` | `registrations:{TICKER}` |
| Ownership block | AskEdgar `/v1/ownership` | `ownership:{TICKER}` |
| AI chart analysis | AskEdgar `/v1/ai-chart-analysis` | `chart:{TICKER}` |
| Stock price, short float, fee rate, days-to-cover, avg volume, exchange | AskEdgar `/v1/screener` | `screener:{TICKER}` |
| News list | EDGAR + FMP (NewsService) | `news:{TICKER}` |

### Intel panel (MarketStrengthBar + GainerEnrichment badges)

| UI field | Source | Cache key |
|---|---|---|
| Market strength text, sector performance table | AskEdgar `/v1/market-strength` | `mkt_strength` (global, no ticker) |
| Pump-and-dump hot list | AskEdgar `/v1/pump-and-dump-tracker` (no-ticker list) | `pd_list` |
| P&D score per ticker (batch enrichment) | AskEdgar `/v1/pump-and-dump-tracker` (per-ticker) | `pd:{TICKER}` |
| Compliance deficiency badge (batch enrichment) | AskEdgar `/v1/nasdaq-compliance` | `compliance:{TICKER}` |
| Reverse split badge (batch enrichment) | AskEdgar `/v1/reverse-splits` | `revsplit:{TICKER}` |
| Filing titles list | AskEdgar `/v1/filing-titles` | `filingtitles:{TICKER}` |
| Historical float chart | AskEdgar `/v1/historical-float-pro` | `histfloat:{TICKER}` |
| AI research report | AskEdgar `/v1/research-reports` | `report:{TICKER}` |

---

## Polling Frequency and Call Budget

How often each API call reaches the backend server (not the live upstream) during
an active trading session on the `/test` page with all three gainer columns enabled.

### Automatic (interval-driven)

| Component | Frontend interval | Backend endpoint | Backend cache TTL | Upstream fires |
|---|---|---|---|---|
| GainerPanel (TradingView) | 60 s (paused when tab hidden) | `GET /api/v1/gainers` | 60 s | Every ~60 s per unique filter state |
| GainerPanel (Massive) | 60 s (paused when tab hidden) | `GET /api/v1/gainers/massive` | 60 s | Every ~60 s + CS type check per ticker |
| GainerPanel (FMP) | 60 s (paused when tab hidden) | `GET /api/v1/gainers/fmp` | 60 s | Every ~60 s + realtime price per ticker |
| MarketStrengthBar (P&D list) | 300 s (paused when tab hidden) | `GET /api/v1/pump-and-dump-list` | 300 s | Every ~5 min |
| MarketStrengthBar (market strength) | On mount only | `GET /api/v1/market-strength` | 24 h | At most 1× per day |

### Reactive (triggered by data change)

| Trigger | Frontend call | Backend endpoint | Backend cache TTL | AskEdgar calls |
|---|---|---|---|---|
| Gainers data refreshes | `fetchBatchEnrichment(top 10 × active columns)` | `GET /api/v1/enrichment/batch` | P&D: 30 m, compliance: 24 h, revsplit: 24 h | Up to 3 AskEdgar calls per ticker on first hit; cached thereafter |
| Watchlist set changes (add/remove) | `fetchWatchlistQuote(watchlist)` | `GET /api/v1/watchlist-quote/batch` | FMP: 60 s, AskEdgar fields: 24 h | 3 FMP + 3 AskEdgar calls per new ticker; all cached |

### On user action (ticker select)

| Trigger | Backend endpoint | AskEdgar endpoints fired | Cache TTL |
|---|---|---|---|
| User selects ticker in dilution panel | `GET /api/v1/dilution/{ticker}` | 9 concurrent AskEdgar calls (see dilution panel table above) + 3 news sources | All 24 h except news (30 m) |

### Per-gainer AskEdgar cost (first load vs cached)

Each new ticker loaded into a gainer panel fires 3 calls/new ticker/24h via `_enrich_gainer()` Stage 2, plus 1 additional call via batch enrichment:
- `/v1/dilution-rating` (risk badge) — 24 h cache
- `/v1/ai-chart-analysis` (chart rating badge) — 24 h cache
- `/v1/float-outstanding` (float + marketCap on GainerRow) — 24 h cache

These are all 24-hour cached. After first load, a ticker appearing again within 24 hours
costs zero AskEdgar calls from Stage 2. The `/v1/pump-and-dump-tracker` per-ticker call
fires separately via batch enrichment (30 min cache) and is not part of `_enrich_gainer()`.

The P&D list (`pd_list`, 5-minute cache) fires independently of per-ticker P&D calls.
It is the global hot list shown in the P&D panel — not the per-ticker badge data.

---

## How to Add a New AskEdgar Endpoint

### Step 1: Choose the right service

- Nightly-update filing data (dilution, float, registrations, screener-type fields):
  add to **DilutionService**.
- Intel enrichment (compliance, P&D, splits, research, market-strength):
  add to **IntelService**.
- News (real-time or today-flag): add to **NewsService**.
- Do not add AskEdgar calls to WatchlistService — it delegates to DilutionService.

### Step 2: Pick a key prefix and TTL

Choose a short, lowercase, underscore-separated prefix that is not already in any
`CACHE_TTL_MAP`. If the endpoint updates nightly: add it to the relevant service's
`CACHE_TTL_MAP` with `TTL_24H`. If more frequent: either use `TTL_30M` in the map
or pass an explicit `ttl=` override to `_cache_get` (as `pd_list` does).

If you skip adding the prefix to the map, the fallback is `TTL_24H` — safe but
undocumented. Prefer explicit map entries.

### Step 3: Write the method

```python
# DilutionService example — new per-ticker endpoint
async def get_something(self, ticker: str) -> dict | None:
    upper = ticker.upper()
    cache_key = f"something:{upper}"
    cached = self._cache_get(cache_key)
    if cached is _CACHE_EMPTY:          # sentinel check FIRST
        return None
    if cached is not None:
        return cached
    try:
        result = await self._make_request("/v1/something", ticker)
        self._cache_set(cache_key, result)   # None → stored as _CACHE_EMPTY
        return result if result else None
    except (asyncio.TimeoutError, httpx.RequestError):
        self._cache_set(cache_key, None, ttl_override=TTL_BACKOFF)
        return None
    except Exception:
        return None
```

Or use the existing helper for list endpoints:

```python
return await self._make_request_list_cached(
    "/v1/something", {"ticker": ticker}, f"something:{upper}"
)
```

### Step 4: Register the prefix

Add the entry to `CACHE_TTL_MAP` in the service file:

```python
CACHE_TTL_MAP: dict[str, int] = {
    # ... existing entries ...
    "something":  TTL_24H,   # /v1/something — nightly update
}
```

Place it alphabetically among existing entries or grouped by logical domain.
Add a comment if the TTL choice is non-obvious.

### Step 5: Update this document

Add a row to the AskEdgar TTL reference table and the UI field provenance table
for the service you modified.

---

## Future Endpoints

**Historical Dilution Rating** (estimated ship: ~2026-05-23)
Add to DilutionService with a new `CACHE_TTL_MAP` entry. The prefix and exact
endpoint path will be confirmed when AskEdgar publishes the endpoint.

**Float Outstanding / Screener consolidation**
AskEdgar may consolidate these two endpoints. No action until AskEdgar notifies.
If they merge, the two existing map entries (`float`, `screener`) can be collapsed
into one — but that is a future cleanup, not a blocker.

---

## Common Mistakes

| Mistake | Effect | Fix |
|---|---|---|
| Forgetting to uppercase the ticker in the cache key | Cache miss on every call for the same ticker in different cases | Always call `ticker.upper()` before building the key |
| Placing `is _CACHE_EMPTY` check AFTER `is not None` | Sentinel treated as cache miss — live request fires on every call | `is _CACHE_EMPTY` must always be the FIRST check |
| Adding a news endpoint to DilutionService | Bypasses the two-tier dedup + ranking logic in NewsService | Add news endpoints to NewsService only |
| Reading `WatchlistService.ASKEDGAR_TTL` in new code | Documents 86400 s but has no enforcement effect | Use DilutionService methods directly; the TTL is enforced there |
| Passing `ttl=TTL_30M` to `_cache_get` for a nightly endpoint | Data refreshes every 30 min, wasting API calls | Use `CACHE_TTL_MAP` entry with `TTL_24H` instead |
| Assuming FMP provides dilution panel fields | Dilution panel fields (risk, float, warrants, gap-stats, etc.) all come from AskEdgar | Check the UI field provenance table before assuming a source |
| Assuming FMP still provides gainer card float/mcap | After gainer-float-accuracy sprint, float and marketCap on GainerRow come from AskEdgar `/v1/float-outstanding` via `DilutionService._make_request_cached` with cache key `float:{TICKER}`. FMP `shares_float` is no longer called in `_enrich_gainer`. | Check the UI field provenance table; `GainersService._fmp_enrich_cache` now holds only `{sector, country}` |
