"""
cache-none-sentinel — GH#5

Acceptance Criteria Coverage:
- [x] AC-1: _cache_set stores _CACHE_EMPTY (not None) when called with value=None
- [x] AC-2: _cache_get returns _CACHE_EMPTY sentinel on a within-TTL cache hit
- [x] AC-3: Public methods return None (or []) — never the raw sentinel — on sentinel cache hit
- [x] AC-4: Non-empty (real) responses are cached and returned as-is
- [x] AC-5: get_screener_data calls _cache_set with None on falsy result before early return
- [x] AC-6: get_pump_and_dump_list uses ttl=CACHE_TTL_PD_LIST on _cache_get call
- [x] AC-7: Sentinel does not leak across services (dilution._CACHE_EMPTY is not intel._CACHE_EMPTY)
- [x] AC-8: Exception paths do NOT call _cache_set

Edge-case sub-tests:
- Empty dict {} is NOT None — stored as real value, not sentinel
- Empty list [] is NOT None — stored as real value, not sentinel
- Sentinel is not importable/accessible outside the module
- TTL expiry: after TTL, a new HTTP request fires (stale sentinel does not block)
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock

import app.services.dilution as dilution_module
import app.services.intel as intel_module
from app.services.dilution import DilutionService
from app.services.intel import IntelService, CACHE_TTL_PD_LIST


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dilution() -> DilutionService:
    """Create a DilutionService with a fresh in-memory cache."""
    return DilutionService()


def _make_intel() -> IntelService:
    """Create an IntelService backed by a fresh DilutionService."""
    d = _make_dilution()
    return IntelService(d)


def _dilution_sentinel():
    """Return the module-level _CACHE_EMPTY object from dilution module."""
    return dilution_module._CACHE_EMPTY


def _intel_sentinel():
    """Return the module-level _CACHE_EMPTY object from intel module."""
    return intel_module._CACHE_EMPTY


# ---------------------------------------------------------------------------
# AC-1: _cache_set stores sentinel (not None) when called with value=None
# ---------------------------------------------------------------------------

def test_dilution_cache_set_none_stores_sentinel_not_none():
    """
    AC-1 (dilution): _cache_set(key, None) must write _CACHE_EMPTY to _cache,
    not None and not skip the write.
    """
    service = _make_dilution()
    service._cache_set("dilution:TEST", None)

    assert "dilution:TEST" in service._cache
    stored_value = service._cache["dilution:TEST"][1]
    assert stored_value is _dilution_sentinel()
    assert stored_value is not None


def test_intel_cache_set_none_stores_sentinel_not_none():
    """
    AC-1 (intel): _cache_set(key, None) must write _CACHE_EMPTY to _cache,
    not None and not skip the write.
    """
    service = _make_intel()
    service._cache_set("pd:TEST", None)

    assert "pd:TEST" in service._cache
    stored_value = service._cache["pd:TEST"][1]
    assert stored_value is _intel_sentinel()
    assert stored_value is not None


# ---------------------------------------------------------------------------
# AC-2: _cache_get returns _CACHE_EMPTY sentinel on within-TTL cache hit
# ---------------------------------------------------------------------------

def test_dilution_cache_get_returns_sentinel_within_ttl():
    """
    AC-2 (dilution): When the cache stores the sentinel at a key, _cache_get
    must return the sentinel (not None) within TTL.
    """
    service = _make_dilution()
    service._cache["chart:AAPL"] = (time.time(), _dilution_sentinel())

    result = service._cache_get("chart:AAPL")
    assert result is _dilution_sentinel()
    assert result is not None


def test_intel_cache_get_returns_sentinel_within_ttl():
    """
    AC-2 (intel): When the cache stores the sentinel at a key, _cache_get
    must return the sentinel (not None) within TTL.
    """
    service = _make_intel()
    service._cache["pd:AAPL"] = (time.time(), _intel_sentinel())

    result = service._cache_get("pd:AAPL")
    assert result is _intel_sentinel()
    assert result is not None


# ---------------------------------------------------------------------------
# AC-3: Public methods return None / [] on sentinel cache hit — never raw sentinel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_get_chart_analysis_returns_none_on_sentinel_hit():
    """
    AC-3 (dilution / dict endpoint): get_chart_analysis must return None, not
    the raw _CACHE_EMPTY sentinel, when the cache holds the sentinel.
    """
    service = _make_dilution()
    service._cache["chart:AAPL"] = (time.time(), _dilution_sentinel())

    result = await service.get_chart_analysis("AAPL")
    assert result is None
    assert result is not _dilution_sentinel()


@pytest.mark.asyncio
async def test_dilution_get_ownership_returns_none_on_sentinel_hit():
    """
    AC-3 (dilution / ownership dict endpoint): get_ownership must return None
    on sentinel cache hit.
    """
    service = _make_dilution()
    service._cache["ownership:AAPL"] = (time.time(), _dilution_sentinel())

    result = await service.get_ownership("AAPL")
    assert result is None


@pytest.mark.asyncio
async def test_dilution_get_screener_data_returns_none_on_sentinel_hit():
    """
    AC-3 (dilution / screener dict endpoint): get_screener_data must return
    None on sentinel cache hit.
    """
    service = _make_dilution()
    service._cache["screener:AAPL"] = (time.time(), _dilution_sentinel())

    result = await service.get_screener_data("AAPL")
    assert result is None


@pytest.mark.asyncio
async def test_dilution_make_request_cached_returns_none_on_sentinel_hit():
    """
    AC-3 (dilution / _make_request_cached): must return None on sentinel hit.
    """
    service = _make_dilution()
    service._cache["dilution:AAPL"] = (time.time(), _dilution_sentinel())

    result = await service._make_request_cached("/v1/dilution-rating", "AAPL", "dilution:AAPL")
    assert result is None


@pytest.mark.asyncio
async def test_dilution_make_request_list_cached_returns_empty_list_on_sentinel_hit():
    """
    AC-3 (dilution / _make_request_list_cached list endpoint): must return []
    on sentinel cache hit.
    """
    service = _make_dilution()
    service._cache["gapstats:AAPL"] = (time.time(), _dilution_sentinel())

    result = await service._make_request_list_cached(
        "/v1/gap-stats", {"ticker": "AAPL"}, "gapstats:AAPL"
    )
    assert result == []


@pytest.mark.asyncio
async def test_intel_get_pump_and_dump_returns_none_on_sentinel_hit():
    """
    AC-3 (intel / pump-and-dump dict endpoint): get_pump_and_dump must return
    None on sentinel cache hit.
    """
    service = _make_intel()
    service._cache["pd:AAPL"] = (time.time(), _intel_sentinel())

    result = await service.get_pump_and_dump("AAPL")
    assert result is None
    assert result is not _intel_sentinel()


@pytest.mark.asyncio
async def test_intel_get_market_strength_returns_none_on_sentinel_hit():
    """
    AC-3 (intel / market strength dict endpoint): get_market_strength must
    return None on sentinel cache hit.
    """
    service = _make_intel()
    service._cache["mkt_strength"] = (time.time(), _intel_sentinel())

    result = await service.get_market_strength()
    assert result is None


@pytest.mark.asyncio
async def test_intel_get_research_report_returns_none_on_sentinel_hit():
    """
    AC-3 (intel / research report dict endpoint): get_research_report must
    return None on sentinel cache hit.
    """
    service = _make_intel()
    service._cache["report:AAPL"] = (time.time(), _intel_sentinel())

    result = await service.get_research_report("AAPL")
    assert result is None


@pytest.mark.asyncio
async def test_intel_get_pump_and_dump_list_returns_empty_list_on_sentinel_hit():
    """
    AC-3 (intel / pump-and-dump list endpoint): get_pump_and_dump_list must
    return [] on sentinel cache hit.
    """
    service = _make_intel()
    service._cache["pd_list"] = (time.time(), _intel_sentinel())

    result = await service.get_pump_and_dump_list()
    assert result == []


@pytest.mark.asyncio
async def test_intel_get_nasdaq_compliance_returns_empty_list_on_sentinel_hit():
    """
    AC-3 (intel / compliance list endpoint): get_nasdaq_compliance must return
    [] on sentinel cache hit.
    """
    service = _make_intel()
    service._cache["compliance:AAPL"] = (time.time(), _intel_sentinel())

    result = await service.get_nasdaq_compliance("AAPL")
    assert result == []


# ---------------------------------------------------------------------------
# AC-4: Non-empty (real) responses are cached and returned as-is
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_get_chart_analysis_caches_and_returns_real_data():
    """
    AC-4 (dilution): When AskEdgar returns real data, get_chart_analysis caches
    it and returns the same dict. A second call must not issue another HTTP request.
    """
    service = _make_dilution()
    real_data = {"rating": "Bullish", "score": 9}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [real_data]}
    service.client.get = AsyncMock(return_value=mock_resp)

    result1 = await service.get_chart_analysis("AAPL")
    result2 = await service.get_chart_analysis("AAPL")

    assert result1 == real_data
    assert result2 == real_data
    # Only one HTTP call — second call served from cache
    assert service.client.get.call_count == 1


@pytest.mark.asyncio
async def test_intel_get_pump_and_dump_caches_and_returns_real_data():
    """
    AC-4 (intel): When AskEdgar returns real data, get_pump_and_dump caches it
    and a second call does not fire another HTTP request.
    """
    service = _make_intel()
    real_data = {"ticker": "AAPL", "score": 7}

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [real_data]}
    service.client.get = AsyncMock(return_value=mock_resp)

    result1 = await service.get_pump_and_dump("AAPL")
    result2 = await service.get_pump_and_dump("AAPL")

    assert result1 == real_data
    assert result2 == real_data
    assert service.client.get.call_count == 1


# ---------------------------------------------------------------------------
# AC-5: get_screener_data calls _cache_set with None on falsy result (early return path)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_get_screener_data_sets_sentinel_on_falsy_result():
    """
    AC-5: When _make_request returns a falsy dict ({}), get_screener_data must
    call _cache_set with None so the sentinel is stored and subsequent calls
    skip the live request.
    """
    service = _make_dilution()

    # _make_request returns empty dict (falsy)
    service._make_request = AsyncMock(return_value={})

    result = await service.get_screener_data("AAPL")

    assert result is None
    # Sentinel must now be in cache for this key
    assert "screener:AAPL" in service._cache
    cached_value = service._cache["screener:AAPL"][1]
    assert cached_value is _dilution_sentinel()


@pytest.mark.asyncio
async def test_dilution_get_screener_data_no_http_on_second_call_after_empty():
    """
    AC-5 (corollary): After an empty result is sentinelled, a second call must
    not make another HTTP request.
    """
    service = _make_dilution()

    call_count = 0

    async def fake_make_request(endpoint, ticker):
        nonlocal call_count
        call_count += 1
        return {}

    service._make_request = fake_make_request

    await service.get_screener_data("AAPL")
    assert call_count == 1

    await service.get_screener_data("AAPL")
    # No second HTTP call — sentinel in cache blocks it
    assert call_count == 1


# ---------------------------------------------------------------------------
# AC-6: get_pump_and_dump_list uses ttl=CACHE_TTL_PD_LIST on _cache_get call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intel_get_pump_and_dump_list_uses_pd_list_ttl_override():
    """
    AC-6: get_pump_and_dump_list must pass ttl=CACHE_TTL_PD_LIST (300 s) to
    _cache_get. A cache entry that is 400 s old exceeds 300 s and must trigger
    a fresh HTTP request, even though CACHE_TTL_MAP['pd'] (TTL_30M=1800 s)
    would not yet have expired.
    """
    service = _make_intel()
    # Store an entry 400 s old (older than CACHE_TTL_PD_LIST=300 but younger than TTL_30M=1800)
    service._cache["pd_list"] = (time.time() - 400, ["stale_entry"])

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [{"ticker": "FRESH"}]}
    service.client.get = AsyncMock(return_value=mock_resp)

    result = await service.get_pump_and_dump_list()

    # Fresh fetch was made because ttl=300 expired
    assert service.client.get.call_count == 1
    assert result == [{"ticker": "FRESH"}]


# ---------------------------------------------------------------------------
# AC-7: Sentinel does not leak across services
# ---------------------------------------------------------------------------

def test_sentinel_objects_are_distinct_across_services():
    """
    AC-7: dilution._CACHE_EMPTY and intel._CACHE_EMPTY must be separate
    object() instances. Leaking one into the other's cache would create
    cross-module confusion.
    """
    assert _dilution_sentinel() is not _intel_sentinel()


def test_sentinel_not_accessible_as_class_attribute():
    """
    AC-7 (corollary): The sentinel must not appear on DilutionService or
    IntelService as a class or instance attribute (must remain module-private).
    """
    d = _make_dilution()
    i = _make_intel()

    assert not hasattr(d, "_CACHE_EMPTY"), "DilutionService must not expose _CACHE_EMPTY as instance attribute"
    assert not hasattr(i, "_CACHE_EMPTY"), "IntelService must not expose _CACHE_EMPTY as instance attribute"
    assert not hasattr(DilutionService, "_CACHE_EMPTY"), "DilutionService class must not expose _CACHE_EMPTY"
    assert not hasattr(IntelService, "_CACHE_EMPTY"), "IntelService class must not expose _CACHE_EMPTY"


# ---------------------------------------------------------------------------
# AC-8: Exception paths do NOT call _cache_set
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_get_chart_analysis_exception_does_not_cache():
    """
    AC-8 (dilution): When the HTTP call raises an exception, get_chart_analysis
    must return None and must not write anything to the cache.
    """
    service = _make_dilution()
    service.client.get = AsyncMock(side_effect=Exception("network error"))

    result = await service.get_chart_analysis("AAPL")

    assert result is None
    assert "chart:AAPL" not in service._cache


@pytest.mark.asyncio
async def test_dilution_get_ownership_exception_does_not_cache():
    """
    AC-8 (dilution / ownership): When the HTTP call raises, get_ownership
    must return None without writing to the cache.
    """
    service = _make_dilution()
    service.client.get = AsyncMock(side_effect=Exception("timeout"))

    result = await service.get_ownership("AAPL")

    assert result is None
    assert "ownership:AAPL" not in service._cache


@pytest.mark.asyncio
async def test_intel_get_pump_and_dump_exception_does_not_cache():
    """
    AC-8 (intel): When the HTTP call raises, get_pump_and_dump must return None
    without writing to the cache.
    """
    service = _make_intel()
    service.client.get = AsyncMock(side_effect=Exception("network error"))

    result = await service.get_pump_and_dump("AAPL")

    assert result is None
    assert "pd:AAPL" not in service._cache


@pytest.mark.asyncio
async def test_intel_get_research_report_exception_does_not_cache():
    """
    AC-8 (intel / research report): When the HTTP call raises, get_research_report
    must return None without writing to the cache.
    """
    service = _make_intel()
    service.client.get = AsyncMock(side_effect=Exception("timeout"))

    result = await service.get_research_report("AAPL")

    assert result is None
    assert "report:AAPL" not in service._cache


# ---------------------------------------------------------------------------
# Edge case: Empty dict {} is NOT None — stored as real value, not sentinel
# ---------------------------------------------------------------------------

def test_dilution_cache_set_empty_dict_is_not_sentinelled():
    """
    Edge case: _cache_set({}) must store the real empty dict, not the sentinel.
    {} is falsy in Python but is NOT None.
    """
    service = _make_dilution()
    service._cache_set("dilution:TEST", {})

    stored_value = service._cache["dilution:TEST"][1]
    assert stored_value == {}
    assert stored_value is not _dilution_sentinel()


def test_intel_cache_set_empty_dict_is_not_sentinelled():
    """
    Edge case: _cache_set({}) must store the real empty dict in intel service.
    """
    service = _make_intel()
    service._cache_set("pd:TEST", {})

    stored_value = service._cache["pd:TEST"][1]
    assert stored_value == {}
    assert stored_value is not _intel_sentinel()


# ---------------------------------------------------------------------------
# Edge case: Empty list [] is NOT None — stored as real value, not sentinel
# ---------------------------------------------------------------------------

def test_dilution_cache_set_empty_list_is_not_sentinelled():
    """
    Edge case: _cache_set([]) must store the real empty list, not the sentinel.
    [] is falsy in Python but is NOT None.
    """
    service = _make_dilution()
    service._cache_set("gapstats:TEST", [])

    stored_value = service._cache["gapstats:TEST"][1]
    assert stored_value == []
    assert stored_value is not _dilution_sentinel()


def test_intel_cache_set_empty_list_is_not_sentinelled():
    """
    Edge case: _cache_set([]) must store the real empty list in intel service.
    """
    service = _make_intel()
    service._cache_set("compliance:TEST", [])

    stored_value = service._cache["compliance:TEST"][1]
    assert stored_value == []
    assert stored_value is not _intel_sentinel()


# ---------------------------------------------------------------------------
# Edge case: TTL expiry — after TTL a new HTTP call fires (stale sentinel does not block)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_get_chart_analysis_fires_after_sentinel_ttl_expiry():
    """
    Edge case: A sentinel entry stored beyond the TTL window must be treated as
    a cache miss. get_chart_analysis must fire a fresh HTTP request and NOT
    return None from the stale sentinel.
    """
    service = _make_dilution()
    # chart prefix TTL is TTL_24H (86400). Store sentinel with age > TTL.
    service._cache["chart:AAPL"] = (time.time() - 86401, _dilution_sentinel())

    real_data = {"rating": "Bearish"}
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [real_data]}
    service.client.get = AsyncMock(return_value=mock_resp)

    result = await service.get_chart_analysis("AAPL")

    assert service.client.get.call_count == 1
    assert result == real_data


@pytest.mark.asyncio
async def test_intel_get_pump_and_dump_fires_after_sentinel_ttl_expiry():
    """
    Edge case: A sentinel entry stored beyond pd TTL (TTL_30M=1800 s) must be
    treated as a cache miss. get_pump_and_dump must fire a fresh HTTP request.
    """
    service = _make_intel()
    # pd prefix TTL is TTL_30M (1800). Store sentinel with age > TTL.
    service._cache["pd:AAPL"] = (time.time() - 1801, _intel_sentinel())

    real_data = {"ticker": "AAPL", "score": 3}
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [real_data]}
    service.client.get = AsyncMock(return_value=mock_resp)

    result = await service.get_pump_and_dump("AAPL")

    assert service.client.get.call_count == 1
    assert result == real_data


# ---------------------------------------------------------------------------
# No-second-HTTP-call verification for chart analysis and pump-and-dump (US-3)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_get_chart_analysis_no_http_on_second_call_when_none():
    """
    US-3 / AC-3: When get_chart_analysis returns None (empty results) on first
    call, the second call within TTL must not issue another HTTP request.
    """
    service = _make_dilution()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": []}  # empty — results[0] gives None
    service.client.get = AsyncMock(return_value=mock_resp)

    result1 = await service.get_chart_analysis("AAPL")
    result2 = await service.get_chart_analysis("AAPL")

    assert result1 is None
    assert result2 is None
    assert service.client.get.call_count == 1


@pytest.mark.asyncio
async def test_intel_get_pump_and_dump_no_http_on_second_call_when_none():
    """
    US-3 / AC-3: When get_pump_and_dump returns None (empty results) on first
    call, the second call within TTL must not issue another HTTP request.
    """
    service = _make_intel()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": []}  # empty — results[0] gives None
    service.client.get = AsyncMock(return_value=mock_resp)

    result1 = await service.get_pump_and_dump("AAPL")
    result2 = await service.get_pump_and_dump("AAPL")

    assert result1 is None
    assert result2 is None
    assert service.client.get.call_count == 1
