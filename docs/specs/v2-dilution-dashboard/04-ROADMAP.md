# Implementation Roadmap: v2-dilution-dashboard

**Version:** 2.0
**Date:** 2026-04-03
**Status:** Ready for Implementation
**Author:** @planner

---

## Overview

This roadmap breaks the V2 architecture into 9 ordered slices. Each slice is independently testable and produces a deployable increment. The sequence is fixed: later slices depend on earlier ones. No slice may be started until all slices it depends on are complete and passing tests.

Total slices: 9
Blocking dependencies mapped: 12

---

## Dependency Map

| Unit | Depends On |
|------|-----------|
| Slice 1: Fix endpoint prefixes + config | — |
| Slice 2: Backend in-memory cache | Slice 1 |
| Slice 3: Backend Pydantic response models | Slice 1 |
| Slice 4: Extend dilution endpoint (V2 sub-calls) | Slice 2, Slice 3 |
| Slice 5: New gainers backend endpoint | Slice 2, Slice 3 |
| Slice 6: Frontend types + API service layer | Slice 4, Slice 5 |
| Slice 7: Two-panel layout shell + page.tsx rewrite | Slice 6 |
| Slice 8: Gainers sidebar components | Slice 7 |
| Slice 9: Right-panel new and updated components | Slice 7 |

Slices 8 and 9 have no dependency on each other and may be implemented in parallel by separate agents.

---

## Slice Overview

| Slice | Goal | Depends On | Files Touched |
|-------|------|-----------|--------------|
| 1 | Fix enterprise endpoint prefixes and base URL config | — | 2 |
| 2 | Add in-memory TTL cache to DilutionService | Slice 1 | 1 |
| 3 | Create backend Pydantic response models | Slice 1 | 1 (new) |
| 4 | Extend dilution endpoint with 5 new sub-calls | Slice 2, 3 | 2 |
| 5 | New /api/v1/gainers endpoint and GainersService | Slice 2, 3 | 3 (2 new) |
| 6 | Frontend types rewrite + API service module | Slice 4, 5 | 2 (1 new) |
| 7 | Two-panel layout shell + page.tsx rewrite | Slice 6 | 1 |
| 8 | GainerRow + TopGainersSidebar components | Slice 7 | 2 (new) |
| 9 | Five new + three updated right-panel components | Slice 7 | 8 (5 new, 3 updated) |

---

## Slices

---

### Slice 1: Fix Enterprise Endpoint Prefixes and Base URL Config

**Goal:** Correct all AskEdgar API endpoint paths so the existing backend makes real calls to the right URLs before any new code is written on top of it.

**Depends On:** —

**Context:** The existing `app/services/dilution.py` calls `/v1/dilution-rating`, `/v1/float-outstanding`, `/v1/news`, `/v1/registrations`, and `/v1/dilution-data`. Per the architecture spec (Pre-Architecture Note), all five of these must use the `/enterprise/v1/` prefix. The config also has a stale default base URL (`https://ask-edgar.com` instead of `https://eapi.askedgar.io`).

**Files:**
- `app/services/dilution.py` — update 5 endpoint path strings from `/v1/` to `/enterprise/v1/`
- `app/core/config.py` — update default `askedgar_url` to `https://eapi.askedgar.io`

**Implementation Notes:**
- Change `"/v1/dilution-rating"` to `"/enterprise/v1/dilution-rating"` in `get_dilution_data`
- Change `"/v1/float-outstanding"` to `"/enterprise/v1/float-outstanding"` in `get_dilution_data`
- Change `"/v1/news"` to `"/enterprise/v1/news"` in `get_news`
- Change `"/v1/registrations"` to `"/enterprise/v1/registrations"` in `get_registrations`
- Change `"/v1/dilution-data"` to `"/enterprise/v1/dilution-data"` in `get_dilution_detail`
- The 5 new endpoints (gap-stats, offerings, ownership, ai-chart-analysis, screener) added in Slice 4 use `/v1/` prefix — do not change those; keep them as standard-tier paths.
- Update only the default value in `config.py`; do not change the `.env` variable name.

**Tests:**
- [ ] Start the backend and call `GET /api/v1/dilution/EEIQ`; observe the outbound request URL in logs — it must contain `/enterprise/v1/dilution-rating`, not `/v1/dilution-rating`.
- [ ] Confirm no 404 from AskEdgar on the corrected endpoints (requires a valid API key in `.env`).
- [ ] If live API key is unavailable: mock `httpx.AsyncClient.get` in a unit test and assert the URL passed matches the correct prefix for each of the 5 existing calls.

**Done When:**
- [ ] All 5 existing AskEdgar calls in `dilution.py` use `/enterprise/v1/` prefix.
- [ ] `askedgar_url` default in `config.py` is `https://eapi.askedgar.io`.
- [ ] Existing tests (if any) still pass.
- [ ] No regressions in `GET /api/v1/dilution/{ticker}` behavior.

**User Stories Satisfied:** Prerequisite for US-18 (extended endpoint), US-13 (caching).

---

### Slice 2: Backend In-Memory TTL Cache

**Goal:** Add a 30-minute in-memory TTL cache to `DilutionService` so all sub-calls (existing and future) can be served from cache on repeated requests.

**Depends On:** Slice 1

**Files:**
- `app/services/dilution.py` — add class-level `_cache` dict and `_cache_get`, `_cache_set`, `_make_request_cached`, `_make_request_list_cached` methods

**Implementation Notes:**
- Add `_cache: dict[str, tuple[float, Any]] = {}` as a class-level attribute on `DilutionService`.
- Cache key format: `"{endpoint_name}:{ticker_uppercase}"` — e.g., `"dilution:EEIQ"`.
- TTL is 30 minutes (1800 seconds). Compare `time.time() - stored_at` against the TTL.
- `_cache_get(key)`: returns cached value if within TTL, else `None`.
- `_cache_set(key, value)`: writes `(time.time(), value)` to `_cache`. **Precondition: only call when value is not None and not an error sentinel.**
- `_make_request_cached(endpoint, params, cache_key)`: wraps `_make_request` with cache lookup/write. Returns `None` on 404 or any exception (does not raise for optional sub-calls).
- `_make_request_list_cached(endpoint, params, cache_key)`: wraps `_make_request_list` with cache lookup/write. Returns `[]` on error.
- The news endpoint must never be cached — do not create a `_make_request_cached` call path for news. The existing `get_news` method continues to call `_make_request_list` directly.
- Cache is module-scoped (single instance per process). No persistence.

