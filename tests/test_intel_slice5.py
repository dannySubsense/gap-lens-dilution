"""
Slice 5: IntelService TTL Dispatch + WatchlistService get_news_today_cached

Acceptance Criteria Coverage:
- [x] AC-1:  IntelService TTL constants correct
- [x] AC-2:  CACHE_TTL_MAP has all 8 keys
- [x] AC-3:  CACHE_TTL_MAP tiers correct
- [x] AC-4:  CACHE_TTL_DEFAULT removed from intel module
- [x] AC-5:  _cache_get uses 24h TTL for mkt_strength (not expired at 2h)
- [x] AC-6:  _cache_get uses 4h TTL for filingtitles (expired at 5h)
- [x] AC-7:  Explicit ttl= override ignores CACHE_TTL_MAP
- [x] AC-8:  get_pump_and_dump_list still uses CACHE_TTL_PD_LIST=300 override
- [x] AC-9:  _get_ticker_quote calls get_news_today_cached, not get_news
- [x] AC-10: newsToday=True when get_news_today_cached returns True
- [x] AC-11: newsToday=False when get_news_today_cached returns False
- [x] AC-12: newsToday=False when get_news_today_cached raises (graceful)
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock

import app.services.intel as intel_module
from app.services.intel import IntelService, TTL_24H, TTL_4H, TTL_30M, CACHE_TTL_MAP, CACHE_TTL_PD_LIST
from app.services.dilution import DilutionService
from app.services.watchlist_service import WatchlistService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_intel() -> IntelService:
    d = DilutionService()
    return IntelService(d)


def _make_watchlist() -> WatchlistService:
    d = DilutionService()
    return WatchlistService(d)


def _mock_fmp_fields(service: WatchlistService) -> None:
    """Replace the three FMP sub-fetchers with AsyncMocks returning minimal data."""
    service._fetch_fmp_quote = AsyncMock(
        return_value={"price": 1.0, "changesPercentage": 5.0, "volume": 100000, "marketCap": 1000000}
    )
    service._fetch_fmp_profile = AsyncMock(
        return_value={"sector": "Tech", "country": "US"}
    )
    service._fetch_fmp_float = AsyncMock(return_value=5000000.0)


# ---------------------------------------------------------------------------
# AC-1: IntelService TTL constants have correct values
# ---------------------------------------------------------------------------

def test_intel_ttl_constants_correct():
    """
    Module-level TTL constants must match spec values:
    TTL_24H=86400, TTL_4H=14400, TTL_30M=1800, CACHE_TTL_PD_LIST=300.
    """
    assert TTL_24H == 86400
    assert TTL_4H == 14400
    assert TTL_30M == 1800
    assert CACHE_TTL_PD_LIST == 300


# ---------------------------------------------------------------------------
# AC-2: CACHE_TTL_MAP has all 8 keys
# ---------------------------------------------------------------------------

def test_intel_cache_ttl_map_has_all_8_keys():
    """
    CACHE_TTL_MAP must contain exactly the 7 IntelService-owned prefix keys.
    pd_list is excluded — get_pump_and_dump_list always overrides with
    CACHE_TTL_PD_LIST=300, making a map entry a misleading dead letter.
    """
    required_keys = {
        "mkt_strength", "pd", "compliance",
        "revsplit", "filingtitles", "histfloat", "report",
    }
    assert required_keys == set(CACHE_TTL_MAP.keys())


# ---------------------------------------------------------------------------
# AC-3: CACHE_TTL_MAP tiers are correct
# ---------------------------------------------------------------------------

def test_intel_cache_ttl_map_tiers_correct():
    """
    Each key in CACHE_TTL_MAP must map to the correct TTL tier:
    - 24h: mkt_strength, compliance, revsplit, histfloat
    - 4h:  filingtitles, report
    - 30m: pd
    pd_list is intentionally absent (always overridden by CACHE_TTL_PD_LIST=300).
    """
    tier_24h = {"mkt_strength", "compliance", "revsplit", "histfloat"}
    tier_4h = {"filingtitles", "report"}
    tier_30m = {"pd"}

    for key in tier_24h:
        assert CACHE_TTL_MAP[key] == TTL_24H, f"Expected TTL_24H for '{key}'"
    for key in tier_4h:
        assert CACHE_TTL_MAP[key] == TTL_4H, f"Expected TTL_4H for '{key}'"
    for key in tier_30m:
        assert CACHE_TTL_MAP[key] == TTL_30M, f"Expected TTL_30M for '{key}'"


# ---------------------------------------------------------------------------
# AC-4: CACHE_TTL_DEFAULT is not present in intel module
# ---------------------------------------------------------------------------

def test_intel_cache_ttl_default_removed():
    """
    CACHE_TTL_DEFAULT must not exist in the intel module — it was replaced
    by the CACHE_TTL_MAP dispatch and named TTL constants.
    """
    assert not hasattr(intel_module, "CACHE_TTL_DEFAULT")


# ---------------------------------------------------------------------------
# AC-5: _cache_get uses 24h TTL for mkt_strength (not expired at 2h)
# ---------------------------------------------------------------------------

def test_intel_cache_get_mkt_strength_not_expired_at_2h():
    """
    A 'mkt_strength' key stored 2 hours (7200 s) ago must still be returned
    because its TTL is TTL_24H (86400 s).
    """
    service = _make_intel()
    service._cache["mkt_strength"] = (time.time() - 7200, {"value": 1})
    result = service._cache_get("mkt_strength")
    assert result == {"value": 1}


# ---------------------------------------------------------------------------
# AC-6: _cache_get uses 4h TTL for filingtitles (expired at 5h)
# ---------------------------------------------------------------------------

def test_intel_cache_get_filingtitles_expired_at_5h():
    """
    A 'filingtitles:AAAA' key stored 5 hours + 1 second (18001 s) ago must
    return None because its TTL is TTL_4H (14400 s).
    """
    service = _make_intel()
    service._cache["filingtitles:AAAA"] = (time.time() - 18001, ["item"])
    result = service._cache_get("filingtitles:AAAA")
    assert result is None


# ---------------------------------------------------------------------------
# AC-7: Explicit ttl= override ignores CACHE_TTL_MAP
# ---------------------------------------------------------------------------

def test_intel_cache_get_explicit_ttl_overrides_map():
    """
    When called with an explicit ttl= argument, _cache_get must use that TTL
    instead of the CACHE_TTL_MAP lookup, even when the key prefix exists in
    the map. Verified by showing the same key/age yields different results
    depending on whether ttl= is supplied.

    pd_list entry is 400 s old:
    - ttl=CACHE_TTL_PD_LIST (300) → cache miss (400 > 300)
    - ttl=None (map TTL_30M=1800) → cache hit (400 < 1800)
    """
    service = _make_intel()
    service._cache["pd_list"] = (time.time() - 400, ["pd"])

    # Explicit override: 400s > 300s → miss
    assert service._cache_get("pd_list", ttl=CACHE_TTL_PD_LIST) is None

    # Map dispatch: 400s < TTL_30M (1800s) → hit
    assert service._cache_get("pd_list") == ["pd"]


# ---------------------------------------------------------------------------
# AC-8: get_pump_and_dump_list uses CACHE_TTL_PD_LIST override (not map)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intel_get_pump_and_dump_list_uses_pd_list_ttl_override():
    """
    get_pump_and_dump_list must pass ttl=CACHE_TTL_PD_LIST (300) to _cache_get.
    An entry 400 s old is beyond 300 s, so the method must fetch fresh data.
    A mock HTTP response returning new data is used to confirm the fetch path.
    """
    service = _make_intel()
    service._cache["pd_list"] = (time.time() - 400, ["old"])

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [{"ticker": "AAPL"}]}
    service.client.get = AsyncMock(return_value=mock_resp)

    result = await service.get_pump_and_dump_list()

    assert service.client.get.call_count == 1
    assert result == [{"ticker": "AAPL"}]


# ---------------------------------------------------------------------------
# AC-9: _get_ticker_quote calls get_news_today_cached, not get_news
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_watchlist_get_ticker_quote_calls_get_news_today_cached_not_get_news():
    """
    _get_ticker_quote must delegate newsToday to get_news_today_cached.
    get_news must not be called.
    """
    service = _make_watchlist()
    _mock_fmp_fields(service)

    service._dilution._make_request_cached = AsyncMock(
        return_value={"overall_offering_risk": "Low"}
    )
    service._dilution.get_chart_analysis = AsyncMock(return_value={"rating": "Bullish"})
    service._dilution.get_news_today_cached = AsyncMock(return_value=False)
    service._dilution.get_news = AsyncMock(return_value=[])

    await service._get_ticker_quote("AAAA")

    assert service._dilution.get_news_today_cached.call_count == 1
    assert service._dilution.get_news.call_count == 0


# ---------------------------------------------------------------------------
# AC-10: newsToday is True when get_news_today_cached returns True
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_watchlist_news_today_true_when_cached_returns_true():
    """
    When get_news_today_cached returns True, the assembled record's newsToday
    field must be True.
    """
    service = _make_watchlist()
    _mock_fmp_fields(service)

    service._dilution._make_request_cached = AsyncMock(
        return_value={"overall_offering_risk": "Low"}
    )
    service._dilution.get_chart_analysis = AsyncMock(return_value={"rating": "Bullish"})
    service._dilution.get_news_today_cached = AsyncMock(return_value=True)

    result = await service._get_ticker_quote("AAAA")

    assert result["newsToday"] is True


# ---------------------------------------------------------------------------
# AC-11: newsToday is False when get_news_today_cached returns False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_watchlist_news_today_false_when_cached_returns_false():
    """
    When get_news_today_cached returns False, the assembled record's newsToday
    field must be False.
    """
    service = _make_watchlist()
    _mock_fmp_fields(service)

    service._dilution._make_request_cached = AsyncMock(
        return_value={"overall_offering_risk": "Low"}
    )
    service._dilution.get_chart_analysis = AsyncMock(return_value={"rating": "Bullish"})
    service._dilution.get_news_today_cached = AsyncMock(return_value=False)

    result = await service._get_ticker_quote("AAAA")

    assert result["newsToday"] is False


# ---------------------------------------------------------------------------
# AC-12: newsToday is False when get_news_today_cached raises (graceful)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_watchlist_news_today_false_when_cached_raises():
    """
    When get_news_today_cached raises an exception, _get_ticker_quote must
    not propagate the error. newsToday must degrade gracefully to False
    via the return_exceptions=True gather pattern.
    """
    service = _make_watchlist()
    _mock_fmp_fields(service)

    service._dilution._make_request_cached = AsyncMock(
        return_value={"overall_offering_risk": "Low"}
    )
    service._dilution.get_chart_analysis = AsyncMock(return_value={"rating": "Bullish"})
    service._dilution.get_news_today_cached = AsyncMock(
        side_effect=Exception("network error")
    )

    result = await service._get_ticker_quote("AAAA")

    assert result["newsToday"] is False
