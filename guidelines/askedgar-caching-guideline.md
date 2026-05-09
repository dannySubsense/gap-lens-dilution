# AskEdgar Caching Guideline

Developer reference for the in-process cache layer that wraps all AskEdgar V2 API calls.
As of 2026-05-09.

---

## Overview

The backend proxies a paid, metered AskEdgar V2 API. Every call costs money.
AskEdgar refreshes its data once per night (except news, which is real-time and
not server-cached). To match that update cadence, all four backend services use
an in-process Python dict cache keyed by `"<prefix>:<TICKER>"` (or `"<prefix>"`
for no-ticker endpoints like market-strength).

**Cache structure:** `dict[str, tuple[float, Any]]`
Each entry is `(stored_at_epoch_float, value)`.

**Cache key format:**
- Per-ticker: `"<prefix>:<TICKER>"` — ticker is always uppercased at call time
- No-ticker: `"<prefix>"` (e.g., `"mkt_strength"`, `"pd_list"`)

**TTL dispatch in DilutionService and IntelService:**
`_cache_get(key)` splits the key on `":"`, takes the prefix, looks it up in
`CACHE_TTL_MAP`, and falls back to `TTL_24H` (86400 s) for any prefix not
explicitly listed. This means unregistered prefixes are safely overcached —
they will not cause surprise short-expiry calls.

**None is never stored.** `_cache_set` silently drops `None` values. A
subsequent call for a ticker that returned `None` will re-fetch. `False`
(the `newsToday` bool) is stored correctly because it is not `None`.

**Single process.** The app runs with one uvicorn worker. The in-process dict is
shared across all requests; there is no inter-process or cross-restart cache.

---

## Service Map

| Service | File | Cache store | What it caches | TTL authority |
|---|---|---|---|---|
| `DilutionService` | `app/services/dilution.py` | `self._cache` | dilution, float, ownership, registrations, offerings, dilutiondata, gapstats, chart, screener | `CACHE_TTL_MAP` in dilution.py |
| `IntelService` | `app/services/intel.py` | `self._cache` | mkt_strength, pd, compliance, revsplit, filingtitles, histfloat, report, pd_list | `CACHE_TTL_MAP` in intel.py |
| `NewsService` | `app/services/news_service.py` | `self._cache` | news, newsToday | Explicit TTL constants in news_service.py |
| `WatchlistService` | `app/services/watchlist_service.py` | `self._fmp_cache` | FMP quote fields only (wlq:fmp prefix) | `FMP_QUOTE_TTL = 60 s` (class constant) |

`IntelService` shares `DilutionService.client` (the httpx.AsyncClient that carries the
AskEdgar API key). `WatchlistService` creates its own separate httpx client for FMP
calls and delegates all AskEdgar calls to `DilutionService` — it never writes to
DilutionService's cache directly.

---

## TTL Reference

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
| `chart` | `/v1/ai-chart-analysis` | 24 h |
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
| `news` | Merged ranked news list (EDGAR 8-K + FMP news + FMP press releases) | 30 m |
| `newsToday` | Bool — any item with today's ET date | 24 h |

Both keys are populated from the same live fetch. When `get_news` is called and
`news:{TICKER}` misses, it fetches all three sources, writes `news:{TICKER}` (30 m),
and derives and writes `newsToday:{TICKER}` (24 h) as a side-effect.

`NewsService._cache_get` takes an explicit `ttl` argument — there is no map lookup.
Each call site passes the correct constant.

### WatchlistService (`app/services/watchlist_service.py`)

| Cache key prefix | Content | TTL |
|---|---|---|
| `wlq:fmp` | FMP quote, profile, float per ticker | 60 s |

`ASKEDGAR_TTL = 86400` is a documentation-only class constant; no code path reads it.
The actual AskEdgar TTL for WatchlistService-originated calls is whatever
DilutionService enforces (24 h for dilution-rating, 24 h for ai-chart-analysis,
24 h for newsToday via NewsService). WatchlistService cannot override those TTLs.

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
    if cached is not None:
        return cached
    try:
        result = await self._make_request("/v1/something", ticker)
        if not result:
            return None
        self._cache_set(cache_key, result)
        return result
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

Add a row to the TTL reference table for the service you modified.

---

## Future Endpoints

Two known additions are pending as of 2026-05-09:

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
| Storing `None` via `_cache_set` | No-op — `None` is silently dropped; next call re-fetches | Return `None` without calling `_cache_set`; that is the correct pattern |
| Adding a news endpoint to DilutionService | Bypasses the two-tier dedup + ranking logic in NewsService | Add news endpoints to NewsService only |
| Reading `WatchlistService.ASKEDGAR_TTL` in new code | Documents 86400 s but has no enforcement effect | Use DilutionService methods directly; the TTL is enforced there |
| Passing `ttl=TTL_30M` to `_cache_get` for a nightly endpoint | Data refreshes every 30 min, wasting API calls | Use `CACHE_TTL_MAP` entry with `TTL_24H` instead |
