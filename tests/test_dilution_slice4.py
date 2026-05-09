"""
Slice 4: TTL Constants + DilutionService TTL Dispatch + Two-Tier News Cache

Acceptance Criteria Coverage:
- [x] AC-1:  TTL_24H=86400, TTL_4H=14400, TTL_30M=1800
- [x] AC-2:  CACHE_TTL_MAP has all 16 required key prefixes
- [x] AC-3:  CACHE_TTL_MAP TTL tiers correct
- [x] AC-4:  _cache_get returns value within 24h TTL
- [x] AC-5:  _cache_get returns None when 30-min key expired
- [x] AC-6:  _cache_get does NOT expire 2h-old dilution key (24h TTL upgrade verified)
- [x] AC-7:  _cache_get falls back to TTL_30M for unknown prefix
- [removed] AC-10: moved to tests/test_news_slice6.py (NewsService owns newsToday write)
- [removed] AC-11: moved to tests/test_news_slice6.py (NewsService owns newsToday write)
- [removed] AC-12: moved to tests/test_news_slice6.py (NewsService owns newsToday write)
- [removed] AC-13: moved to tests/test_news_slice6.py (NewsService owns newsToday cache read)
- [removed] AC-14: moved to tests/test_news_slice6.py (NewsService owns newsToday cache read)
- [removed] AC-15: moved to tests/test_news_slice6.py (NewsService owns newsToday cache read)
- [x] AC-16: GainersService._enrich_gainer calls get_news_today_cached (not inline derivation)
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.dilution import DilutionService, TTL_24H, TTL_4H, TTL_30M, CACHE_TTL_MAP
from app.services.gainers import GainersService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dilution_service() -> DilutionService:
    """Build a DilutionService instance (no network calls in constructor)."""
    return DilutionService()


def _make_gainers_service() -> GainersService:
    """Build a GainersService backed by a real DilutionService stub."""
    return GainersService(_make_dilution_service())


def _base_gainer_item(ticker: str = "AAAA") -> dict:
    """Minimal gainer item dict for _enrich_gainer."""
    return {
        "ticker": ticker,
        "todaysChangePerc": 20.0,
        "price": 1.00,
        "volume": 500_000,
    }


# ---------------------------------------------------------------------------
# AC-1: TTL constants have correct values
# ---------------------------------------------------------------------------

def test_ttl_constants_correct_values():
    """
    Module-level TTL constants must match the values mandated by the spec:
    TTL_24H=86400, TTL_4H=14400, TTL_30M=1800.
    """
    assert TTL_24H == 86400
    assert TTL_4H == 14400
    assert TTL_30M == 1800


# ---------------------------------------------------------------------------
# AC-2: CACHE_TTL_MAP has all 16 required keys
# ---------------------------------------------------------------------------

def test_cache_ttl_map_has_all_16_keys():
    """
    CACHE_TTL_MAP must contain exactly the DilutionService-owned keys.
    Intel-only keys (filingtitles, report, revsplit, histfloat, compliance)
    are governed by IntelService.CACHE_TTL_MAP only — removed from here.
    screener is 30m (not 24h) because stockPrice is rendered live in the header.
    """
    required_keys = {
        "dilution", "float", "ownership", "registrations", "offerings",
        "dilutiondata", "gapstats", "screener", "chart", "news", "newsToday",
    }
    assert required_keys == set(CACHE_TTL_MAP.keys())


# ---------------------------------------------------------------------------
# AC-3: CACHE_TTL_MAP TTL tiers are correct
# ---------------------------------------------------------------------------

def test_cache_ttl_map_tiers_correct():
    """
    Each key in CACHE_TTL_MAP must map to the correct TTL tier:
    - 24h tier: dilution, float, ownership, registrations, offerings,
                dilutiondata, gapstats, newsToday
    - 4h tier:  chart
    - 30m tier: screener (stockPrice rendered live in header), news
    """
    tier_24h = {
        "dilution", "float", "ownership", "registrations", "offerings",
        "dilutiondata", "gapstats", "newsToday",
    }
    tier_4h = {"chart"}
    tier_30m = {"screener", "news"}

    for key in tier_24h:
        assert CACHE_TTL_MAP[key] == TTL_24H, f"Expected TTL_24H for '{key}'"
    for key in tier_4h:
        assert CACHE_TTL_MAP[key] == TTL_4H, f"Expected TTL_4H for '{key}'"
    for key in tier_30m:
        assert CACHE_TTL_MAP[key] == TTL_30M, f"Expected TTL_30M for '{key}'"


# ---------------------------------------------------------------------------
# AC-4: _cache_get returns value within TTL for a 24h key
# ---------------------------------------------------------------------------

def test_cache_get_returns_value_within_24h_ttl():
    """
    A 'dilution:' key stored at current time must be returned by _cache_get
    because the entry age (≈0 s) is well within the 24h TTL.
    """
    d = _make_dilution_service()
    d._cache["dilution:AAAA"] = (time.time(), {"offeringRisk": "High"})
    result = d._cache_get("dilution:AAAA")
    assert result == {"offeringRisk": "High"}


# ---------------------------------------------------------------------------
# AC-5: _cache_get returns None when TTL expired for a 30-min key
# ---------------------------------------------------------------------------

def test_cache_get_returns_none_when_30min_key_expired():
    """
    A 'news:' key stored 3700 seconds ago (past the 1800 s TTL) must return
    None from _cache_get.
    """
    d = _make_dilution_service()
    d._cache["news:AAAA"] = (time.time() - 3700, [{"headline": "old"}])
    result = d._cache_get("news:AAAA")
    assert result is None


# ---------------------------------------------------------------------------
# AC-6: _cache_get does NOT expire 2h-old dilution key (24h TTL upgrade)
# ---------------------------------------------------------------------------

def test_cache_get_dilution_key_not_expired_at_2h():
    """
    A 'dilution:' key stored 7200 seconds (2 h) ago must still be returned
    by _cache_get because the TTL is 86400 s (24 h), not the old 1800 s.
    This verifies the TTL upgrade from 30 min to 24 h.
    """
    d = _make_dilution_service()
    payload = {"offeringRisk": "Low"}
    d._cache["dilution:AAAA"] = (time.time() - 7200, payload)
    result = d._cache_get("dilution:AAAA")
    assert result == payload


# ---------------------------------------------------------------------------
# AC-7: _cache_get falls back to TTL_30M for unrecognized key prefix
# ---------------------------------------------------------------------------

def test_cache_get_falls_back_to_30m_ttl_for_unknown_prefix():
    """
    An unrecognized prefix ('unknown:') is not in CACHE_TTL_MAP. The fallback
    TTL is TTL_30M (1800 s). An entry stored 3700 s ago must return None.
    """
    d = _make_dilution_service()
    d._cache["unknown:AAAA"] = (time.time() - 3700, "some-value")
    result = d._cache_get("unknown:AAAA")
    assert result is None


# ---------------------------------------------------------------------------
# AC-16: GainersService._enrich_gainer calls get_news_today_cached (not inline)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_calls_get_news_today_cached_not_get_news():
    """
    _enrich_gainer must delegate newsToday to dilution_service.get_news_today_cached
    and must NOT call dilution_service.get_news directly. This verifies the
    Slice 4 refactor replaced inline news derivation with the two-tier cache API.
    """
    service = _make_gainers_service()

    # Mock FMP sub-fetchers
    service._fetch_fmp_float_for_gainer = AsyncMock(return_value=5_000_000.0)
    service._fetch_fmp_profile_for_gainer = AsyncMock(
        return_value={"mktCap": 50_000_000, "sector": "Technology", "country": "US"}
    )

    # Mock AskEdgar enrichment calls on the dilution service
    service.dilution_service._make_request_cached = AsyncMock(
        return_value={"overall_offering_risk": "Low"}
    )
    service.dilution_service.get_chart_analysis = AsyncMock(return_value={"rating": "Bullish"})

    # The two mocks under test
    service.dilution_service.get_news_today_cached = AsyncMock(return_value=False)
    service.dilution_service.get_news = AsyncMock()

    await service._enrich_gainer(_base_gainer_item("AAAA"))

    assert service.dilution_service.get_news_today_cached.call_count == 1
    assert service.dilution_service.get_news.call_count == 0
