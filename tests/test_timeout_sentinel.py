"""
timeout-sentinel-gap — Slice 5 Gate 2

Acceptance Criteria Coverage:
- [x] (a) asyncio.TimeoutError writes sentinel to cache within 300s TTL — DilutionService
- [x] (a) httpx.TimeoutException writes sentinel to cache within 300s TTL — IntelService
- [x] (b) Sentinel hit skips HTTP call on second invocation — DilutionService
- [x] (b) Sentinel hit skips HTTP call on second invocation — IntelService
- [x] (c) Sentinel expires after TTL (301s backdated stored_at) — DilutionService
- [x] (c) Sentinel expires after TTL (301s backdated stored_at) — IntelService
- [x] (d) ExternalAPIError does NOT write sentinel — DilutionService
- [x] (d) ExternalAPIError does NOT write sentinel — IntelService
"""

import asyncio
import time
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

import app.services.dilution as dilution_module
import app.services.intel as intel_module
from app.services.dilution import DilutionService
from app.services.intel import IntelService
from app.utils.errors import ExternalAPIError

# Sentinel objects — accessed through the module to avoid cross-importing the
# private names directly (the contract says they must remain module-private).
DILUTION_CACHE_EMPTY = dilution_module._CACHE_EMPTY
INTEL_CACHE_EMPTY = intel_module._CACHE_EMPTY


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dilution() -> DilutionService:
    """Create a DilutionService with a fresh in-memory cache."""
    return DilutionService()


def _make_intel() -> IntelService:
    """Create an IntelService backed by a fresh DilutionService."""
    return IntelService(_make_dilution())


# ---------------------------------------------------------------------------
# DilutionService — (a) asyncio.TimeoutError writes sentinel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_asyncio_timeout_writes_sentinel():
    """
    (a) DilutionService: When get_ownership raises asyncio.TimeoutError internally,
    _cache_get('ownership:TEST') must return _CACHE_EMPTY (not None) within 300s.

    Uses get_ownership because its sentinel write path uses asyncio.TimeoutError
    directly from the asyncio.gather path through _make_request_list.
    """
    service = _make_dilution()
    # Mock the HTTP client to raise asyncio.TimeoutError on every call.
    # get_ownership calls _make_request_list which has max_retries=3; each attempt
    # will raise, and on the final attempt httpx.TimeoutException propagates up.
    # get_ownership itself catches (asyncio.TimeoutError, httpx.RequestError).
    # We raise asyncio.TimeoutError directly on client.get so get_ownership's
    # except clause fires and writes the backoff sentinel.
    service.client.get = AsyncMock(side_effect=asyncio.TimeoutError())

    result = await service.get_ownership("TEST")

    # Method must return None (appropriate default)
    assert result is None

    # Cache must hold the sentinel (not None, not missing)
    cached = service._cache_get("ownership:TEST")
    assert cached is DILUTION_CACHE_EMPTY, (
        f"Expected _CACHE_EMPTY sentinel after timeout, got {cached!r}"
    )


# ---------------------------------------------------------------------------
# DilutionService — (b) Sentinel hit skips live HTTP request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_sentinel_hit_skips_http_call():
    """
    (b) DilutionService: After a timeout writes the backoff sentinel, a second
    call to get_ownership within the 300s window must not issue another HTTP
    request and must still return None.
    """
    service = _make_dilution()
    service.client.get = AsyncMock(side_effect=asyncio.TimeoutError())

    # First call — fires the HTTP attempt (which times out) and writes sentinel.
    result1 = await service.get_ownership("TEST")
    assert result1 is None
    first_call_count = service.client.get.call_count
    assert first_call_count >= 1  # at least one attempt was made

    # Second call — sentinel is in cache; no further HTTP call should be made.
    result2 = await service.get_ownership("TEST")
    assert result2 is None
    assert service.client.get.call_count == first_call_count, (
        "Expected no additional HTTP calls after sentinel cache hit"
    )


# ---------------------------------------------------------------------------
# DilutionService — (c) Sentinel expires after TTL (301s)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_sentinel_expires_after_ttl():
    """
    (c) DilutionService: Backdating stored_at to 301 seconds ago causes
    _cache_get to return None (expired), allowing a fresh live request.

    TTL_BACKOFF is 300s. An entry stored 301s ago is past the window.
    """
    service = _make_dilution()
    cache_key = "ownership:EXPIRE"

    # Manually plant an aged-out backoff sentinel (3-tuple with ttl_override=300).
    service._cache[cache_key] = (time.time() - 301, DILUTION_CACHE_EMPTY, 300)

    # _cache_get must treat this as a miss (expired).
    result = service._cache_get(cache_key)
    assert result is None, (
        f"Expected None for expired sentinel, got {result!r}"
    )
    # The expired entry must have been evicted.
    assert cache_key not in service._cache

    # Confirm a fresh HTTP call now fires when the method is invoked.
    real_data = {"field": "fresh"}
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [real_data]}
    service.client.get = AsyncMock(return_value=mock_resp)

    result2 = await service.get_ownership("EXPIRE")
    assert service.client.get.call_count >= 1, "Expected a fresh HTTP request after sentinel expiry"
    assert result2 == real_data


