"""
Slice 6: NewsService — EDGAR + FMP fetchers, dedup, rank, two-tier cache

Acceptance Criteria Coverage:
- [x] AC-1:  _cache_get returns None when key absent
- [x] AC-2:  _cache_get returns value within TTL
- [x] AC-3:  _cache_get returns None when TTL expired (stale timestamp)
- [x] AC-4:  _cache_set stores a non-None value
- [x] AC-5:  _cache_set does NOT store None
- [x] AC-6:  _cache_set stores [] (empty list is valid)
- [x] AC-7:  _cache_set stores False (False is not None)
- [x] AC-8:  _parse_edgar_atom valid Atom XML — correct fields (form_type, url, published_at ET)
- [x] AC-9:  _parse_edgar_atom skips entry with no <link href>
- [x] AC-10: _parse_edgar_atom malformed XML returns [] without raising
- [x] AC-11: _parse_edgar_atom published_at uses US/Eastern — UTC midnight crossing
- [x] AC-12: _url_hash same for URLs differing only in tracking params
- [x] AC-13: _url_hash different for structurally different URLs
- [x] AC-14: _merge_and_rank 8-K appears before news item (tier ordering)
- [x] AC-15: _merge_and_rank duplicate URL — 8-K wins over news item
- [x] AC-16: _merge_and_rank within same tier, more recent published_at first
- [x] AC-17: _fetch_edgar_8k HTTP 200 returns parsed items
- [x] AC-18: _fetch_edgar_8k HTTP 429 returns [] without raising
- [x] AC-19: _fetch_edgar_8k exception returns [] without raising
- [x] AC-20: _fetch_fmp_news HTTP 200 returns items with form_type="news" and ET date
- [x] AC-21: _fetch_fmp_news HTTP 429 returns [] without raising
- [x] AC-22: _fetch_fmp_press_releases HTTP 200 returns items with form_type="press-release"
- [x] AC-23: _fetch_fmp_press_releases HTTP 429 returns [] without raising
- [x] AC-24: get_news cache hit — fetchers NOT called
- [x] AC-25: get_news cache miss — fans out all three fetchers, returns merged list
- [x] AC-26: get_news after cache miss writes both news:{TICKER} and newsToday:{TICKER}
- [x] AC-27: newsToday:{TICKER} is True when result contains today's 8-K (ET date)
- [x] AC-28: newsToday:{TICKER} is False when result is empty
- [x] AC-29: get_news_today cache hit on newsToday:{TICKER} returns bool without calling get_news
- [x] AC-30: get_news_today cache miss calls get_news then returns bool
"""

import time
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo

from app.services.news_service import NewsService, TTL_24H, TTL_30M

ET = ZoneInfo("America/New_York")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_svc() -> NewsService:
    """Build a NewsService with a fresh empty cache."""
    return NewsService()


def _make_atom_xml(
    url: str = "https://www.sec.gov/Archives/edgar/data/12345/000001234526000001/0000012345-26-000001-index.htm",
    updated: str = "2026-05-08T13:00:00+00:00",
    title: str = "8-K filing for AAAA",
) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>{title}</title>
    <link href="{url}"/>
    <updated>{updated}</updated>
  </entry>
</feed>"""


def _make_atom_xml_no_link(
    updated: str = "2026-05-08T13:00:00+00:00",
    title: str = "No link entry",
) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>{title}</title>
    <updated>{updated}</updated>
  </entry>
</feed>"""


# ---------------------------------------------------------------------------
# AC-1: _cache_get returns None when key absent
# ---------------------------------------------------------------------------

def test_cache_get_returns_none_when_key_absent():
    """
    When no key is stored, _cache_get must return None for any TTL value.
    """
    svc = _make_svc()
    result = svc._cache_get("news:AAAA", TTL_30M)
    assert result is None


# ---------------------------------------------------------------------------
# AC-2: _cache_get returns value within TTL
# ---------------------------------------------------------------------------

