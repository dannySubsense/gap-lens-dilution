import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.dilution import DilutionService


class TestSlice2Cache:
    """Tests for DilutionService in-memory cache (Slice 2)."""

    # -------------------------------------------------------------------------
    # Test 1: _cache_set stores a value and _cache_get retrieves it
    # -------------------------------------------------------------------------
    def test_cache_set_and_get(self):
        service = DilutionService()
        service._cache_set("dilution:TEST", {"data": 1})
        result = service._cache_get("dilution:TEST")
        assert result == {"data": 1}

    # -------------------------------------------------------------------------
    # Test 2: _cache_get returns None when entry is older than the 24h TTL
    # -------------------------------------------------------------------------
    def test_cache_ttl_expired(self):
        service = DilutionService()
        # Plant an entry timestamped 25 hours (90001 s) in the past — beyond TTL_24H (86400 s)
        service._cache["dilution:TEST"] = (time.time() - 90001, {"data": 1}, None)
        result = service._cache_get("dilution:TEST")
        assert result is None

    # -------------------------------------------------------------------------
    # Test 3: _make_request_cached calls client.get only once for two calls
    #         with the same cache key (second call is served from cache)
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_make_request_cached_uses_cache(self):
        service = DilutionService()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"value": 42}]}

        service.client.get = AsyncMock(return_value=mock_response)

        first = await service._make_request_cached(
            "/enterprise/v1/dilution-rating", "TEST", "dilution:TEST"
        )
        second = await service._make_request_cached(
            "/enterprise/v1/dilution-rating", "TEST", "dilution:TEST"
        )

        assert first == second
        service.client.get.assert_called_once()

    # -------------------------------------------------------------------------
    # Test 4: _cache_set stores None as _CACHE_EMPTY sentinel (always writes)
    # -------------------------------------------------------------------------
    def test_cache_set_stores_none_as_sentinel(self):
        service = DilutionService()
        # _cache_set always writes; None is stored as the _CACHE_EMPTY sentinel
        # so that confirmed-empty responses can be distinguished from cache misses.
        service._cache_set("test:NONE", None)
        assert "test:NONE" in service._cache
        # The stored value must not be Python None — it's the sentinel object
        stored_value = service._cache["test:NONE"][1]
        assert stored_value is not None

    # -------------------------------------------------------------------------
    # Test 5: get_news delegates entirely to _news_service.get_news.
    #         DilutionService._cache_get must NOT be called during get_news.
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_get_news_bypasses_dilution_cache(self):
        service = DilutionService()

        with patch.object(
            service._news_service, "get_news", new_callable=AsyncMock, return_value=[]
        ) as mock_news_svc, patch.object(
            service, "_cache_get"
        ) as mock_cache_get:
            await service.get_news("TEST", limit=5)

        mock_news_svc.assert_called_once()
        mock_cache_get.assert_not_called()