# ---------------------------------------------------------------------------
# DilutionService — (d) ExternalAPIError does NOT write sentinel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dilution_external_api_error_does_not_write_sentinel():
    """
    (d) DilutionService: When get_ownership raises ExternalAPIError, no sentinel
    must be written. _cache_get returns None (cache miss, not sentinel hit).

    ExternalAPIError is caught by the bare `except Exception` clause which does
    NOT call _cache_set — only the timeout clause writes the backoff sentinel.
    """
    service = _make_dilution()
    # _make_request_list raises ExternalAPIError after exhausting retries.
    # We raise it directly on client.get so it propagates through _make_request_list
    # as ExternalAPIError (via the except httpx.RequestError handler converting it,
    # or directly). Either way, get_ownership's except Exception: return None fires.
    service.client.get = AsyncMock(side_effect=ExternalAPIError("upstream 503"))

    result = await service.get_ownership("TEST")

    assert result is None

    # No sentinel must be in cache — key must be absent.
    assert "ownership:TEST" not in service._cache, (
        "ExternalAPIError must not write a sentinel to the cache"
    )
    cached = service._cache_get("ownership:TEST")
    assert cached is None, (
        f"Expected None (cache miss) after ExternalAPIError, got {cached!r}"
    )


# ---------------------------------------------------------------------------
# IntelService — (a) httpx.TimeoutException writes sentinel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intel_httpx_timeout_writes_sentinel():
    """
    (a) IntelService: When get_market_strength raises httpx.TimeoutException
    (caught as httpx.RequestError since TimeoutException is a subclass), the
    except (asyncio.TimeoutError, httpx.RequestError) clause must write the
    backoff sentinel.

    After the call, _cache_get('mkt_strength') must return _CACHE_EMPTY.
    """
    service = _make_intel()
    # httpx.TimeoutException is a subclass of httpx.RequestError.
    # The except clause catches both asyncio.TimeoutError and httpx.RequestError,
    # so raising httpx.TimeoutException triggers the sentinel write.
    service.client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    result = await service.get_market_strength()

    assert result is None

    cached = service._cache_get("mkt_strength")
    assert cached is INTEL_CACHE_EMPTY, (
        f"Expected _CACHE_EMPTY sentinel after httpx.TimeoutException, got {cached!r}"
    )


# ---------------------------------------------------------------------------
# IntelService — (b) Sentinel hit skips live HTTP request
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intel_sentinel_hit_skips_http_call():
    """
    (b) IntelService: After a timeout sentinel is written by get_market_strength,
    a second call must not issue another HTTP request and must return None.
    """
    service = _make_intel()
    service.client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    # First call — fires HTTP attempt, times out, writes sentinel.
    result1 = await service.get_market_strength()
    assert result1 is None
    first_call_count = service.client.get.call_count
    assert first_call_count >= 1

    # Second call — sentinel hit, no additional HTTP call.
    result2 = await service.get_market_strength()
    assert result2 is None
    assert service.client.get.call_count == first_call_count, (
        "Expected no additional HTTP calls after IntelService sentinel cache hit"
    )


# ---------------------------------------------------------------------------
# IntelService — (c) Sentinel expires after TTL (301s)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intel_sentinel_expires_after_ttl():
    """
    (c) IntelService: Backdating stored_at to 301s ago causes _cache_get to
    return None (expired), allowing a fresh HTTP call on the next method invocation.
    """
    service = _make_intel()
    cache_key = "mkt_strength"

    # Plant an aged-out backoff sentinel.
    service._cache[cache_key] = (time.time() - 301, INTEL_CACHE_EMPTY, 300)

    result = service._cache_get(cache_key)
    assert result is None, (
        f"Expected None for expired IntelService sentinel, got {result!r}"
    )
    assert cache_key not in service._cache

    # Verify a fresh HTTP call fires when the method runs again.
    real_data = {"market": "strong"}
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"results": [real_data]}
    service.client.get = AsyncMock(return_value=mock_resp)

    result2 = await service.get_market_strength()
    assert service.client.get.call_count >= 1, "Expected a fresh HTTP request after sentinel expiry"
    assert result2 == real_data


# ---------------------------------------------------------------------------
# IntelService — (d) ExternalAPIError does NOT write sentinel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_intel_external_api_error_does_not_write_sentinel():
    """
    (d) IntelService: When get_market_strength raises ExternalAPIError, no
    sentinel must be written. ExternalAPIError is caught by except Exception
    which returns None without touching the cache.
    """
    service = _make_intel()
    service.client.get = AsyncMock(side_effect=ExternalAPIError("upstream 503"))

    result = await service.get_market_strength()

    assert result is None

    assert "mkt_strength" not in service._cache, (
        "ExternalAPIError must not write a sentinel to IntelService cache"
    )
    cached = service._cache_get("mkt_strength")
    assert cached is None, (
        f"Expected None (cache miss) after ExternalAPIError, got {cached!r}"
    )