def test_cache_get_returns_value_within_ttl():
    """
    A key stored at the current timestamp is well within any TTL; _cache_get
    must return the stored value.
    """
    svc = _make_svc()
    payload = [{"form_type": "8-K", "headline": "test", "url": "https://sec.gov/1", "published_at": "2026-05-08"}]
    svc._cache["news:AAAA"] = (time.time(), payload)
    result = svc._cache_get("news:AAAA", TTL_30M)
    assert result == payload


# ---------------------------------------------------------------------------
# AC-3: _cache_get returns None when TTL expired (stale timestamp)
# ---------------------------------------------------------------------------

def test_cache_get_returns_none_when_ttl_expired():
    """
    A key stored 3700 seconds ago is past TTL_30M (1800 s). _cache_get must
    return None.
    """
    svc = _make_svc()
    svc._cache["news:AAAA"] = (time.time() - 3700, [{"form_type": "8-K"}])
    result = svc._cache_get("news:AAAA", TTL_30M)
    assert result is None


# ---------------------------------------------------------------------------
# AC-4: _cache_set stores a non-None value
# ---------------------------------------------------------------------------

def test_cache_set_stores_non_none_value():
    """
    _cache_set must write a non-None dict value to _cache with a valid
    timestamp tuple.
    """
    svc = _make_svc()
    payload = {"form_type": "8-K"}
    svc._cache_set("news:AAAA", payload)
    assert "news:AAAA" in svc._cache
    _stored_at, stored_value = svc._cache["news:AAAA"]
    assert stored_value == payload


# ---------------------------------------------------------------------------
# AC-5: _cache_set does NOT store None
# ---------------------------------------------------------------------------

def test_cache_set_does_not_store_none():
    """
    The cache no-None contract (INVARIANTS.md §3): _cache_set must silently
    drop the call when value is None and must not create the key.
    """
    svc = _make_svc()
    svc._cache_set("news:AAAA", None)
    assert "news:AAAA" not in svc._cache


# ---------------------------------------------------------------------------
# AC-6: _cache_set stores [] (empty list is valid, not None)
# ---------------------------------------------------------------------------

def test_cache_set_stores_empty_list():
    """
    An empty list is not None. _cache_set must store it to prevent repeat
    lookups for tickers with no news.
    """
    svc = _make_svc()
    svc._cache_set("news:AAAA", [])
    assert "news:AAAA" in svc._cache
    _stored_at, stored_value = svc._cache["news:AAAA"]
    assert stored_value == []


# ---------------------------------------------------------------------------
# AC-7: _cache_set stores False (False is not None)
# ---------------------------------------------------------------------------

def test_cache_set_stores_false():
    """
    False is not None. _cache_set must store it — this is the newsToday path
    for tickers with no recent news.
    """
    svc = _make_svc()
    svc._cache_set("newsToday:AAAA", False)
    assert "newsToday:AAAA" in svc._cache
    _stored_at, stored_value = svc._cache["newsToday:AAAA"]
    assert stored_value is False


# ---------------------------------------------------------------------------
# AC-8: _parse_edgar_atom valid Atom XML — correct fields
# ---------------------------------------------------------------------------

def test_parse_edgar_atom_valid_xml_correct_fields():
    """
    A minimal valid Atom feed with one entry must produce a list with one item
    containing form_type="8-K", a non-empty url, and published_at as an
    US/Eastern date string (not a UTC raw slice).
    """
    svc = _make_svc()
    xml = _make_atom_xml(
        url="https://www.sec.gov/Archives/edgar/data/12345/0001.htm",
        updated="2026-05-08T13:00:00+00:00",
        title="8-K Current Report",
    )
    result = svc._parse_edgar_atom(xml)

    assert len(result) == 1
    item = result[0]
    assert item["form_type"] == "8-K"
    assert item["url"] == "https://www.sec.gov/Archives/edgar/data/12345/0001.htm"
    assert item["published_at"] == "2026-05-08"
    assert "headline" in item


# ---------------------------------------------------------------------------
# AC-9: _parse_edgar_atom skips entry with no <link href>
# ---------------------------------------------------------------------------

