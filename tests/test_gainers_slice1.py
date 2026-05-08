"""
Slice 1: GainersService FMP Float Sub-Fetcher + Enrichment Cache Tests

Acceptance Criteria Coverage:
- [x] AC-1:  _fmp_enrich_cache_set does NOT store None
- [x] AC-2:  _fmp_enrich_cache_set DOES store non-None values
- [x] AC-3:  _fmp_enrich_cache_get returns None on cache miss
- [x] AC-4:  _fmp_enrich_cache_get returns cached value on hit within TTL
- [x] AC-5:  _fmp_enrich_cache_get returns None when TTL expired
- [x] AC-6:  _fetch_fmp_float_for_gainer returns positive float on valid 200 + floatShares
- [x] AC-7:  _fetch_fmp_float_for_gainer returns None when HTTP status != 200 (429)
- [x] AC-8:  _fetch_fmp_float_for_gainer returns None when response list is empty
- [x] AC-9:  _fetch_fmp_float_for_gainer returns None when floatShares is 0
- [x] AC-10: _fetch_fmp_float_for_gainer returns None when floatShares is None
- [x] AC-11: _fetch_fmp_float_for_gainer returns None (does not raise) on HTTP exception
- [x] AC-12: FMP_ENRICH_TTL class constant equals 300
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.dilution import DilutionService
from app.services.gainers import GainersService


def _make_service() -> GainersService:
    """Build a GainersService with a minimal DilutionService stub."""
    dilution_service = DilutionService()
    return GainersService(dilution_service)


def _fmp_float_response(status_code: int, body) -> MagicMock:
    """Build a MagicMock httpx response for the FMP shares_float endpoint."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    return resp


# ---------------------------------------------------------------------------
# AC-1: _fmp_enrich_cache_set does NOT store None
# ---------------------------------------------------------------------------

def test_fmp_enrich_cache_set_none_not_stored():
    """
    Passing None to _fmp_enrich_cache_set must leave the key absent from the
    internal _fmp_enrich_cache dict (mirrors _cache_set contract in DilutionService).
    """
    service = _make_service()
    service._fmp_enrich_cache_set("float:AAAA", None)
    assert "float:AAAA" not in service._fmp_enrich_cache


# ---------------------------------------------------------------------------
# AC-2: _fmp_enrich_cache_set DOES store non-None values
# ---------------------------------------------------------------------------

def test_fmp_enrich_cache_set_stores_non_none():
    """
    Passing a non-None value to _fmp_enrich_cache_set must result in the key
    being present in _fmp_enrich_cache.
    """
    service = _make_service()
    service._fmp_enrich_cache_set("float:BBBB", 5_000_000.0)
    assert "float:BBBB" in service._fmp_enrich_cache


# ---------------------------------------------------------------------------
# AC-3: _fmp_enrich_cache_get returns None on cache miss
# ---------------------------------------------------------------------------

def test_fmp_enrich_cache_get_miss_returns_none():
    """
    _fmp_enrich_cache_get on a key that was never set must return None.
    """
    service = _make_service()
    result = service._fmp_enrich_cache_get("float:CCCC")
    assert result is None


# ---------------------------------------------------------------------------
# AC-4: _fmp_enrich_cache_get returns the cached value on hit within TTL
# ---------------------------------------------------------------------------

def test_fmp_enrich_cache_get_hit_within_ttl():
    """
    _fmp_enrich_cache_get must return the stored value when the entry is within
    the FMP_ENRICH_TTL window.
    """
    service = _make_service()
    service._fmp_enrich_cache_set("float:DDDD", 12_500_000.0)
    result = service._fmp_enrich_cache_get("float:DDDD")
    assert result == 12_500_000.0


# ---------------------------------------------------------------------------
# AC-5: _fmp_enrich_cache_get returns None when TTL expired
# ---------------------------------------------------------------------------

