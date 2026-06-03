"""
Slice 4: get_dilution_data_v2 Tests

Acceptance Criteria Coverage:
- [x] AC1: Returns all required top-level keys for a valid ticker
- [x] AC2: Graceful degradation when a sub-call (gap-stats) raises an Exception
- [x] AC3: mgmtCommentary is mapped from dilution-rating mgmt_commentary field
- [x] AC4: 4x price filter excludes warrants whose exercise_price exceeds 4x stock price
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.dilution import DilutionService


def _make_ok_response(payload: dict) -> MagicMock:
    """Build a synchronous-json MagicMock that _make_request will accept."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = payload
    return resp


# ---------------------------------------------------------------------------
# Helpers: reusable valid payloads
# ---------------------------------------------------------------------------

DILUTION_RATING_PAYLOAD = {
    "results": [{
        "overall_offering_risk": "Low",
        "offering_ability": "High",
        "offering_ability_desc": "desc",
        "dilution": "Low",
        "dilution_desc": "desc",
        "offering_frequency": "Rare",
        "cash_need": "Low",
        "cash_need_desc": "desc",
        "cash_remaining_months": 24,
        "cash_burn": 500000,
        "estimated_cash": 10000000,
        "warrant_exercise": "Low",
        "warrant_exercise_desc": "desc",
        "mgmt_commentary": "No commentary",
    }]
}

FLOAT_OUTSTANDING_PAYLOAD = {
    "results": [{
        "float": 5000000,
        "outstanding": 10000000,
        "market_cap_final": 50000000,
        "industry": "Biotech",
        "sector": "Healthcare",
        "country": "USA",
        "insider_percent": 0.10,
        "institutions_percent": 0.30,
    }]
}

SCREENER_PAYLOAD = {
    "results": [{"price": 5.0}]
}

EMPTY_LIST_PAYLOAD = {"results": []}


# ---------------------------------------------------------------------------
# Test 1: all required top-level keys are present
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_v2_returns_all_fields():
    """get_dilution_data_v2 returns a dict containing all required V2 keys."""
    service = DilutionService()

    async_get = AsyncMock(return_value=_make_ok_response(EMPTY_LIST_PAYLOAD))

    # Override specific endpoints with their real payloads
    async def smart_get(url, **kwargs):
        params = kwargs.get("params", {})
        ticker_param = params.get("ticker", "")
        if "dilution-rating" in url:
            return _make_ok_response(DILUTION_RATING_PAYLOAD)
        if "float-outstanding" in url:
            return _make_ok_response(FLOAT_OUTSTANDING_PAYLOAD)
        if "screener" in url:
            return _make_ok_response(SCREENER_PAYLOAD)
        # gap-stats, offerings, ownership, chart, news, registrations, dilution-data
        return _make_ok_response(EMPTY_LIST_PAYLOAD)

    service.client.get = smart_get

    result = await service.get_dilution_data_v2("TEST")

    required_keys = [
        "ticker", "gapStats", "offerings", "ownership", "chartAnalysis",
        "stockPrice", "mgmtCommentary", "warrants", "convertibles",
        "news", "offeringRisk",
    ]
    for key in required_keys:
        assert key in result, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# Test 2: graceful degradation — gap-stats raises, result still returned
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_v2_graceful_degradation():
    """
    When get_gap_stats raises an Exception, get_dilution_data_v2 still
    returns a result (no exception propagated) and gapStats is empty.
    """
    service = DilutionService()

    async def smart_get(url, **kwargs):
        if "dilution-rating" in url:
            return _make_ok_response(DILUTION_RATING_PAYLOAD)
        if "float-outstanding" in url:
            return _make_ok_response(FLOAT_OUTSTANDING_PAYLOAD)
        if "screener" in url:
            return _make_ok_response(SCREENER_PAYLOAD)
        return _make_ok_response(EMPTY_LIST_PAYLOAD)

    service.client.get = smart_get

    # Patch get_gap_stats to raise
    with patch.object(service, "get_gap_stats", new_callable=AsyncMock, side_effect=Exception("gap-stats down")):
        result = await service.get_dilution_data_v2("TEST")

    assert isinstance(result, dict), "Expected a dict result, not an exception"
    assert result.get("gapStats") in ([], None, {}), (
        f"Expected gapStats to be empty on failure, got: {result.get('gapStats')}"
    )


# ---------------------------------------------------------------------------
# Test 3: mgmtCommentary is mapped from mgmt_commentary
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_v2_mgmt_commentary_extracted():
    """mgmtCommentary in the result equals the mgmt_commentary from dilution-rating."""
    service = DilutionService()

    custom_dilution_payload = {
        "results": [{
            "overall_offering_risk": "Low",
            "mgmt_commentary": "Test commentary",
        }]
    }

    async def smart_get(url, **kwargs):
        if "dilution-rating" in url:
            return _make_ok_response(custom_dilution_payload)
        if "float-outstanding" in url:
            return _make_ok_response(FLOAT_OUTSTANDING_PAYLOAD)
        if "screener" in url:
            return _make_ok_response(SCREENER_PAYLOAD)
        return _make_ok_response(EMPTY_LIST_PAYLOAD)

    service.client.get = smart_get

    result = await service.get_dilution_data_v2("TEST")

    assert result["mgmtCommentary"] == "Test commentary"


# ---------------------------------------------------------------------------
# Test 4: 4x price filter for warrants
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_v2_4x_filter_warrants():
    """
    Warrants whose exercise_price > 4 * stock_price are excluded.
    Stock price = $5 → threshold = $20.
    Warrant at $25 is excluded; warrant at $10 is included.
    """
    service = DilutionService()

    # dilution-data returns two warrants: one above 4x, one within 4x
    dilution_data_payload = {
        "results": [
            {
                "warrants_remaining": 100000,
                "warrants_exercise_price": 25.0,   # 25 > 20 → should be filtered OUT
                "registered": "Registered",
                "filed_at": "2020-01-01T00:00:00Z",
            },
            {
                "warrants_remaining": 200000,
                "warrants_exercise_price": 10.0,   # 10 <= 20 → should be INCLUDED
                "registered": "Registered",
                "filed_at": "2020-01-01T00:00:00Z",
            },
        ]
    }

    async def smart_get(url, **kwargs):
        if "dilution-rating" in url:
            return _make_ok_response(DILUTION_RATING_PAYLOAD)
        if "float-outstanding" in url:
            return _make_ok_response(FLOAT_OUTSTANDING_PAYLOAD)
        if "screener" in url:
            return _make_ok_response(SCREENER_PAYLOAD)   # price = 5.0, threshold = 20
        if "dilution-data" in url:
            return _make_ok_response(dilution_data_payload)
        return _make_ok_response(EMPTY_LIST_PAYLOAD)

    service.client.get = smart_get

    result = await service.get_dilution_data_v2("TEST")

    warrant_prices = [w.get("warrants_exercise_price") for w in result["warrants"]]
    assert 10.0 in warrant_prices, "Expected $10 warrant to be included"
    assert 25.0 not in warrant_prices, "Expected $25 warrant to be excluded (above 4x threshold)"
    assert len(result["warrants"]) == 1