**Tests:**
- [ ] Unit test: call `_cache_set("dilution:TEST", {"data": 1})`; immediately call `_cache_get("dilution:TEST")`; assert value is returned.
- [ ] Unit test: set a cache entry with a timestamp 31 minutes in the past; call `_cache_get`; assert `None` is returned (TTL expired).
- [ ] Unit test: call `_make_request_cached` twice for the same key; mock the HTTP client; assert the HTTP client is called exactly once (second call is served from cache).
- [ ] Unit test: verify that when `_make_request_cached` receives a `None` result from the live call, `_cache_set` is not called.
- [ ] Confirm `get_news` still calls `_make_request_list` directly (no cache path).

**Done When:**
- [ ] `DilutionService` has `_cache` dict and all 4 cache methods.
- [ ] `_cache_get` respects 30-minute TTL.
- [ ] `_cache_set` never stores `None`.
- [ ] `get_news` bypasses cache.
- [ ] All cache method unit tests pass.

**User Stories Satisfied:** US-13 (AC-13)

---

### Slice 3: Backend Pydantic Response Models

**Goal:** Create the `app/models/responses.py` file with all Pydantic models needed for V2 responses.

**Depends On:** Slice 1

**Files:**
- `app/models/responses.py` — create new file with all V2 response models

**Implementation Notes:**
- Create `app/models/__init__.py` if it does not exist (empty file is fine).
- Define these models per the architecture spec (Section 3.1):
  - `GapStatEntry`
  - `OfferingEntry`
  - `OwnerEntry`
  - `OwnershipGroup`
  - `ChartAnalysis`
  - `WarrantItem`
  - `ConvertibleItem`
  - `DilutionV2Response`
  - `GainerEntry`
- `DilutionV2Response` must include all V1 fields (mapped from existing `get_dilution_data` result) plus new V2 fields: `gapStats`, `offerings`, `ownership`, `chartAnalysis`, `stockPrice`, `mgmtCommentary`.
- Python reserved word collision: `float` field must be aliased. Use `model_config = ConfigDict(populate_by_name=True)` and `Field(alias="float")` for the `float_` field, or use `model_config` with `serialization_alias`. Match the architecture spec exactly: the field in the JSON response must be `"float"` (not `"float_"`).
- `warrants` field in `DilutionV2Response` holds `list[WarrantItem]`; `convertibles` holds `list[ConvertibleItem]`.
- `news` and `registrations` fields hold `list` (untyped, for flexibility).

**Tests:**
- [ ] Unit test: instantiate `DilutionV2Response` with all required fields; assert it does not raise `ValidationError`.
- [ ] Unit test: instantiate `GainerEntry` with `newsToday=False` and all `Optional` fields as `None`; assert valid.
- [ ] Unit test: serialize `DilutionV2Response` to JSON; assert the `float` field appears as `"float"` in the output (not `"float_"`).

**Done When:**
- [ ] `app/models/responses.py` exists and imports cleanly.
- [ ] All 9 model classes are defined.
- [ ] `DilutionV2Response` covers every field documented in architecture Section 3.1.
- [ ] Model unit tests pass.

**User Stories Satisfied:** Prerequisite for US-18, US-19.

---

### Slice 4: Extend Dilution Endpoint with V2 Sub-Calls

**Goal:** Wire the 5 new AskEdgar endpoints (gap-stats, offerings, ownership, ai-chart-analysis, screener) into the existing `GET /api/v1/dilution/{ticker}` endpoint so it returns the full `DilutionV2Response`.

**Depends On:** Slice 2, Slice 3

**Files:**
- `app/services/dilution.py` — add 5 new service methods and rewrite `get_dilution_data` → `get_dilution_data_v2`
- `app/api/v1/routes.py` — update handler to call `get_dilution_data_v2` and return `DilutionV2Response`

**Implementation Notes:**

Add these 5 methods to `DilutionService`, each using `_make_request_cached` or `_make_request_list_cached`:

```
get_gap_stats(ticker):
  GET /v1/gap-stats?ticker={ticker}&page=1&limit=100
  cache key: "gapstats:{ticker}"
  returns: list[dict] ([] on error/404)

get_offerings(ticker):
  GET /v1/offerings?ticker={ticker}&limit=5
  cache key: "offerings:{ticker}"
  returns: list[dict] ([] on error/404)

get_ownership(ticker):
  GET /v1/ownership?ticker={ticker}&limit=100
  cache key: "ownership:{ticker}"
  returns: dict | None (first result, or None if empty/error)

get_chart_analysis(ticker):
  GET /v1/ai-chart-analysis?ticker={ticker}&limit=1
  cache key: "chart:{ticker}"
  returns: dict | None (first result, or None if empty/error)

get_screener_price(ticker):
  GET /enterprise/v1/screener?ticker={ticker}
  cache key: "price:{ticker}"
  returns: float | None (price field from first result, or None)
```

Rewrite `get_dilution_data` as `get_dilution_data_v2`:
- Run all 9 sub-calls concurrently via `asyncio.gather(..., return_exceptions=True)`.
- The 9 calls: dilution-rating, float-outstanding, news (no cache), dilution-data, gap-stats, offerings, ownership, ai-chart-analysis, screener.
- Check each result: if it is an `Exception` instance, replace with the appropriate null/empty value.
- `mgmtCommentary`: extract `mgmt_commentary` field from dilution-rating result (no new AskEdgar call needed — it is a field in the existing response).
- `convertibles` extraction: items from dilution-data where `conversion_price` is present and `underlying_shares_remaining > 0`. Items with `registered == "Not Registered"` and `filed_at` within 180 days are excluded from warrants but included from convertibles.
- Warrants extraction: items from dilution-data where `warrants_remaining > 0` and (`registered != "Not Registered"` or item is a convertible).
- Return a `DilutionV2Response` (or dict matching its shape) — not the old untyped dict.
- The route handler must map `TickerNotFoundError` → 404, `RateLimitError` → 429, other exceptions → 500. Partial failures in sub-calls do not propagate as errors.