def test_fmp_enrich_cache_get_expired_returns_none():
    """
    _fmp_enrich_cache_get must return None when the entry is older than
    FMP_ENRICH_TTL (300 s). Mocking time.time() to simulate expiry.
    """
    service = _make_service()

    # Plant an entry timestamped at t=1000
    service._fmp_enrich_cache["float:EEEE"] = (1000.0, 99_000_000.0)

    # Advance time past TTL: 1000 + 300 + 1 = 1301
    with patch("app.services.gainers.time.time", return_value=1301.0):
        result = service._fmp_enrich_cache_get("float:EEEE")

    assert result is None


# ---------------------------------------------------------------------------
# AC-6: _fetch_fmp_float_for_gainer returns positive float on valid 200 + floatShares
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_float_valid_200_returns_float():
    """
    When the FMP /api/v4/shares_float endpoint returns HTTP 200 with a
    non-zero floatShares value, _fetch_fmp_float_for_gainer returns that value
    as a positive float.
    """
    service = _make_service()

    mock_resp = _fmp_float_response(200, [{"floatShares": 8_000_000.0}])
    service._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_float_for_gainer("AAAA")

    assert result == 8_000_000.0
    assert result > 0


# ---------------------------------------------------------------------------
# AC-7: _fetch_fmp_float_for_gainer returns None when HTTP status != 200 (429)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_float_429_returns_none():
    """
    When the FMP endpoint returns HTTP 429 (rate limit), _fetch_fmp_float_for_gainer
    must return None without raising. No retry.
    """
    service = _make_service()

    mock_resp = _fmp_float_response(429, None)
    service._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_float_for_gainer("BBBB")

    assert result is None


# ---------------------------------------------------------------------------
# AC-8: _fetch_fmp_float_for_gainer returns None when response list is empty
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_float_empty_list_returns_none():
    """
    When the FMP endpoint returns HTTP 200 but an empty list body,
    _fetch_fmp_float_for_gainer must return None.
    """
    service = _make_service()

    mock_resp = _fmp_float_response(200, [])
    service._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_float_for_gainer("CCCC")

    assert result is None


# ---------------------------------------------------------------------------
# AC-9: _fetch_fmp_float_for_gainer returns None when floatShares is 0
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_float_zero_float_shares_returns_none():
    """
    When floatShares is 0 in the FMP response, _fetch_fmp_float_for_gainer
    must return None (treat 0 as absent, matching WatchlistService behaviour).
    """
    service = _make_service()

    mock_resp = _fmp_float_response(200, [{"floatShares": 0}])
    service._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_float_for_gainer("DDDD")

    assert result is None


# ---------------------------------------------------------------------------
# AC-10: _fetch_fmp_float_for_gainer returns None when floatShares is None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_float_none_float_shares_returns_none():
    """
    When the FMP response contains a record but floatShares is explicitly None,
    _fetch_fmp_float_for_gainer must return None.
    """
    service = _make_service()

    mock_resp = _fmp_float_response(200, [{"floatShares": None}])
    service._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_float_for_gainer("EEEE")

    assert result is None


# ---------------------------------------------------------------------------
# AC-11: _fetch_fmp_float_for_gainer returns None (does not raise) on exception
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_float_exception_returns_none():
    """
    When an exception occurs during the HTTP call (e.g. network timeout),
    _fetch_fmp_float_for_gainer must return None instead of propagating the
    exception to the caller.
    """
    service = _make_service()

    service._http.get = AsyncMock(side_effect=Exception("network timeout"))

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_float_for_gainer("FFFF")

    assert result is None


# ---------------------------------------------------------------------------
# AC-12: FMP_ENRICH_TTL class constant equals 300
# ---------------------------------------------------------------------------

def test_fmp_enrich_ttl_constant_is_300():
    """
    GainersService.FMP_ENRICH_TTL must equal 300 (5-minute TTL for the gainer
    FMP enrichment cache, as defined in the spec).
    """
    assert GainersService.FMP_ENRICH_TTL == 300