def test_parse_edgar_atom_skips_entry_with_no_link():
    """
    An entry without a <link href> attribute produces an empty url string.
    The implementation skips items with no url — result must be empty.
    """
    svc = _make_svc()
    xml = _make_atom_xml_no_link(updated="2026-05-08T13:00:00+00:00")
    result = svc._parse_edgar_atom(xml)
    assert result == []


# ---------------------------------------------------------------------------
# AC-10: _parse_edgar_atom malformed XML returns [] without raising
# ---------------------------------------------------------------------------

def test_parse_edgar_atom_malformed_xml_returns_empty_list():
    """
    Malformed XML must not raise; _parse_edgar_atom must return [] defensively.
    """
    svc = _make_svc()
    result = svc._parse_edgar_atom("<not valid xml<<<")
    assert result == []


# ---------------------------------------------------------------------------
# AC-11: _parse_edgar_atom published_at uses US/Eastern — UTC midnight crossing
# ---------------------------------------------------------------------------

def test_parse_edgar_atom_published_at_is_eastern_date_midnight_crossing():
    """
    2026-05-09T03:30:00Z is UTC, which is 2026-05-08T23:30:00 US/Eastern (UTC-4
    in May). The published_at field must be "2026-05-08", not "2026-05-09".
    This confirms the implementation converts to ET before taking the date,
    rather than slicing the UTC string directly.
    """
    svc = _make_svc()
    xml = _make_atom_xml(
        url="https://www.sec.gov/Archives/edgar/data/12345/0001.htm",
        updated="2026-05-09T03:30:00Z",
    )
    result = svc._parse_edgar_atom(xml)
    assert len(result) == 1
    assert result[0]["published_at"] == "2026-05-08"


# ---------------------------------------------------------------------------
# AC-12: _url_hash same for URLs differing only in tracking params
# ---------------------------------------------------------------------------

def test_url_hash_same_for_urls_differing_only_in_tracking_params():
    """
    Two URLs that are identical except for UTM tracking params must produce
    the same 16-character hash after normalization strips the tracking params.
    """
    url_base = "https://example.com/news/article-1"
    url_tracked = "https://example.com/news/article-1?utm_source=twitter&utm_campaign=may26"
    assert NewsService._url_hash(url_base) == NewsService._url_hash(url_tracked)


# ---------------------------------------------------------------------------
# AC-13: _url_hash different for structurally different URLs
# ---------------------------------------------------------------------------

def test_url_hash_different_for_structurally_different_urls():
    """
    Two URLs with different paths must produce different hashes.
    """
    url_a = "https://example.com/news/article-1"
    url_b = "https://example.com/news/article-2"
    assert NewsService._url_hash(url_a) != NewsService._url_hash(url_b)


# ---------------------------------------------------------------------------
# AC-14: _merge_and_rank 8-K appears before news item (tier ordering)
# ---------------------------------------------------------------------------

def test_merge_and_rank_8k_appears_before_news_tier_ordering():
    """
    An 8-K item (tier 1) must appear before a news item (tier 3) in the
    merged output, regardless of published_at ordering.
    """
    svc = _make_svc()
    edgar_items = [{"form_type": "8-K", "headline": "8-K", "url": "https://sec.gov/8k", "published_at": "2026-05-07"}]
    news_items = [{"form_type": "news", "headline": "News", "url": "https://fmp.com/news", "published_at": "2026-05-08"}]

    result = svc._merge_and_rank(edgar_items, [], news_items)

    assert len(result) == 2
    assert result[0]["form_type"] == "8-K"
    assert result[1]["form_type"] == "news"


# ---------------------------------------------------------------------------
# AC-15: _merge_and_rank duplicate URL — 8-K wins over news item
# ---------------------------------------------------------------------------

def test_merge_and_rank_duplicate_url_8k_wins_over_news():
    """
    When an 8-K and a news item share the same URL hash, the 8-K (tier 1)
    must be kept and the news item (tier 3) must be discarded.
    """
    svc = _make_svc()
    shared_url = "https://www.sec.gov/Archives/edgar/data/12345/0001.htm"
    edgar_items = [{"form_type": "8-K", "headline": "SEC 8-K", "url": shared_url, "published_at": "2026-05-08"}]
    news_items = [{"form_type": "news", "headline": "FMP copy", "url": shared_url, "published_at": "2026-05-08"}]

    result = svc._merge_and_rank(edgar_items, [], news_items)

    assert len(result) == 1
    assert result[0]["form_type"] == "8-K"