**Tests:**
- [ ] Integration test: mock all 9 AskEdgar calls; call `get_dilution_data_v2("TEST")`; assert the result contains `gapStats`, `offerings`, `ownership`, `chartAnalysis`, `stockPrice`, `mgmtCommentary` keys.
- [ ] Unit test: when gap-stats call raises an exception, `get_dilution_data_v2` still returns a result with `gapStats: []` (no 500).
- [ ] Unit test: when ownership call returns `[]`, `ownership` field in result is `None`.
- [ ] Unit test: `mgmtCommentary` is extracted from dilution-rating `mgmt_commentary` field.
- [ ] Integration test: `GET /api/v1/dilution/EEIQ` returns HTTP 200 with all V2 fields in the JSON body.
- [ ] Integration test: when ticker is not found, returns HTTP 404.
- [ ] Cache test: call the endpoint twice for the same ticker within 30 seconds; assert the AskEdgar calls (except news) are made only once.

**Done When:**
- [ ] `DilutionService` has all 5 new methods.
- [ ] `get_dilution_data_v2` runs all 9 sub-calls concurrently.
- [ ] Sub-call failures degrade gracefully to null/[].
- [ ] Route handler calls `get_dilution_data_v2`.
- [ ] Response JSON includes all `DilutionV2Response` fields.
- [ ] All tests pass.

**User Stories Satisfied:** US-05 (gap stats data), US-06 (offerings data), US-07 (ownership data), US-08 (chart analysis data), US-09 (convertibles data), US-11 (mgmt commentary data), US-12 (stock price data), US-13 (caching), US-15 (error states), US-18 (AC-18)

---

### Slice 5: New /api/v1/gainers Endpoint and GainersService

**Goal:** Create the `/api/v1/gainers` backend endpoint that fetches from TradingView, filters, and enriches each gainer in parallel.

**Depends On:** Slice 2, Slice 3

**Files:**
- `app/services/gainers.py` — create new file with `GainersService`
- `app/api/v1/routes.py` — add `GET /gainers` route
- `app/main.py` — no changes needed (router already registered)

**Implementation Notes:**

`GainersService` class:
- `TRADINGVIEW_URL = "https://scanner.tradingview.com/america/scan"`
- `MIN_CHANGE_PCT = 15.0`
- `TICKER_RE = re.compile(r'^[A-Z]{2,4}$')`
- `CACHE_TTL_SECS = 60`
- Class-level `_cache: dict[str, tuple[float, list]] = {}`; key is `"gainers"`.
- `__init__` receives a `DilutionService` instance.

`get_gainers()`:
- Check `_cache["gainers"]` — if present and age < 60 seconds, return cached list.
- Otherwise: call `_fetch_from_tradingview()`, filter by `TICKER_RE` and `>= 15%` change, run `_enrich_gainer()` on each via `asyncio.gather`.
- Store enriched list in `_cache["gainers"]` with current timestamp.
- On any error: return `[]` (never raise).

`_fetch_from_tradingview()`:
- POST to `TRADINGVIEW_URL` with the scanner body from INTAKE.md.
- Parse response: extract each ticker's `d` array values for `name` (ticker), `change_from_open` (or appropriate change field), `close` (price), `volume`.
- Filter: ticker matches `TICKER_RE` and change >= 15.0.
- Return list of raw dicts. Return `[]` on any error.

`_enrich_gainer(item)`:
- Run 4 calls concurrently via `asyncio.gather`:
  1. `dilution_service.get_float(ticker)` — for `float_` and `marketCap` and `sector` and `country`
  2. `dilution_service._get_dilution_rating(ticker)` — for `risk` level
  3. `dilution_service.get_chart_analysis(ticker)` — for `chartRating`
  4. News check: fetch latest news and check if any item's `filed_at` date is today's date
- All 4 use the 30-minute cache from `DilutionService` (no extra calls if ticker was recently looked up).
- Partial failures: set missing fields to `None`/`False`.
- Return a dict matching `GainerEntry` shape.

Route addition in `routes.py`:
```python
@router.get("/gainers")
async def get_gainers():
    data = await gainers_service.get_gainers()
    return data
```

Instantiate `GainersService` at module level in `routes.py` alongside `DilutionService`:
```python
gainers_service = GainersService(dilution_service)
```

**Tests:**
- [ ] Unit test: `_fetch_from_tradingview()` with a mocked TradingView response; assert only tickers matching `^[A-Z]{2,4}$` with change >= 15% are returned.
- [ ] Unit test: `_fetch_from_tradingview()` raises an exception; assert `[]` is returned.
- [ ] Unit test: `get_gainers()` is called twice within 60 seconds; mock TV call; assert TV is called only once (cache hit).
- [ ] Unit test: `_enrich_gainer()` where chart-analysis call raises; assert `chartRating` is `None` in result (partial failure).
- [ ] Integration test: `GET /api/v1/gainers` returns HTTP 200 with a JSON array (may be empty if TV unreachable).
- [ ] Integration test: when TradingView is unreachable, `GET /api/v1/gainers` returns `200 []` (not 500).

**Done When:**
- [ ] `app/services/gainers.py` exists with complete `GainersService`.
- [ ] `GET /api/v1/gainers` route is registered.
- [ ] Filtering by ticker pattern and 15% change is applied.
- [ ] Enrichment runs in parallel.
- [ ] 60-second server-side cache works.
- [ ] Graceful empty-array response on any failure.
- [ ] All tests pass.

**User Stories Satisfied:** US-02 (gainer data), US-13 (caching), US-14 (auto-refresh data), US-19 (AC-19)

---

### Slice 6: Frontend Types Rewrite and API Service Module

