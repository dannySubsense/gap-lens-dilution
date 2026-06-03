"""
Slice 2: FMP Profile Sub-Fetcher + Rewritten _enrich_gainer Tests

Float is now sourced from AskEdgar float-outstanding (not FMP).
FMP profile (_fetch_fmp_profile_for_gainer) supplies sector/country only.
newsToday is delegated to dilution_service.get_news_today_cached.

Acceptance Criteria Coverage:
- [x] AC-1:  _fetch_fmp_profile_for_gainer returns dict with sector/country/mktCap on valid 200
- [x] AC-2:  _fetch_fmp_profile_for_gainer returns None on HTTP 429
- [x] AC-3:  _fetch_fmp_profile_for_gainer returns None when response list is empty
- [x] AC-4:  _fetch_fmp_profile_for_gainer returns None on exception (does not raise)
- [removed] AC-5: _enrich_gainer never calls /enterprise/v1/float-outstanding — DELETED
             (current code DOES call /v1/float-outstanding via _make_request_cached; this
             assertion was for an intermediate design where FMP supplied float)
- [removed] AC-6: float field comes from _fetch_fmp_float_for_gainer — DELETED
             (_fetch_fmp_float_for_gainer was removed; float comes from AskEdgar)
- [x] AC-7:  marketCap comes from AskEdgar float-outstanding market_cap_final field
- [x] AC-8:  sector and country come from FMP profile
- [x] AC-9:  FMP enrichment cache hit path — _fetch_fmp_profile_for_gainer called only once
             for two calls with the same ticker
- [x] AC-10: When AskEdgar float-outstanding returns None, entry["float"] is None (no crash)
- [x] AC-11: When FMP profile returns None, sector/country are None (no crash)
- [x] AC-12: risk comes from dilution_service._make_request_cached result overall_offering_risk
- [x] AC-13: chartRating comes from dilution_service.get_chart_analysis result rating
- [x] AC-14: newsToday is True when get_news_today_cached returns True
- [x] AC-15: newsToday is False when get_news_today_cached returns False
- [x] AC-16: ticker in result is uppercased
- [x] Issue #1: all-null dict must NOT be cached
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.dilution import DilutionService
from app.services.gainers import GainerFilterParams, GainersService

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


def _default_fp() -> GainerFilterParams:
    """Default GainerFilterParams — no bounds set, no exclusions."""
    return GainerFilterParams()


def _setup_enrich_mocks(
    service: GainersService,
    fmp_profile=_UNSET,
    dilution_data=_UNSET,
    chart_data=_UNSET,
    float_data=_UNSET,
    news_today=_UNSET,
) -> None:
    """
    Patch the sub-calls used by _enrich_gainer with AsyncMock defaults.

    Current _enrich_gainer fetches (in order):
      1. _fetch_fmp_profile_for_gainer  → sector/country (cached in _fmp_enrich_cache)
      2. dilution_service._make_request_cached /v1/dilution-rating  → dilution_data
      3. dilution_service.get_chart_analysis                        → chart_data
      4. dilution_service._make_request_cached /v1/float-outstanding → float_data
      5. dilution_service.get_news_today_cached                     → news_today bool

    _make_request_cached is called with two different paths; we use side_effect to
    route by path argument.
    """
    if fmp_profile is _UNSET:
        fmp_profile = {"sector": "Technology", "country": "US", "mktCap": 50_000_000}
    if dilution_data is _UNSET:
        dilution_data = {"overall_offering_risk": "High"}
    if chart_data is _UNSET:
        chart_data = {"rating": "Bullish"}
    if float_data is _UNSET:
        float_data = {"float": 5_000_000.0, "market_cap_final": 50_000_000.0}
    if news_today is _UNSET:
        news_today = False

    service._fetch_fmp_profile_for_gainer = AsyncMock(return_value=fmp_profile)
    service.dilution_service.get_chart_analysis = AsyncMock(return_value=chart_data)
    service.dilution_service.get_news_today_cached = AsyncMock(return_value=news_today)

    # _make_request_cached is called for both /v1/dilution-rating and /v1/float-outstanding.
    # Route by the first positional argument (path).
    async def _route_make_request_cached(path, ticker, cache_key):
        if "float-outstanding" in path:
            return float_data
        return dilution_data

    service.dilution_service._make_request_cached = AsyncMock(
        side_effect=_route_make_request_cached
    )


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
# AC-7: marketCap comes from AskEdgar float-outstanding market_cap_final field
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_market_cap_from_askedgar_float_outstanding():
    """
    The marketCap field in the enriched entry must equal market_cap_final from
    the AskEdgar /v1/float-outstanding response, not from FMP profile.
    """
    service = _make_service()
    _setup_enrich_mocks(
        service,
        float_data={"float": 5_000_000.0, "market_cap_final": 75_000_000.0},
    )

    entry = await service._enrich_gainer(_base_item("AAAA"), _default_fp())

    assert entry["marketCap"] == 75_000_000.0


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
        fmp_profile={"sector": "Healthcare", "country": "CA", "mktCap": 50_000_000},
    )

    entry = await service._enrich_gainer(_base_item("AAAA"), _default_fp())

    assert entry["sector"] == "Healthcare"
    assert entry["country"] == "CA"


# ---------------------------------------------------------------------------
# AC-9: FMP enrichment cache hit — _fetch_fmp_profile_for_gainer called only once
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_fmp_cache_hit_calls_profile_once():
    """
    When _enrich_gainer is called twice for the same ticker, _fetch_fmp_profile_for_gainer
    is invoked only on the first call. The second call uses the _fmp_enrich_cache.
    """
    service = _make_service()
    _setup_enrich_mocks(service)

    await service._enrich_gainer(_base_item("AAAA"), _default_fp())
    await service._enrich_gainer(_base_item("AAAA"), _default_fp())

    assert service._fetch_fmp_profile_for_gainer.call_count == 1


# ---------------------------------------------------------------------------
# AC-10: When AskEdgar float-outstanding returns None, entry["float"] is None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_askedgar_float_none_no_crash():
    """
    When AskEdgar /v1/float-outstanding returns None, the resulting entry must have
    float == None and no exception must propagate.
    """
    service = _make_service()
    _setup_enrich_mocks(service, float_data=None)

    entry = await service._enrich_gainer(_base_item("AAAA"), _default_fp())

    assert entry["float"] is None


# ---------------------------------------------------------------------------
# AC-11: When FMP profile returns None, sector/country are None (no crash)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_fmp_profile_none_fields_are_none():
    """
    When _fetch_fmp_profile_for_gainer returns None, the resulting entry must
    have sector and country both equal to None with no crash.
    """
    service = _make_service()
    _setup_enrich_mocks(service, fmp_profile=None)

    entry = await service._enrich_gainer(_base_item("AAAA"), _default_fp())

    assert entry["sector"] is None
    assert entry["country"] is None


# ---------------------------------------------------------------------------
# AC-12: risk comes from dilution_service._make_request_cached overall_offering_risk
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_risk_from_dilution_service():
    """
    The risk field must equal the overall_offering_risk value returned by
    dilution_service._make_request_cached for the /v1/dilution-rating path.
    """
    service = _make_service()
    _setup_enrich_mocks(service, dilution_data={"overall_offering_risk": "Very High"})

    entry = await service._enrich_gainer(_base_item("AAAA"), _default_fp())

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

    entry = await service._enrich_gainer(_base_item("AAAA"), _default_fp())

    assert entry["chartRating"] == "Bearish"


# ---------------------------------------------------------------------------
# AC-14: newsToday is True when get_news_today_cached returns True
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_news_today_true():
    """
    newsToday must be True when dilution_service.get_news_today_cached returns True.
    """
    service = _make_service()
    _setup_enrich_mocks(service, news_today=True)

    entry = await service._enrich_gainer(_base_item("AAAA"), _default_fp())

    assert entry["newsToday"] is True


# ---------------------------------------------------------------------------
# AC-15: newsToday is False when get_news_today_cached returns False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enrich_gainer_news_today_false():
    """
    newsToday must be False when dilution_service.get_news_today_cached returns False.
    """
    service = _make_service()
    _setup_enrich_mocks(service, news_today=False)

    entry = await service._enrich_gainer(_base_item("AAAA"), _default_fp())

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

    entry = await service._enrich_gainer(_base_item("aaaa"), _default_fp())

    assert entry["ticker"] == "AAAA"


# ---------------------------------------------------------------------------
# Issue #1: all-null dict must NOT be cached (Frank QC, 2026-05-08)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fmp_enrich_cache_does_not_cache_all_null_dict():
    """
    When _fetch_fmp_profile_for_gainer returns None, the resulting all-None
    fmp_fields dict must not be written to _fmp_enrich_cache. A second
    _enrich_gainer call for the same ticker must re-attempt the FMP fetch.
    """
    service = _make_service()
    _setup_enrich_mocks(service, fmp_profile=None)

    await service._enrich_gainer(_base_item("AAAA"), _default_fp())
    await service._enrich_gainer(_base_item("AAAA"), _default_fp())

    # If the all-null dict had been cached, the second call would be a cache hit
    # and the fetcher would have been called only once total.
    # With the fix, neither call is cached, so each call re-invokes the fetcher.
    assert service._fetch_fmp_profile_for_gainer.call_count == 2