# ---------------------------------------------------------------------------
# AC-16: _merge_and_rank within same tier, more recent published_at first
# ---------------------------------------------------------------------------

def test_merge_and_rank_within_same_tier_more_recent_first():
    """
    Within the same tier (both news), the item with the more recent
    published_at must appear first.
    """
    svc = _make_svc()
    older = {"form_type": "news", "headline": "Old", "url": "https://fmp.com/old", "published_at": "2026-05-06"}
    newer = {"form_type": "news", "headline": "New", "url": "https://fmp.com/new", "published_at": "2026-05-08"}

    # Pass in older-first order to confirm sort is applied
    result = svc._merge_and_rank([], [], [older, newer])

    assert len(result) == 2
    assert result[0]["published_at"] == "2026-05-08"
    assert result[1]["published_at"] == "2026-05-06"


# ---------------------------------------------------------------------------
# AC-17: _fetch_edgar_8k HTTP 200 returns parsed items
# ---------------------------------------------------------------------------

async def test_fetch_edgar_8k_http_200_returns_parsed_items():
    """
    When the EDGAR endpoint returns HTTP 200 with valid Atom XML, _fetch_edgar_8k
    must return a non-empty list of parsed items with form_type="8-K".
    """
    svc = _make_svc()
    xml = _make_atom_xml(
        url="https://www.sec.gov/Archives/edgar/data/12345/0001.htm",
        updated="2026-05-08T14:00:00+00:00",
    )
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = xml
    svc._http.get = AsyncMock(return_value=mock_resp)

    result = await svc._fetch_edgar_8k("AAAA")

    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["form_type"] == "8-K"
    assert result[0]["url"] == "https://www.sec.gov/Archives/edgar/data/12345/0001.htm"


# ---------------------------------------------------------------------------
# AC-18: _fetch_edgar_8k HTTP 429 returns [] without raising
# ---------------------------------------------------------------------------

async def test_fetch_edgar_8k_http_429_returns_empty_list():
    """
    HTTP 429 (rate limit) must be treated as a silent empty result.
    _fetch_edgar_8k must return [] and must not raise.
    """
    svc = _make_svc()
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    svc._http.get = AsyncMock(return_value=mock_resp)

    result = await svc._fetch_edgar_8k("AAAA")

    assert result == []


# ---------------------------------------------------------------------------
# AC-19: _fetch_edgar_8k exception returns [] without raising
# ---------------------------------------------------------------------------

async def test_fetch_edgar_8k_exception_returns_empty_list():
    """
    When the HTTP request itself raises (network error, timeout), _fetch_edgar_8k
    must catch the exception and return []. It must never raise.
    """
    svc = _make_svc()
    svc._http.get = AsyncMock(side_effect=Exception("connection refused"))

    result = await svc._fetch_edgar_8k("AAAA")

    assert result == []


# ---------------------------------------------------------------------------
# AC-20: _fetch_fmp_news HTTP 200 returns items with form_type="news" and ET date
# ---------------------------------------------------------------------------

async def test_fetch_fmp_news_http_200_returns_news_items_with_et_date():
    """
    HTTP 200 with a valid FMP news response must return a list of items each
    having form_type="news" and a published_at date converted to US/Eastern.

    The UTC timestamp "2026-05-09T03:30:00+00:00" maps to "2026-05-08" in
    US/Eastern (UTC-4 in May). Explicit +00:00 offset ensures unambiguous UTC
    parsing — verifies ET conversion, not raw UTC string slice.
    """
    svc = _make_svc()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "title": "FMP headline",
            "url": "https://fmp.com/article",
            "publishedDate": "2026-05-09T03:30:00+00:00",
        }
    ]
    svc._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.news_service.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await svc._fetch_fmp_news("AAAA")

    assert len(result) == 1
    assert result[0]["form_type"] == "news"
    assert result[0]["published_at"] == "2026-05-08"
    assert result[0]["headline"] == "FMP headline"


