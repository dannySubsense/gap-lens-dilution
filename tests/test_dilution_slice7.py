"""
Slice 7: DilutionService news delegation + press-release normalization

Acceptance Criteria Coverage:
- [x] AC-1: get_news delegates entirely to _news_service.get_news
- [x] AC-2: get_news_today_cached delegates entirely to _news_service.get_news_today
- [x] AC-3: get_dilution_data_v2 normalizes form_type="press-release" → "news"
- [x] AC-4: Items with form_type != "press-release" are passed through unchanged
"""

from unittest.mock import AsyncMock

from app.services.dilution import DilutionService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dilution_service() -> DilutionService:
    """Build a DilutionService instance (no network calls in constructor)."""
    return DilutionService()


# ---------------------------------------------------------------------------
# AC-1: get_news delegates entirely to _news_service.get_news
# ---------------------------------------------------------------------------

async def test_get_news_delegates_to_news_service():
    """
    DilutionService.get_news must delegate entirely to _news_service.get_news
    with the ticker as the positional arg and return its result unchanged.
    No AskEdgar call or cache logic must execute in the method body.
    """
    d = _make_dilution_service()
    expected = [
        {"form_type": "8-K", "headline": "test", "url": "https://sec.gov/1", "published_at": "2026-05-08"}
    ]
    d._news_service.get_news = AsyncMock(return_value=expected)

    result = await d.get_news("AAAA")

    d._news_service.get_news.assert_called_once_with("AAAA", limit=10)
    assert result == expected


# ---------------------------------------------------------------------------
# AC-2: get_news_today_cached delegates entirely to _news_service.get_news_today
# ---------------------------------------------------------------------------

async def test_get_news_today_cached_delegates_to_news_service():
    """
    DilutionService.get_news_today_cached must delegate entirely to
    _news_service.get_news_today with the ticker and return its result.
    No cache check or fallback logic must execute in the method body.
    """
    d = _make_dilution_service()
    d._news_service.get_news_today = AsyncMock(return_value=True)

    result = await d.get_news_today_cached("AAAA")

    d._news_service.get_news_today.assert_called_once_with("AAAA")
    assert result is True


# ---------------------------------------------------------------------------
# AC-3: get_dilution_data_v2 normalizes press-release → "news" in result
# ---------------------------------------------------------------------------

async def test_get_dilution_data_v2_normalizes_press_release_to_news():
    """
    When the news list returned by get_news contains an item with
    form_type="press-release", get_dilution_data_v2 must rewrite that
    form_type to "news" before including the item in result["news"].
    The item count must be unchanged (1 in, 1 out).
    """
    d = _make_dilution_service()

    press_release_item = {
        "form_type": "press-release",
        "headline": "PR",
        "url": "https://fmp.com/pr",
        "published_at": "2026-05-08",
    }

    # Mock all sub-call paths so no real HTTP requests are attempted.
    # _make_request_cached covers: dilution-rating, float-outstanding.
    # _make_request_list_cached covers: dilution-data, registrations, gap_stats, offerings.
    # get_ownership and get_screener_data each call _make_request_list / _make_request
    # internally; mock them at the method level for simplicity.
    d._make_request_cached = AsyncMock(return_value={})
    d._make_request_list_cached = AsyncMock(return_value=[])
    d.get_ownership = AsyncMock(return_value=None)
    d.get_screener_data = AsyncMock(return_value=None)
    d.get_chart_analysis = AsyncMock(return_value=None)
    d.get_news = AsyncMock(return_value=[press_release_item])

    result = await d.get_dilution_data_v2("AAAA")

    news_items = result["news"]
    assert len(news_items) == 1
    assert news_items[0]["form_type"] == "news", (
        f"Expected 'news' but got '{news_items[0]['form_type']}'"
    )
    assert all(item["form_type"] != "press-release" for item in news_items), (
        "No item in result['news'] should have form_type='press-release'"
    )


# ---------------------------------------------------------------------------
# AC-4: Items with form_type != "press-release" are passed through unchanged
# ---------------------------------------------------------------------------

async def test_get_dilution_data_v2_passes_through_non_press_release_items():
    """
    Items with form_type values other than "press-release" (e.g. "8-K", "news")
    must appear in result["news"] with their original form_type unchanged.
    """
    d = _make_dilution_service()

    eight_k_item = {
        "form_type": "8-K",
        "headline": "SEC filing",
        "url": "https://sec.gov/8k",
        "published_at": "2026-05-08",
    }
    news_item = {
        "form_type": "news",
        "headline": "Article",
        "url": "https://fmp.com/article",
        "published_at": "2026-05-08",
    }

    d._make_request_cached = AsyncMock(return_value={})
    d._make_request_list_cached = AsyncMock(return_value=[])
    d.get_ownership = AsyncMock(return_value=None)
    d.get_screener_data = AsyncMock(return_value=None)
    d.get_chart_analysis = AsyncMock(return_value=None)
    d.get_news = AsyncMock(return_value=[eight_k_item, news_item])

    result = await d.get_dilution_data_v2("AAAA")

    news_items = result["news"]
    assert len(news_items) == 2

    form_types = {item["form_type"] for item in news_items}
    assert "8-K" in form_types, "8-K item must be present and unchanged"
    assert "news" in form_types, "news item must be present and unchanged"
    assert "press-release" not in form_types
