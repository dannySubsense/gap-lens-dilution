"""
Slice 5: GainersService Tests

Acceptance Criteria Coverage:
- [x] AC1: get_gainers() returns a list of enriched entries with required fields
- [x] AC2: TradingView is called only once when get_gainers() is called twice within 60s
- [x] AC3: get_gainers() returns [] when TradingView raises an exception
"""

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.dilution import DilutionService
from app.services.gainers import GainersService


def _tv_response(rows: list) -> MagicMock:
    """Build a MagicMock TradingView response with synchronous .json()."""
    resp = MagicMock()
    resp.json.return_value = {"data": rows}
    return resp


def _tv_row(ticker: str, change_pct: float) -> dict:
    """Build a minimal TradingView data row."""
    # d: [name, close, premarket_change, premarket_change_abs,
    #     premarket_close, premarket_volume, volume, market_cap_basic]
    return {"d": [ticker, 5.0, change_pct, 1.0, 5.0, 100000, 200000, 10000000]}


# ---------------------------------------------------------------------------
# Test 1: get_gainers returns a list with required fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gainers_returns_list():
    """
    get_gainers() returns a list of 2 enriched entries with ticker,
    todaysChangePerc, and risk fields when TradingView returns 2 valid gainers.
    """
    dilution_service = DilutionService()

    # Mock DilutionService enrichment calls to return safe defaults
    dilution_service._make_request_cached = AsyncMock(return_value={"overall_offering_risk": "Low"})
    dilution_service.get_chart_analysis = AsyncMock(return_value=None)
    dilution_service.get_news = AsyncMock(return_value=[])

    service = GainersService(dilution_service)

    tv_resp = _tv_response([
        _tv_row("AAAA", 20.0),
        _tv_row("BBBB", 18.0),
    ])
    service._http.post = AsyncMock(return_value=tv_resp)

    result = await service.get_gainers()

    assert isinstance(result, list)
    assert len(result) == 2
    for entry in result:
        assert "ticker" in entry
        assert "todaysChangePerc" in entry
        assert "risk" in entry


# ---------------------------------------------------------------------------
# Test 2: second call within 60s is served from cache (TradingView called once)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gainers_cache_60s():
    """
    Calling get_gainers() twice within 60 seconds results in only one
    POST to TradingView; the second call is served from cache.
    """
    dilution_service = DilutionService()
    dilution_service._make_request_cached = AsyncMock(return_value={"overall_offering_risk": "Medium"})
    dilution_service.get_chart_analysis = AsyncMock(return_value=None)
    dilution_service.get_news = AsyncMock(return_value=[])

    service = GainersService(dilution_service)

    tv_resp = _tv_response([_tv_row("CCCC", 25.0)])
    mock_post = AsyncMock(return_value=tv_resp)
    service._http.post = mock_post

    first = await service.get_gainers()
    second = await service.get_gainers()

    assert first == second
    mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# Test 3: TradingView exception causes get_gainers to return []
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gainers_error_returns_empty():
    """
    When the TradingView POST raises an exception, get_gainers() returns
    an empty list rather than propagating the error.
    """
    dilution_service = DilutionService()
    service = GainersService(dilution_service)

    service._http.post = AsyncMock(side_effect=Exception("TradingView unreachable"))

    result = await service.get_gainers()

    assert result == []