# ---------------------------------------------------------------------------
# AC-21: _fetch_fmp_news HTTP 429 returns [] without raising
# ---------------------------------------------------------------------------

async def test_fetch_fmp_news_http_429_returns_empty_list():
    """
    HTTP 429 from FMP news endpoint must be silently treated as [] (no retry,
    no raise). Per INVARIANTS.md §3 FMP 429 silent fallback contract.
    """
    svc = _make_svc()
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    svc._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.news_service.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await svc._fetch_fmp_news("AAAA")

    assert result == []


# ---------------------------------------------------------------------------
# AC-22: _fetch_fmp_press_releases HTTP 200 returns press-release items
# ---------------------------------------------------------------------------

async def test_fetch_fmp_press_releases_http_200_returns_press_release_items():
    """
    HTTP 200 with a valid FMP press-releases response must return items with
    form_type="press-release".
    """
    svc = _make_svc()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = [
        {
            "title": "Company Press Release",
            "url": "https://fmp.com/pr/1",
            "date": "2026-05-08T10:00:00+00:00",
        }
    ]
    svc._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.news_service.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await svc._fetch_fmp_press_releases("AAAA")

    assert len(result) == 1
    assert result[0]["form_type"] == "press-release"
    assert result[0]["headline"] == "Company Press Release"


# ---------------------------------------------------------------------------
# AC-23: _fetch_fmp_press_releases HTTP 429 returns [] without raising
# ---------------------------------------------------------------------------

async def test_fetch_fmp_press_releases_http_429_returns_empty_list():
    """
    HTTP 429 from FMP press-releases endpoint must return [] silently.
    """
    svc = _make_svc()
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    svc._http.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.news_service.settings") as mock_settings:
        mock_settings.fmp_api_key = "test-key"
        result = await svc._fetch_fmp_press_releases("AAAA")

    assert result == []


# ---------------------------------------------------------------------------
# AC-24: get_news cache hit — all three fetchers NOT called
# ---------------------------------------------------------------------------

async def test_get_news_cache_hit_fetchers_not_called():
    """
    When news:AAAA is already cached within TTL_30M, get_news must return
    the cached value without calling any of the three source fetchers.
    """
    svc = _make_svc()
    cached_items = [{"form_type": "8-K", "headline": "Cached", "url": "https://sec.gov/1", "published_at": "2026-05-08"}]
    svc._cache["news:AAAA"] = (time.time(), cached_items)
    svc._http.get = AsyncMock()

    result = await svc.get_news("AAAA")

    assert result == cached_items
    assert svc._http.get.call_count == 0


# ---------------------------------------------------------------------------
# AC-25: get_news cache miss — fans out all three fetchers, returns merged list
# ---------------------------------------------------------------------------

async def test_get_news_cache_miss_fans_out_all_three_fetchers():
    """
    On a cache miss, get_news must call all three source fetchers and return
    a merged list. Verified by mocking each fetcher independently and
    confirming all three are invoked and their results merged.
    """
    svc = _make_svc()
    edgar_item = {"form_type": "8-K", "headline": "8-K", "url": "https://sec.gov/8k", "published_at": "2026-05-08"}
    pr_item = {"form_type": "press-release", "headline": "PR", "url": "https://fmp.com/pr", "published_at": "2026-05-08"}
    news_item = {"form_type": "news", "headline": "News", "url": "https://fmp.com/news", "published_at": "2026-05-08"}

    svc._fetch_edgar_8k = AsyncMock(return_value=[edgar_item])
    svc._fetch_fmp_press_releases = AsyncMock(return_value=[pr_item])
    svc._fetch_fmp_news = AsyncMock(return_value=[news_item])

    result = await svc.get_news("AAAA")

    assert svc._fetch_edgar_8k.call_count == 1
    assert svc._fetch_fmp_press_releases.call_count == 1
    assert svc._fetch_fmp_news.call_count == 1
    assert len(result) == 3


