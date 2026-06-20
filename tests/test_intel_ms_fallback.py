"""
GH#16 — IntelService.get_market_strength() fallback branch (intel.py:91-97).

Frank flagged at DDR-10 closure: when AskEdgar is unreachable (httpx.RequestError),
IntelService falls back to the most recent SQLite snapshot via MarketStrengthService.
This path had zero runtime test coverage — all prior gates only exercised the happy path.

Tests:
  (1) RequestError + seeded snapshot → snapshot dict returned with analysis + performance.
  (2) RequestError + empty DB (no snapshot) → None returned.
  (3) RequestError + no market_strength_service wired → None returned.
  (4) asyncio.TimeoutError also triggers the fallback (same except branch).
"""

import asyncio
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from app.services.intel import IntelService
from app.services.dilution import DilutionService
from app.services.market_strength_service import MarketStrengthService
from app.db.market_strength_db import MarketStrengthDB, MarketStrengthSnapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_intel_with_ms(ms_service: MarketStrengthService) -> IntelService:
    service = IntelService(DilutionService(), market_strength_service=ms_service)
    service.client = MagicMock()
    return service


def _make_intel_no_ms() -> IntelService:
    service = IntelService(DilutionService())
    service.client = MagicMock()
    return service


def _seed_snapshot(db: MarketStrengthDB) -> MarketStrengthSnapshot:
    snap = MarketStrengthSnapshot(
        date="2026-06-02",
        analysis="Broad market trending bullish.",
        performance="SPY +0.8%, QQQ +1.1%",
        last_updated="2026-06-02T09:00:00Z",
        captured_at="2026-06-02T09:00:00-04:00",
    )
    db.upsert(snap)
    return snap


# ---------------------------------------------------------------------------
# (1) RequestError + seeded snapshot → snapshot dict returned
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_returns_snapshot_on_request_error():
    """When AskEdgar raises RequestError, the SQLite snapshot dict is returned."""
    db = MarketStrengthDB(":memory:")
    db.init_db()
    snap = _seed_snapshot(db)

    http_client = MagicMock()
    ms_service = MarketStrengthService(db=db, http_client=http_client)
    intel = _make_intel_with_ms(ms_service)
    intel.client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

    result = await intel.get_market_strength()

    assert result is not None
    assert result["analysis"] == snap.analysis
    assert result["performance"] == snap.performance
    assert result["date"] == snap.date


# ---------------------------------------------------------------------------
# (2) RequestError + empty DB → None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_returns_none_when_db_empty():
    """When AskEdgar raises RequestError and DB is empty, None is returned."""
    db = MarketStrengthDB(":memory:")
    db.init_db()

    http_client = MagicMock()
    ms_service = MarketStrengthService(db=db, http_client=http_client)
    intel = _make_intel_with_ms(ms_service)
    intel.client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

    result = await intel.get_market_strength()

    assert result is None


# ---------------------------------------------------------------------------
# (3) RequestError + no market_strength_service → None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_returns_none_when_no_ms_service():
    """When AskEdgar raises RequestError and no MS service is wired, None is returned."""
    intel = _make_intel_no_ms()
    intel.client.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))

    result = await intel.get_market_strength()

    assert result is None


# ---------------------------------------------------------------------------
# (4) asyncio.TimeoutError also triggers the fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fallback_triggered_by_timeout_error():
    """asyncio.TimeoutError is in the same except branch — must also fall back."""
    db = MarketStrengthDB(":memory:")
    db.init_db()
    snap = _seed_snapshot(db)

    http_client = MagicMock()
    ms_service = MarketStrengthService(db=db, http_client=http_client)
    intel = _make_intel_with_ms(ms_service)
    intel.client.get = AsyncMock(side_effect=asyncio.TimeoutError())

    result = await intel.get_market_strength()

    assert result is not None
    assert result["analysis"] == snap.analysis
