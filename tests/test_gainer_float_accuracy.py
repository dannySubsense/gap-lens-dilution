"""
gainer-float-accuracy — Slice 4

Acceptance criteria covered:
- float on GainerRow sourced from AskEdgar /v1/float-outstanding (not FMP)
- marketCap on GainerRow sourced from float_data["market_cap_final"] (not FMP)
- _fetch_fmp_float_for_gainer method deleted (hasattr returns False)
- _make_request_cached called with "/v1/float-outstanding" at least once
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.gainers import GainerFilterParams, GainersService
from app.services.dilution import DilutionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_service() -> GainersService:
    """GainersService instance with a fresh DilutionService dependency."""
    dilution = DilutionService()
    return GainersService(dilution_service=dilution)


def _make_item(ticker: str = "TSTR") -> dict:
    return {
        "ticker": ticker,
        "todaysChangePerc": 25.0,
        "price": 5.0,
        "volume": 3_000_000,
    }


# ---------------------------------------------------------------------------
# Float accuracy test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_float_sourced_from_askedgar():
    """
    _enrich_gainer() must source float and marketCap from AskEdgar
    /v1/float-outstanding, not from FMP.

    Mocks:
    - DilutionService._make_request_cached returns float-outstanding dict when
      called with "/v1/float-outstanding"; returns None for all other endpoints.
    - DilutionService.get_chart_analysis returns None (prevent HTTP).
    - DilutionService.get_news_today_cached returns False (prevent HTTP).
    - GainersService._fetch_fmp_profile_for_gainer returns a stubbed profile
      (prevent live FMP HTTP calls).
    """
    service = _make_service()

    # Stub _make_request_cached: return float data for float-outstanding,
    # None for all other endpoints (e.g., dilution-rating).
    float_payload = {"float": 5_000_000, "market_cap_final": 25_000_000}

    async def _mock_make_request_cached(endpoint: str, ticker: str, cache_key: str):
        if endpoint == "/v1/float-outstanding":
            return float_payload
        return None

    service.dilution_service._make_request_cached = AsyncMock(
        side_effect=_mock_make_request_cached
    )

    # Stub get_chart_analysis to prevent HTTP.
    service.dilution_service.get_chart_analysis = AsyncMock(return_value=None)

    # Stub get_news_today_cached to prevent HTTP.
    service.dilution_service.get_news_today_cached = AsyncMock(return_value=False)

    # Stub _fetch_fmp_profile_for_gainer to prevent live FMP HTTP calls.
    service._fetch_fmp_profile_for_gainer = AsyncMock(
        return_value={"sector": "Technology", "country": "USA"}
    )

    item = _make_item()
    fp = GainerFilterParams()

    result = await service._enrich_gainer(item, fp)

    # float and marketCap must come from AskEdgar float-outstanding payload.
    assert result is not None, "_enrich_gainer returned None unexpectedly"
    assert result["float"] == 5_000_000, (
        f"Expected float=5_000_000 from AskEdgar, got {result['float']!r}"
    )
    assert result["marketCap"] == 25_000_000, (
        f"Expected marketCap=25_000_000 from AskEdgar market_cap_final, got {result['marketCap']!r}"
    )

    # _fetch_fmp_float_for_gainer must not exist on the service (deleted in Slice 1).
    assert not hasattr(service, "_fetch_fmp_float_for_gainer"), (
        "_fetch_fmp_float_for_gainer still present on GainersService — expected deletion"
    )

    # _make_request_cached must have been called with /v1/float-outstanding at least once.
    float_calls = [
        call
        for call in service.dilution_service._make_request_cached.call_args_list
        if call.args and call.args[0] == "/v1/float-outstanding"
    ]
    assert len(float_calls) >= 1, (
        "_make_request_cached was never called with '/v1/float-outstanding'"
    )