# ---------------------------------------------------------------------------
# AC-26: get_news writes both news:{TICKER} and newsToday:{TICKER} after cache miss
# ---------------------------------------------------------------------------

async def test_get_news_writes_both_cache_keys_after_cache_miss():
    """
    After a live fetch (cache miss), get_news must write both news:AAAA (full
    list) and newsToday:AAAA (bool) to _cache.
    """
    svc = _make_svc()
    svc._fetch_edgar_8k = AsyncMock(return_value=[])
    svc._fetch_fmp_press_releases = AsyncMock(return_value=[])
    svc._fetch_fmp_news = AsyncMock(return_value=[])

    await svc.get_news("AAAA")

    assert "news:AAAA" in svc._cache
    assert "newsToday:AAAA" in svc._cache
    _stored_at, news_value = svc._cache["news:AAAA"]
    _stored_at_today, today_value = svc._cache["newsToday:AAAA"]
    assert isinstance(news_value, list)
    assert isinstance(today_value, bool)


# ---------------------------------------------------------------------------
# AC-27: newsToday:{TICKER} is True when result contains today's 8-K (ET date)
# ---------------------------------------------------------------------------

async def test_get_news_news_today_true_when_today_8k_in_result():
    """
    When the merged result contains an 8-K with today's ET date as published_at,
    newsToday:AAAA must be stored as True.
    """
    svc = _make_svc()
    today_et = str(datetime.now(ET).date())
    today_8k = {
        "form_type": "8-K",
        "headline": "Today 8-K",
        "url": "https://sec.gov/today",
        "published_at": today_et,
    }
    svc._fetch_edgar_8k = AsyncMock(return_value=[today_8k])
    svc._fetch_fmp_press_releases = AsyncMock(return_value=[])
    svc._fetch_fmp_news = AsyncMock(return_value=[])

    await svc.get_news("AAAA")

    _stored_at, today_value = svc._cache["newsToday:AAAA"]
    assert today_value is True


# ---------------------------------------------------------------------------
# AC-28: newsToday:{TICKER} is False when result is empty
# ---------------------------------------------------------------------------

async def test_get_news_news_today_false_when_result_is_empty():
    """
    When all three fetchers return empty lists, the merged result is empty.
    newsToday:AAAA must be stored as False.
    """
    svc = _make_svc()
    svc._fetch_edgar_8k = AsyncMock(return_value=[])
    svc._fetch_fmp_press_releases = AsyncMock(return_value=[])
    svc._fetch_fmp_news = AsyncMock(return_value=[])

    await svc.get_news("AAAA")

    _stored_at, today_value = svc._cache["newsToday:AAAA"]
    assert today_value is False


# ---------------------------------------------------------------------------
# AC-29: get_news_today cache hit returns bool without calling get_news
# ---------------------------------------------------------------------------

async def test_get_news_today_cache_hit_returns_bool_without_calling_get_news():
    """
    When newsToday:AAAA is in cache within TTL_24H, get_news_today must return
    the cached bool directly and must not invoke get_news.
    """
    svc = _make_svc()
    svc._cache["newsToday:AAAA"] = (time.time(), True)
    svc.get_news = AsyncMock()

    result = await svc.get_news_today("AAAA")

    assert result is True
    assert svc.get_news.call_count == 0


# ---------------------------------------------------------------------------
# AC-30: get_news_today cache miss calls get_news then returns bool
# ---------------------------------------------------------------------------

async def test_get_news_today_cache_miss_calls_get_news_returns_bool():
    """
    When newsToday:AAAA is not in cache, get_news_today must call get_news
    (which populates the key as a side-effect), then return a bool.
    """
    svc = _make_svc()
    # No newsToday key pre-populated
    svc._fetch_edgar_8k = AsyncMock(return_value=[])
    svc._fetch_fmp_press_releases = AsyncMock(return_value=[])
    svc._fetch_fmp_news = AsyncMock(return_value=[])

    result = await svc.get_news_today("AAAA")

    assert isinstance(result, bool)
    # Confirm the key was written as a side-effect of get_news
    assert "newsToday:AAAA" in svc._cache
