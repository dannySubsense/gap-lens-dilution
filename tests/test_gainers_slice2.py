"""
Slice 2: FMP Profile Sub-Fetcher + Rewritten _enrich_gainer Tests

Acceptance Criteria Coverage:
- [x] AC-1:  _fetch_fmp_profile_for_gainer returns dict with sector/country/mktCap on valid 200
- [x] AC-2:  _fetch_fmp_profile_for_gainer returns None on HTTP 429
- [x] AC-3:  _fetch_fmp_profile_for_gainer returns None when response list is empty
- [x] AC-4:  _fetch_fmp_profile_for_gainer returns None on exception (does not raise)
- [x] AC-5:  _enrich_gainer never calls dilution_service._make_request_cached with /enterprise/v1/float-outstanding
- [x] AC-6:  float field comes from _fetch_fmp_float_for_gainer (mocked to 5_000_000.0)
- [x] AC-7:  marketCap comes from FMP profile mktCap field
- [x] AC-8:  sector and country come from FMP profile
- [x] AC-9:  FMP enrichment cache hit path — _fetch_fmp_float_for_gainer called only once for two calls
- [x] AC-10: When FMP float returns None, entry["float"] is None (no crash)
- [x] AC-11: When FMP profile returns None, sector/country/marketCap are all None (no crash)
- [x] AC-12: risk comes from dilution_service._make_request_cached result overall_offering_risk
- [x] AC-13: chartRating comes from dilution_service.get_chart_analysis result rating
- [x] AC-14: newsToday is True when news list contains 8-K item with today's ET date
- [x] AC-15: newsToday is False when news list is empty
- [x] AC-16: ticker in result is uppercased
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.dilution import DilutionService
from app.services.gainers import GainersService

_UNSET = object()  # sentinel — distinguishes "use default" from explicit None


def _make_service() -> GainersService:
    """Build a GainersService with a minimal DilutionService stub."""
    dilution_service = DilutionService()
    return GainersService(dilution_service)


def _fmp_profile_response(status_code: int, body) -> MagicMock:
    """Build a MagicMock httpx response for the FMP profile endpoint."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    return resp


def _base_item(ticker: str = "AAAA") -> dict:
    """Build a minimal gainer item dict for _enrich_gainer."""
    return {
        "ticker": ticker,
        "todaysChangePerc": 25.0,
        "price": 1.50,
        "volume": 1_000_000,
    }


def _setup_enrich_mocks(
    service: GainersService,
    fmp_float=5_000_000.0,
    fmp_profile=_UNSET,
    dilution_data=_UNSET,
    chart_data=_UNSET,
    news=_UNSET,
) -> None:
    """
    Patch the three sub-calls used by _enrich_gainer with AsyncMock defaults.
    Pass explicit None to simulate a sub-fetcher returning None (e.g. 429/empty).
    Patches are applied directly on the service instance and its dilution_service.
    """
    if fmp_profile is _UNSET:
        fmp_profile = {"mktCap": 50_000_000, "sector": "Technology", "country": "US"}
    if dilution_data is _UNSET:
        dilution_data = {"overall_offering_risk": "High"}
    if chart_data is _UNSET:
        chart_data = {"rating": "Bullish"}
    if news is _UNSET:
        news = []

    service._fetch_fmp_float_for_gainer = AsyncMock(return_value=fmp_float)
    service._fetch_fmp_profile_for_gainer = AsyncMock(return_value=fmp_profile)
    service.dilution_service._make_request_cached = AsyncMock(return_value=dilution_data)
    service.dilution_service.get_chart_analysis = AsyncMock(return_value=chart_data)
    service.dilution_service.get_news = AsyncMock(return_value=news)
    service.dilution_service._cache_get = MagicMock(return_value=None)


# ---------------------------------------------------------------------------
# AC-1: _fetch_fmp_profile_for_gainer returns dict with sector/country/mktCap on 200
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_profile_valid_200_returns_dict():
    """
    When FMP /api/v3/profile returns HTTP 200 with a non-empty list, the function
    returns the first element as a dict containing sector, country, and mktCap.
    """
    service = _make_service()

    mock_body = [{"sector": "Technology", "country": "US", "mktCap": 50_000_000}]
    mock_resp = _fmp_profile_response(200, mock_body)
    service._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_profile_for_gainer("AAAA")

    assert result is not None
    assert result["sector"] == "Technology"
    assert result["country"] == "US"
    assert result["mktCap"] == 50_000_000


# ---------------------------------------------------------------------------
# AC-2: _fetch_fmp_profile_for_gainer returns None on HTTP 429
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_profile_429_returns_none():
    """
    When FMP returns HTTP 429 (rate limit), the function returns None without raising.
    """
    service = _make_service()

    mock_resp = _fmp_profile_response(429, None)
    service._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_profile_for_gainer("BBBB")

    assert result is None


# ---------------------------------------------------------------------------
# AC-3: _fetch_fmp_profile_for_gainer returns None when response list is empty
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_profile_empty_list_returns_none():
    """
    When FMP returns HTTP 200 but an empty list body, the function returns None.
    """
    service = _make_service()

    mock_resp = _fmp_profile_response(200, [])
    service._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_profile_for_gainer("CCCC")

    assert result is None