**Goal:** Replace the existing `dilution.ts` types file with the full V2 type definitions, and create the `api.ts` service module so all subsequent frontend components have typed data and a single fetch layer.

**Depends On:** Slice 4, Slice 5

**Context:** The current `frontend/src/types/dilution.ts` uses the V1 type shapes (flat `DilutionReport`, simple `Warrant`, old `OfferingAbilityData`). The new shapes match the `DilutionResponse` and `GainerEntry` from architecture Section 3.3. The existing component props will need to be updated — that happens in Slices 8 and 9.

**Files:**
- `frontend/src/types/dilution.ts` — full rewrite with V2 type definitions
- `frontend/src/services/api.ts` — create new file

**Implementation Notes for `dilution.ts`:**
- Replace the entire file content with the type definitions from architecture Section 3.3.
- Preserve all types: `RiskLevel`, `ChartRating`, `HeaderData`, `FilingType`, `Headline`, `RiskAssessment`, `JMT415Note`, `OfferingAbilityData`, `WarrantItem`, `ConvertibleItem`, `InPlayDilutionData`, `GapStatEntry`, `GapStatsComputed`, `OfferingEntry`, `OwnerEntry`, `OwnershipData`, `ChartAnalysis`, `GainerEntry`, `DilutionResponse`, `RawWarrantItem`, `RawConvertibleItem`, `ApiResult<T>`.
- `RiskLevel` now includes `"N/A"` (V1 had only `"Low" | "Medium" | "High"`).
- `FilingType` adds `"news"` and `"jmt415"` values.
- `HeaderData` adds `stockPrice: number | null` and `chartAnalysis: ChartAnalysis | null`.
- `InPlayDilutionData` adds `convertibles: ConvertibleItem[]` and `stockPrice: number | null`.
- `OfferingAbilityData` simplifies to `{ offeringAbilityDesc: string | null }`.

**Implementation Notes for `api.ts`:**
- Read base URL from `process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"`.
- `fetchDilution(ticker: string, signal?: AbortSignal): Promise<ApiResult<DilutionResponse>>`:
  - `GET {BASE_URL}/api/v1/dilution/{ticker}`
  - Map 404 → `{ ok: false, status: 404, message: "No dilution data available for {ticker}" }`
  - Map 429 → `{ ok: false, status: 429, message: "Rate limit exceeded. Try again later." }`
  - Map network errors or 5xx → `{ ok: false, status: 500, message: "API error. Please retry." }`
  - On success → `{ ok: true, data: responseJson }`
  - Pass `signal` to `fetch()` for abort support.
- `fetchGainers(): Promise<ApiResult<GainerEntry[]>>`:
  - `GET {BASE_URL}/api/v1/gainers`
  - Map any error → `{ ok: false, status: 500, message: "Could not load gainers." }`
  - On success → `{ ok: true, data: responseJson }`
- Neither function throws. All errors are captured and returned as typed results.

**Tests:**
- [ ] TypeScript compiler (`tsc --noEmit`) passes with no errors after the types rewrite.
- [ ] Unit test (jest or vitest): `fetchDilution` with a mocked `fetch` returning 404; assert result is `{ ok: false, status: 404, message: ... }`.
- [ ] Unit test: `fetchDilution` with a mocked `fetch` returning 200 with valid JSON; assert `{ ok: true, data: ... }`.
- [ ] Unit test: `fetchDilution` where `fetch` throws a network error; assert `{ ok: false, status: 500, message: ... }`.
- [ ] Unit test: `fetchGainers` with mocked 200 response; assert `{ ok: true, data: [...] }`.

**Done When:**
- [ ] `frontend/src/types/dilution.ts` contains all V2 types with no compilation errors.
- [ ] `frontend/src/services/api.ts` exists with `fetchDilution` and `fetchGainers`.
- [ ] Neither function contains raw `fetch` inside components.
- [ ] All unit tests pass.
- [ ] `tsc --noEmit` reports no type errors in the updated types file.

**User Stories Satisfied:** US-17 (AC-17)

---

### Slice 7: Two-Panel Layout Shell and page.tsx Rewrite

**Goal:** Replace the single-column `page.tsx` with the two-panel layout shell, wiring state management, AbortController fetch, search, and gainer-click handlers — but using stub/null props for components not yet built.

**Depends On:** Slice 6

**Context:** The current `page.tsx` uses static placeholder data and a single column layout. This slice rewrites it to the two-panel shell. Components that do not yet exist (TopGainersSidebar, GainerRow) are rendered as `null` or a placeholder `<div>` until Slice 8 completes. New right-panel components (GapStats, Offerings, Ownership, MgmtCommentary, ChartAnalysisBadge) are similarly stubbed or omitted until Slice 9 completes.

**Files:**
- `frontend/src/app/page.tsx` — full rewrite

**Implementation Notes:**

State shape (managed by `page.tsx`):
```typescript
const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
const [sidebarSelectedTicker, setSidebarSelectedTicker] = useState<string | null>(null);
const [dilutionData, setDilutionData] = useState<DilutionResponse | null>(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<{ status: number; message: string } | null>(null);
const abortRef = useRef<AbortController | null>(null);
```

`loadTicker(ticker: string, clearSidebar: boolean)` handler:
1. Abort any in-flight request: `abortRef.current?.abort()`.
2. Create new `AbortController`; store in `abortRef.current`.
3. Set `isLoading = true`, `dilutionData = null`, `error = null`.
4. If `clearSidebar`: `setSidebarSelectedTicker(null)`.
5. Call `fetchDilution(ticker, abortRef.current.signal)`.
6. If `result.ok`: `setDilutionData(result.data)`, `setIsLoading(false)`.
7. If `!result.ok` and not aborted: `setError({ status: result.status, message: result.message })`, `setIsLoading(false)`.
8. If aborted: discard result, no state update.

`handleGainerSelect(ticker: string)`:
- `setSidebarSelectedTicker(ticker)`.
- Call `loadTicker(ticker, false)`.

`handleSearch(ticker: string)`:
- If empty: return.
- Call `loadTicker(ticker, true)`.

