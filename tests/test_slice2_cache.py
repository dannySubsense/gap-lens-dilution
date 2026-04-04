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
    # Test 2: _cache_get returns None when entry is older than 30 minutes
    # -------------------------------------------------------------------------
    def test_cache_ttl_expired(self):
        service = DilutionService()
        # Manually plant an entry timestamped 31 minutes in the past
        service._cache["dilution:TEST"] = (time.time() - 1860, {"data": 1})
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
    # Test 4: _cache_set ignores None values (key must not appear in _cache)
    # -------------------------------------------------------------------------
    def test_cache_set_ignores_none(self):
        service = DilutionService()
        service._cache_set("test:NONE", None)
        assert "test:NONE" not in service._cache

    # -------------------------------------------------------------------------
    # Test 5: get_news calls _make_request_list directly, not any cached path.
    #         _cache_get must NOT be called during a get_news invocation.
    # -------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_get_news_bypasses_cache(self):
        service = DilutionService()

        with patch.object(
            service, "_make_request_list", new_callable=AsyncMock, return_value=[]
        ) as mock_list, patch.object(
            service, "_cache_get"
        ) as mock_cache_get:
            await service.get_news("TEST", limit=5)

        mock_list.assert_called_once()
        mock_cache_get.assert_not_called()