# ---------------------------------------------------------------------------
# AC-4: _fetch_fmp_profile_for_gainer returns None on exception (does not raise)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_fmp_profile_exception_returns_none():
    """
    When an HTTP exception occurs, the function returns None instead of raising.
    """
    service = _make_service()

    service._http.get = AsyncMock(side_effect=Exception("connection error"))

    with patch("app.services.gainers.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await service._fetch_fmp_profile_for_gainer("DDDD")

    assert result is None


# ---------------------------------------------------------------------------
# AC-5: _enrich_gainer never calls _make_request_cached with /float-outstanding
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_no_float_outstanding_call():
    """
    _enrich_gainer must not call dilution_service._make_request_cached with the
    /enterprise/v1/float-outstanding path. FMP has replaced that call.
    """
    service = _make_service()
    _setup_enrich_mocks(service)

    await service._enrich_gainer(_base_item("AAAA"))

    for c in service.dilution_service._make_request_cached.call_args_list:
        assert "/enterprise/v1/float-outstanding" not in str(c)


# ---------------------------------------------------------------------------
# AC-6: float field comes from _fetch_fmp_float_for_gainer
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_float_comes_from_fmp():
    """
    The float field in the enriched entry must equal the value returned by
    _fetch_fmp_float_for_gainer (5_000_000.0).
    """
    service = _make_service()
    _setup_enrich_mocks(service, fmp_float=5_000_000.0)

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["float"] == 5_000_000.0


# ---------------------------------------------------------------------------
# AC-7: marketCap comes from FMP profile mktCap field
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_market_cap_from_fmp_profile():
    """
    The marketCap field must come from the FMP profile's mktCap key.
    """
    service = _make_service()
    _setup_enrich_mocks(
        service,
        fmp_profile={"mktCap": 50_000_000, "sector": "Technology", "country": "US"},
    )

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["marketCap"] == 50_000_000


# ---------------------------------------------------------------------------
# AC-8: sector and country come from FMP profile
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_sector_and_country_from_fmp_profile():
    """
    The sector and country fields must reflect the values returned by
    _fetch_fmp_profile_for_gainer.
    """
    service = _make_service()
    _setup_enrich_mocks(
        service,
        fmp_profile={"mktCap": 50_000_000, "sector": "Healthcare", "country": "CA"},
    )

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["sector"] == "Healthcare"
    assert entry["country"] == "CA"


# ---------------------------------------------------------------------------
# AC-9: FMP enrichment cache hit path — _fetch_fmp_float_for_gainer called only once
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_fmp_cache_hit_calls_float_once():
    """
    When _enrich_gainer is called twice for the same ticker the FMP sub-fetchers
    are only invoked on the first call. The second call uses the _fmp_enrich_cache.
    """
    service = _make_service()
    _setup_enrich_mocks(service)

    await service._enrich_gainer(_base_item("AAAA"))
    await service._enrich_gainer(_base_item("AAAA"))

    # Both _fetch_fmp_float_for_gainer and _fetch_fmp_profile_for_gainer
    # should have been called exactly once across both _enrich_gainer calls.
    assert service._fetch_fmp_float_for_gainer.call_count == 1
    assert service._fetch_fmp_profile_for_gainer.call_count == 1


# ---------------------------------------------------------------------------
# AC-10: When FMP float returns None, entry["float"] is None (no crash)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_fmp_float_none_no_crash():
    """
    When _fetch_fmp_float_for_gainer returns None, the resulting entry must have
    float == None and no exception must propagate.
    """
    service = _make_service()
    _setup_enrich_mocks(service, fmp_float=None)

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["float"] is None


# ---------------------------------------------------------------------------
# AC-11: When FMP profile returns None, sector/country/marketCap are all None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_fmp_profile_none_fields_are_none():
    """
    When _fetch_fmp_profile_for_gainer returns None, the resulting entry must
    have sector, country, and marketCap all equal to None with no crash.
    """
    service = _make_service()
    _setup_enrich_mocks(service, fmp_profile=None)

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["sector"] is None
    assert entry["country"] is None
    assert entry["marketCap"] is None


# ---------------------------------------------------------------------------
# AC-12: risk comes from dilution_service._make_request_cached overall_offering_risk
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_risk_from_dilution_service():
    """
    The risk field must equal the overall_offering_risk value returned by
    dilution_service._make_request_cached.
    """
    service = _make_service()
    _setup_enrich_mocks(service, dilution_data={"overall_offering_risk": "Very High"})

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["risk"] == "Very High"


# ---------------------------------------------------------------------------
# AC-13: chartRating comes from dilution_service.get_chart_analysis result rating
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_chart_rating_from_chart_analysis():
    """
    The chartRating field must equal the rating value returned by
    dilution_service.get_chart_analysis.
    """
    service = _make_service()
    _setup_enrich_mocks(service, chart_data={"rating": "Bearish"})

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["chartRating"] == "Bearish"


# ---------------------------------------------------------------------------
# AC-14: newsToday is True when news list contains 8-K with today's ET date
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_news_today_true_for_8k_today():
    """
    newsToday must be True when the news list returned by dilution_service.get_news
    contains at least one item with form_type='8-K' and today's date in ET timezone.
    """
    service = _make_service()
    today_et = datetime.now(ZoneInfo("America/New_York")).strftime("%Y-%m-%d")
    news_item = {
        "form_type": "8-K",
        "created_at": f"{today_et}T10:30:00",
    }
    _setup_enrich_mocks(service, news=[news_item])

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["newsToday"] is True


# ---------------------------------------------------------------------------
# AC-15: newsToday is False when news list is empty
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_news_today_false_when_no_news():
    """
    newsToday must be False when dilution_service.get_news returns an empty list.
    """
    service = _make_service()
    _setup_enrich_mocks(service, news=[])

    entry = await service._enrich_gainer(_base_item("AAAA"))

    assert entry["newsToday"] is False


# ---------------------------------------------------------------------------
# AC-16: ticker in result is uppercased
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_ticker_is_uppercased():
    """
    The ticker field in the enriched entry must be the uppercase version of the
    input ticker regardless of the original casing.
    """
    service = _make_service()
    _setup_enrich_mocks(service)

    entry = await service._enrich_gainer(_base_item("aaaa"))

    assert entry["ticker"] == "AAAA"