Layout structure:
```tsx
<div className="flex h-screen overflow-hidden bg-[#0e111a]">
  {/* Left sidebar — stub until Slice 8 */}
  <div className="w-[260px] shrink-0 border-r border-[#2a3447] flex flex-col h-full overflow-hidden">
    {/* TopGainersSidebar will go here in Slice 8 */}
    <div className="p-3 text-[#9aa7c7] text-xs">Gainers sidebar — coming soon</div>
  </div>
  {/* Right panel */}
  <div className="flex-1 overflow-y-auto p-4 space-y-4">
    <TickerSearch onSearch={handleSearch} />
    {/* Idle state */}
    {!selectedTicker && !isLoading && !error && (
      <p className="text-[#9aa7c7] text-sm text-center mt-16">
        Search a ticker or click a gainer to begin.
      </p>
    )}
    {/* Error state */}
    {error && (
      <div className="bg-[#1b2230] border border-[#2a3447] rounded-[9px] p-5">
        <p className="text-[#ff6b6b] text-sm">{error.message}</p>
        <button onClick={() => selectedTicker && loadTicker(selectedTicker, false)}
          className="mt-3 text-xs text-[#ff4fa6] hover:underline">
          Retry
        </button>
      </div>
    )}
    {/* Loaded/loading states — existing V1 components wired to dilutionData */}
    {(isLoading || dilutionData) && (
      <>
        <Header data={dilutionData ? buildHeaderData(dilutionData) : null} />
        <Headlines data={dilutionData?.news ?? null} />
        <RiskBadges data={dilutionData ? buildRiskData(dilutionData) : null} />
        <OfferingAbility offeringAbilityDesc={dilutionData?.offeringAbilityDesc ?? null} />
        <InPlayDilution data={dilutionData ? buildInPlayData(dilutionData) : null} />
        <JMT415Notes data={dilutionData ? extractJMT415(dilutionData.news) : null} />
        {/* New panels — stubbed until Slice 9 */}
      </>
    )}
  </div>
</div>
```

Helper functions (defined in page.tsx or a co-located utils file):
- `buildHeaderData(d: DilutionResponse): HeaderData` — maps response fields to `HeaderData`.
- `buildRiskData(d: DilutionResponse): RiskAssessment` — maps risk fields.
- `buildInPlayData(d: DilutionResponse): InPlayDilutionData` — maps warrants + convertibles, includes `stockPrice`.
- `extractJMT415(news: Headline[]): JMT415Note[]` — filters filingType `"jmt415"` items.

Note on component prop changes: `OfferingAbility` now receives `offeringAbilityDesc: string | null` (not the old `OfferingAbilityData` object) — its internal logic is updated in Slice 9. For this slice, pass the raw string prop and leave `OfferingAbility`'s implementation temporarily compatible or import the existing component with an adapter shim if needed to avoid breaking the build.

**Tests:**
- [ ] `tsc --noEmit` passes with no type errors.
- [ ] Visual check: app loads in browser with two-panel shell; left stub, right panel idle state visible.
- [ ] Typing a ticker in search and pressing Enter triggers a `fetchDilution` call (visible in network tab).
- [ ] While loading: right panel shows skeleton states for Header, Headlines, RiskBadges, InPlayDilution.
- [ ] On successful load: Header, Headlines, RiskBadges, InPlayDilution render with live data.
- [ ] On 404 response: error card appears with correct message.
- [ ] Clicking Search with empty input: no network request made.
- [ ] Two rapid ticker searches: only the second ticker's response updates the UI (abort test).

**Done When:**
- [ ] `page.tsx` uses the two-panel layout.
- [ ] State machine (idle → loading → loaded/error) works correctly.
- [ ] AbortController cancels superseded requests.
- [ ] All existing V1 components (Header, Headlines, RiskBadges, InPlayDilution, JMT415Notes) render live data from the API.
- [ ] Sidebar stub is present in the left panel.
- [ ] `tsc --noEmit` passes.
- [ ] All interaction tests pass.

**User Stories Satisfied:** US-01 (layout), US-04 (search wired to API), US-15 (error states), US-16 (loading skeletons for existing panels)

---

### Slice 8: GainerRow and TopGainersSidebar Components

**Goal:** Build the two gainers sidebar components and wire them into the left panel in `page.tsx`.

**Depends On:** Slice 7

**Note:** This slice is parallelizable with Slice 9.

**Files:**
- `frontend/src/components/GainerRow.tsx` — create new file
- `frontend/src/components/TopGainersSidebar.tsx` — create new file
- `frontend/src/app/page.tsx` — remove stub div; import and render `TopGainersSidebar`

**Implementation Notes:**

`GainerRow` props: `{ gainer: GainerEntry; isSelected: boolean; onClick: (ticker: string) => void }`

GainerRow layout (three lines per UI spec Section 4.1):
- Wrapper: `cursor-pointer w-full mx-2 my-1 px-2.5 py-1.5 border rounded-[5px]` with conditional classes:
  - Default: `bg-[#1b2230] border-[#2a3447]`
  - Selected: `bg-[#222b3a] border-[#ff4fa6]`
  - Hover: `hover:bg-[#222b3a]` (transition)
- Top line: ticker (cyan `#63D3FF`, JetBrains Mono bold), risk badge (color per `#A93232`/`#B96A16`/`#2F7D57`/`#4A525C`), news badge (shown only when `newsToday === true`, `bg-[#1F8FB3]`), change % (green/red).
- Middle line: price (formatted: 2dp if >= $1, 4dp if < $1), volume ("Vol 2.3M" format).
- Bottom line: float | mcap | sector abbreviation | country — joined by ` | ` separator; omit entire line if all values are null.
- Sector abbreviation map: Healthcare→"Health", Technology→"Tech", Industrials→"Indust", Consumer Cyclical→"Cons Cyc", Consumer Defensive→"Cons Def", Communication Services→"Comms", Financial Services→"Financ", Basic Materials→"Materials", Real Estate→"RE", others→full name.
- Number formatting helper: `formatMillions(n)` → "2.3M" if >= 1M, "917K" if >= 1K, raw otherwise.

