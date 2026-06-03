"""
Slice 1: GainersService FMP Enrichment Cache Tests

Float is now sourced from AskEdgar float-outstanding (not a per-gainer FMP float call).
The _fetch_fmp_float_for_gainer method was removed in the gainer-float-accuracy sprint.
FMP profile (_fetch_fmp_profile_for_gainer) supplies sector/country only.

Acceptance Criteria Coverage:
- [x] AC-1:  _fmp_enrich_cache_set does NOT store None
- [x] AC-2:  _fmp_enrich_cache_set DOES store non-None values
- [x] AC-3:  _fmp_enrich_cache_get returns None on cache miss
- [x] AC-4:  _fmp_enrich_cache_get returns cached value on hit within TTL
- [x] AC-5:  _fmp_enrich_cache_get returns None when TTL expired
- [x] AC-12: FMP_ENRICH_TTL class constant equals 300
- [removed] AC-6 through AC-11: _fetch_fmp_float_for_gainer — method removed, tests deleted
"""

import time
import pytest
from unittest.mock import MagicMock, patch
from app.services.dilution import DilutionService
from app.services.gainers import GainersService


def _make_service() -> GainersService:
    """Build a GainersService with a minimal DilutionService stub."""
    dilution_service = DilutionService()
    return GainersService(dilution_service)


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
# AC-12: FMP_ENRICH_TTL class constant equals 300
# ---------------------------------------------------------------------------

def test_fmp_enrich_ttl_constant_is_300():
    """
    GainersService.FMP_ENRICH_TTL must equal 300 (5-minute TTL for the gainer
    FMP enrichment cache, as defined in the spec).
    """
    assert GainersService.FMP_ENRICH_TTL == 300