`TopGainersSidebar` props: `{ selectedTicker: string | null; onGainerSelect: (ticker: string) => void }`

Internal state: `gainers: GainerEntry[]`, `isLoading: boolean`, `error: string | null`, `lastUpdated: Date | null`.

Lifecycle:
- On mount: call `fetchGainers()` immediately; start `setInterval(fetchAndUpdate, 60_000)`.
- On unmount: `clearInterval`.
- Manual refresh button: `clearInterval`, call `fetchGainers()` immediately, restart `setInterval`.

States:
- Loading (initial): 5 skeleton rows (`h-14 bg-[#1b2230] rounded-[5px] mx-2 my-1 animate-pulse`).
- Loading (refresh): header shows "Loading..." replacing the count badge.
- Error: error message in `text-[#ff6b6b]` + "Retry" button in `text-[#ff4fa6]`.
- Empty (loaded but 0 gainers): "No gainers found" centered text.
- Loaded: list of `GainerRow` components.

Sidebar header: `flex items-center justify-between px-3 py-2 border-b border-[#2a3447] shrink-0`
- Title: `text-[#a78bfa] text-sm font-bold` — "Top Gainers"
- Count badge (when not loading): `text-[#9aa7c7] text-xs` — count of gainers
- Refresh button: `text-[#ff4fa6] hover:text-[#ff6fbf] text-xs p-1 rounded` — "↻"
- Loading indicator (when fetching): `text-[#9aa7c7] text-xs animate-pulse` — "Loading..."

Scrollable list area: `flex-1 overflow-y-auto`

Wire into `page.tsx`: Replace the stub div in the left panel with:
```tsx
<TopGainersSidebar
  selectedTicker={sidebarSelectedTicker}
  onGainerSelect={handleGainerSelect}
/>
```

**Tests:**
- [ ] Unit test: `GainerRow` renders ticker in cyan when `isSelected=false`; border changes to `border-[#ff4fa6]` when `isSelected=true`.
- [ ] Unit test: `GainerRow` `onClick` prop fires with the correct ticker string when clicked.
- [ ] Unit test: `GainerRow` does not render the news badge when `newsToday=false`.
- [ ] Unit test: `GainerRow` renders the news badge when `newsToday=true`.
- [ ] Unit test: `GainerRow` bottom line is hidden when all of float, mcap, sector, country are null.
- [ ] Unit test: `formatMillions(2340000)` returns "2.3M"; `formatMillions(917000)` returns "917K".
- [ ] Unit test: `TopGainersSidebar` shows 5 skeleton rows while `isLoading=true`.
- [ ] Unit test: `TopGainersSidebar` shows "No gainers found" when `gainers=[]` after load.
- [ ] Unit test: `TopGainersSidebar` shows error state when `fetchGainers` returns `{ ok: false }`.
- [ ] Integration test: sidebar auto-refetches after 60 seconds (mock `setInterval`).
- [ ] Visual check: sidebar renders in the browser with live gainer data; clicking a row loads that ticker's dilution data in the right panel.
- [ ] Visual check: selected gainer row retains highlight when right panel is loading.

**Done When:**
- [ ] `GainerRow.tsx` and `TopGainersSidebar.tsx` exist and pass type check.
- [ ] Sidebar fetches gainers on mount and every 60 seconds.
- [ ] Manual refresh button works and resets the interval.
- [ ] Clicking a gainer row triggers `loadTicker` in `page.tsx`.
- [ ] Selected row is visually distinguished.
- [ ] All unit tests pass.
- [ ] `tsc --noEmit` passes.

**User Stories Satisfied:** US-02 (AC-02), US-03 (AC-03), US-14 (AC-14), US-15 (sidebar error), US-16 (sidebar skeletons)

---

### Slice 9: New and Updated Right-Panel Components

**Goal:** Build 5 new components (ChartAnalysisBadge, GapStats, Offerings, Ownership, MgmtCommentary) and update 3 existing components (Header, InPlayDilution, OfferingAbility), then wire all of them into `page.tsx`.

**Depends On:** Slice 7

**Note:** This slice is parallelizable with Slice 8.

**Files:**
- `frontend/src/components/ChartAnalysisBadge.tsx` — create new
- `frontend/src/components/GapStats.tsx` — create new
- `frontend/src/components/Offerings.tsx` — create new
- `frontend/src/components/Ownership.tsx` — create new
- `frontend/src/components/MgmtCommentary.tsx` — create new
- `frontend/src/components/Header.tsx` — update (add ChartAnalysisBadge, stockPrice row)
- `frontend/src/components/InPlayDilution.tsx` — update (add convertibles, in-the-money color)
- `frontend/src/components/OfferingAbility.tsx` — update (parse desc string, per-segment color)
- `frontend/src/app/page.tsx` — add new components to render order

**Implementation Notes:**

**ChartAnalysisBadge** props: `{ analysis: ChartAnalysis | null }`
- Renders nothing when `analysis` is null or rating is unrecognized.
- `HISTORY_MAP`: `green → { label: "HISTORY: Strong", bg: "#2F7D57" }`, `yellow → { label: "HISTORY: Semi-Strong", bg: "#B9A816" }`, `orange → { label: "HISTORY: Mixed", bg: "#B96A16" }`, `red → { label: "HISTORY: Fader", bg: "#A93232" }`.
- Badge: `text-xs font-bold px-2.5 py-1 rounded-[5px] text-white` with inline `style={{ backgroundColor }}`.

**Header update** (props: `{ data: HeaderData | null }`):
- Row 1: ticker + `<ChartAnalysisBadge analysis={data.chartAnalysis} />` + risk badge.
- Row 2 (new): when `data.stockPrice` > 0, show formatted price (`>= $1` → 2dp, `< $1` → 4dp). Hide when null/0.
- Row 3: unchanged metadata line.
- Skeleton: add `h-6 w-20 rounded animate-pulse mt-1` for the price row.

**InPlayDilution update** (props: `{ data: InPlayDilutionData | null }`):
- Existing warrants rendering: update color logic on "Strike:" value — use `inTheMoney` boolean on each `WarrantItem` to apply `text-[#5ce08a]` (green) or `text-[#f7b731]` (orange). Previously was always `text-[#a78bfa]`.
- Add CONVERTIBLES subsection after WARRANTS: heading `text-sm font-bold text-[#f7b731] mb-2 mt-4` — "CONVERTIBLES". Only rendered when `data.convertibles.length > 0`.
- Convertible item layout: Line 1 = details; Line 2 = `Remaining: {sharesRemaining}` (in-the-money color) + `| Conv Price: {conversionPrice}` (in-the-money color) + `| Filed: {filedDate}` (muted).
- Empty state: shown only when both `warrants` and `convertibles` are empty.
- Add second skeleton row for convertibles section.

**OfferingAbility update** (props: `{ offeringAbilityDesc: string | null }`):
- Remove the old `OfferingAbilityData` prop type.
- Hide entirely when `offeringAbilityDesc` is null or empty string.
- Parse: split on `,`, trim each segment.
- Per-segment color rule (case-insensitive):
  - Contains "pending s-1" or "pending f-1": `text-[#5ce08a] font-semibold`
  - Contains "shelf capacity" or "atm capacity" or "equity line capacity" AND includes "$0.00": `text-[#ff6b6b]`
  - Contains "shelf capacity" or "atm capacity" or "equity line capacity" AND no "$0.00": `text-[#5ce08a] font-semibold`
  - All other: `text-[#eef1f8]`
- Layout: `<div className="text-sm px-3 py-1 rounded-[5px]">` per segment.

**GapStats** props: `{ rawEntries: GapStatEntry[] }`
- Hide entirely when `rawEntries.length === 0`.
- Compute all 8 statistics inside the component per the formulas in UI spec Section 4.8.
- `pctNewHighAfter11am`: parse `high_time` as ISO timestamp, extract hour in EST (UTC-5 offset). Entries where `high_time` is null or unparseable are skipped.
- Render 8 label-value rows with colors per the traffic-light rules in UI spec Section 4.8.
- Never crash on division-by-zero: use `0.0` as fallback.
- Skeleton: 1 heading skeleton + 8 row skeletons.

**Offerings** props: `{ entries: OfferingEntry[]; stockPrice: number | null }`
- Hide when `entries` is empty.
- Show up to 3 entries (slice `entries.slice(0, 3)`).
- For each entry: compute `isAtmUsed` (headline contains "ATM USED" case-insensitive) and `inTheMoney` (`sharePrice <= stockPrice && sharePrice > 0 && stockPrice > 0`).
- ATM offering display: amount in `$X.XXM` format + date.
- Regular offering display: headline + data fields with in-the-money color.
- Date always muted (`text-[#9aa7c7]`), not colored.
- Skeleton: heading + 3 skeleton cards.

**Ownership** props: `{ data: OwnershipData | null }`
- Hide when `data` is null or `data.owners.length === 0`.
- Heading row: "Ownership" + sub-heading "As of {reportedDate.slice(0, 10)}".
- Table: Owner | Title | Shares columns.
- Shares formatted with `toLocaleString()` for comma separators; colored `text-[#5ce08a]`.
- Skeleton: heading + header row + 4 data row skeletons.

**MgmtCommentary** props: `{ text: string | null }`
- Hide when `text` is null or empty string.
- No skeleton needed.
- Body: `<p className="text-sm text-[#eef1f8] leading-relaxed whitespace-pre-line">{text}</p>`

**page.tsx updates** — wire new components into the loaded/loading section per the canonical render order (Section 6 of UI spec):
1. Header (updated — passes `chartAnalysis` and `stockPrice` via `buildHeaderData`)
2. Headlines
3. RiskBadges
4. OfferingAbility (updated — passes `offeringAbilityDesc` string)
5. InPlayDilution (updated — passes convertibles and stockPrice via `buildInPlayData`)
6. Offerings (new — rendered when `dilutionData.offerings.length > 0`)
7. GapStats (new — rendered when `dilutionData.gapStats.length > 0`)
8. JMT415Notes
9. MgmtCommentary (new — rendered when `dilutionData.mgmtCommentary` is non-empty)
10. Ownership (new — rendered when `dilutionData.ownership?.owners.length > 0`)

During loading (`isLoading === true`, `dilutionData === null`): all components receive `null` or empty array and show their skeleton states. GapStats, Offerings, Ownership, MgmtCommentary are conditionally rendered only when data is loaded and non-empty (they have no skeletons by design — they either appear or don't).

**Tests:**
- [ ] Unit test: `ChartAnalysisBadge` renders nothing when `analysis=null`.
- [ ] Unit test: `ChartAnalysisBadge` renders "HISTORY: Strong" with `#2F7D57` background when `rating="green"`.
- [ ] Unit test: `ChartAnalysisBadge` renders nothing for unrecognized rating string.
- [ ] Unit test: `Header` renders stock price row when `stockPrice=1.24`; formatted as "$1.24".
- [ ] Unit test: `Header` hides stock price row when `stockPrice=null`.
- [ ] Unit test: `Header` hides stock price row when `stockPrice=0`.
- [ ] Unit test: `Header` renders price as "$0.0032" (4dp) when `stockPrice=0.0032`.
- [ ] Unit test: `OfferingAbility` renders nothing when `offeringAbilityDesc=null`.
- [ ] Unit test: `OfferingAbility` renders nothing when `offeringAbilityDesc=""`.
- [ ] Unit test: `OfferingAbility` parses comma-separated string into separate line items.
- [ ] Unit test: segment "shelf capacity $0.00M remaining" is colored red.
- [ ] Unit test: segment "ATM capacity $5.00M remaining" is colored green and semibold.
- [ ] Unit test: segment "pending s-1" is colored green and semibold.
- [ ] Unit test: `InPlayDilution` renders CONVERTIBLES subsection when convertibles array is non-empty.
- [ ] Unit test: `InPlayDilution` does not render CONVERTIBLES when array is empty.
- [ ] Unit test: warrant with `inTheMoney=true` renders strike price in `#5ce08a`.
- [ ] Unit test: warrant with `inTheMoney=false` renders strike price in `#f7b731`.
- [ ] Unit test: `GapStats` renders nothing when `rawEntries=[]`.
- [ ] Unit test: `GapStats` computes `pctClosedBelowVwap` correctly from sample entries.
- [ ] Unit test: `GapStats` shows 0.0% rather than crashing when all `market_open` values are null.
- [ ] Unit test: `Offerings` renders nothing when `entries=[]`.
- [ ] Unit test: ATM offering (headline contains "ATM USED") renders amount in green.
- [ ] Unit test: regular offering with `sharePrice <= stockPrice` renders in green.
- [ ] Unit test: regular offering with `sharePrice > stockPrice` renders in orange.
- [ ] Unit test: `Ownership` renders nothing when `data=null`.
- [ ] Unit test: `Ownership` renders nothing when `data.owners=[]`.
- [ ] Unit test: `Ownership` formats `1234567` shares as "1,234,567".
- [ ] Unit test: `MgmtCommentary` renders nothing when `text=""`.
- [ ] Unit test: `MgmtCommentary` renders the text when non-empty.
- [ ] Integration test: full page load for a ticker with all V2 data; all 10 panel positions render in correct order.
- [ ] `tsc --noEmit` passes with no errors.

**Done When:**
- [ ] All 5 new components created.
- [ ] All 3 existing components updated.
- [ ] `page.tsx` renders all 10 panels in canonical order.
- [ ] All loading skeleton states work correctly.
- [ ] All conditional-hide rules work correctly.
- [ ] All unit tests pass.
- [ ] `tsc --noEmit` passes.

**User Stories Satisfied:** US-05 (AC-05), US-06 (AC-06), US-07 (AC-07), US-08 (AC-08), US-09 (AC-09), US-10 (AC-10), US-11 (AC-11), US-12 (AC-12), US-16 (skeletons for new panels)

---

## Sequence Rules

1. Complete each slice fully (all "Done When" criteria met and tests passing) before starting a dependent slice.
2. Slices 8 and 9 may be implemented in parallel — they share no file ownership except `page.tsx`. If implemented in parallel, coordinate the final `page.tsx` edits to avoid conflicts (Slice 8 adds `TopGainersSidebar`; Slice 9 adds new right-panel components).
3. No partial slice work. If a slice is blocked, HALT and report.
4. If a HALT condition is encountered during implementation, do not skip ahead to a later slice.
5. No additional slices may be added without human approval.

---

## Deferred Work (Not This Roadmap)

The following items are explicitly out of scope for V2 and must not be implemented during this roadmap:

- **yfinance price enrichment for gainers** — TradingView scanner price data is used directly; yfinance is a post-V2 follow-up.
- **Mobile responsive design** — the layout is desktop-first; no breakpoints or touch optimizations.
- **DAS Trader / thinkorswim window scraping** — desktop-only feature; not applicable to the web app.
- **Export or download of any data panels** — not in requirements.
- **User authentication or per-user settings** — not in requirements.
- **Enterprise `/v1/registrations` endpoint rework** — the existing backend already calls it and includes its data in `offering_ability_desc`, which is now parsed client-side. No new wiring needed.
- **Polygon API / `massive_backup.py` integration** — reference only.
- **`massive_api_key` and `fmp_api_key` config fields** — already in `config.py` as stubs; leave them untouched.
- **Persistent cache (Redis, disk)** — in-memory dict is sufficient for V2.
- **Rate-limit counter / daily ticker quota tracking** — caching is the mitigation; a formal quota tracker is a post-V2 concern.

---

## File Ownership Summary

| File | Created or Modified | Slice |
|------|---------------------|-------|
| `app/core/config.py` | Modified | 1 |
| `app/services/dilution.py` | Modified | 1, 2, 4 |
| `app/models/__init__.py` | Created | 3 |
| `app/models/responses.py` | Created | 3 |
| `app/services/gainers.py` | Created | 5 |
| `app/api/v1/routes.py` | Modified | 4, 5 |
| `frontend/src/types/dilution.ts` | Modified (full rewrite) | 6 |
| `frontend/src/services/api.ts` | Created | 6 |
| `frontend/src/app/page.tsx` | Modified (full rewrite) | 7, 8 (wire), 9 (wire) |
| `frontend/src/components/GainerRow.tsx` | Created | 8 |
| `frontend/src/components/TopGainersSidebar.tsx` | Created | 8 |
| `frontend/src/components/ChartAnalysisBadge.tsx` | Created | 9 |
| `frontend/src/components/GapStats.tsx` | Created | 9 |
| `frontend/src/components/Offerings.tsx` | Created | 9 |
| `frontend/src/components/Ownership.tsx` | Created | 9 |
| `frontend/src/components/MgmtCommentary.tsx` | Created | 9 |
| `frontend/src/components/Header.tsx` | Modified | 9 |
| `frontend/src/components/InPlayDilution.tsx` | Modified | 9 |
| `frontend/src/components/OfferingAbility.tsx` | Modified | 9 |

No file is touched by more than one slice concurrently, with the exception of `page.tsx` which is written in Slice 7 and extended in Slices 8 and 9. The Slice 7 version uses stubs; the wire-up edits in 8 and 9 are additive-only and can be merged in sequence.

---

## Verification Checklist (Pre-Report)

- [x] Every backend architecture component is assigned to a slice (DilutionService cache, GainersService, Pydantic models, 5 new service methods, route handler updates).
- [x] Every frontend architecture component is assigned to a slice (TopGainersSidebar, GainerRow, GapStats, Offerings, Ownership, ChartAnalysisBadge, MgmtCommentary, Header update, InPlayDilution update, OfferingAbility update, apiService, types, page.tsx).
- [x] No circular dependencies: the dependency graph is a strict DAG.
- [x] Each slice has testable "Done When" criteria.
- [x] All file paths are concrete (no placeholders).
- [x] Deferred work is documented and will not be implemented.
