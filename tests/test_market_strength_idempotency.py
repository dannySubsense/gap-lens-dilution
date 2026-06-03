"""
Market-strength capture idempotency tests.

Verifies that a successful morning capture suppresses redundant AskEdgar
calls from later cron retries, while preserving the retry safety net for
the no_data / 404 / empty paths.

Acceptance criteria:
  (1) First capture() → status=captured, HTTP called once, captured_at set.
  (2) Immediate second capture() (same ET day) → status=skipped/already_captured,
      HTTP call count UNCHANGED.
  (3) captured_at set to yesterday (or _now_et advanced by one day) →
      next capture() calls AskEdgar again (count increments).
  (4) Safety net: when AskEdgar returns empty results (no_data) on first call,
      capture returns skipped/no_data AND a subsequent call still hits AskEdgar.
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import app.services.market_strength_service as ms_module
from app.db.market_strength_db import MarketStrengthDB, MarketStrengthSnapshot
from app.services.market_strength_service import MarketStrengthService

# ---------------------------------------------------------------------------
# Canned AskEdgar payload
# ---------------------------------------------------------------------------

_CANNED_DATE = "2026-06-02"
_CANNED_PAYLOAD = {
    "results": [
        {
            "date": _CANNED_DATE,
            "analysis": "x",
            "performance": "y",
            "last_updated": "2026-06-02T09:00:00Z",
        }
    ]
}

_FIXED_ET = datetime(2026, 6, 2, 9, 30, 0, tzinfo=ZoneInfo("America/New_York"))
_FIXED_ET_ISO = _FIXED_ET.isoformat()
_FIXED_ET_DATE = "2026-06-02"

_YESTERDAY_ET_ISO = datetime(
    2026, 6, 1, 9, 30, 0, tzinfo=ZoneInfo("America/New_York")
).isoformat()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_response(payload: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.raise_for_status = MagicMock()
    return resp


def _make_service(db: MarketStrengthDB) -> tuple[MarketStrengthService, AsyncMock]:
    """Return (service, mock_get) where mock_get is the http_client.get AsyncMock."""
    http_client = MagicMock()
    mock_get = AsyncMock(
        return_value=_make_mock_response(_CANNED_PAYLOAD)
    )
    http_client.get = mock_get
    service = MarketStrengthService(db=db, http_client=http_client)
    return service, mock_get


# ---------------------------------------------------------------------------
# (1) First capture → captured, HTTP called once, captured_at stamped
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_capture_calls_askedgar_and_stamps_captured_at(monkeypatch):
    """First capture on an empty DB calls AskEdgar exactly once and writes captured_at."""
    db = MarketStrengthDB(":memory:")
    db.init_db()
    service, mock_get = _make_service(db)

    monkeypatch.setattr(ms_module, "_now_et", lambda: _FIXED_ET)

    result = await service.capture()

    assert result == {"status": "captured", "date": _CANNED_DATE}
    assert mock_get.call_count == 1

    rows = db.get_history(limit=1)
    assert len(rows) == 1
    assert rows[0].captured_at is not None
    assert rows[0].captured_at[:10] == _FIXED_ET_DATE


# ---------------------------------------------------------------------------
# (2) Immediate second capture on same ET day → skipped, no new HTTP call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_second_capture_same_day_is_skipped(monkeypatch):
    """Second capture on the same ET day skips AskEdgar entirely."""
    db = MarketStrengthDB(":memory:")
    db.init_db()
    service, mock_get = _make_service(db)

    monkeypatch.setattr(ms_module, "_now_et", lambda: _FIXED_ET)

    # First call — should succeed
    first = await service.capture()
    assert first["status"] == "captured"
    assert mock_get.call_count == 1

    # Second call — same monkeypatched day
    second = await service.capture()
    assert second == {"status": "skipped", "reason": "already_captured"}
    # HTTP call count must not have increased
    assert mock_get.call_count == 1


# ---------------------------------------------------------------------------
# (3) captured_at from yesterday → next capture hits AskEdgar again
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_capture_advances_after_yesterday_captured_at(monkeypatch):
    """If the stored row has captured_at from yesterday, today's capture proceeds."""
    db = MarketStrengthDB(":memory:")
    db.init_db()

    # Pre-seed DB with a row whose captured_at is YESTERDAY
    yesterday_snapshot = MarketStrengthSnapshot(
        date="2026-06-01",
        analysis="old",
        performance="old",
        last_updated="2026-06-01T09:00:00Z",
        captured_at=_YESTERDAY_ET_ISO,
    )
    db.upsert(yesterday_snapshot)

    service, mock_get = _make_service(db)

    # Monkeypatch to TODAY
    monkeypatch.setattr(ms_module, "_now_et", lambda: _FIXED_ET)

    result = await service.capture()

    assert result["status"] == "captured"
    assert mock_get.call_count == 1


@pytest.mark.asyncio
async def test_capture_advances_when_now_et_advances_to_next_day(monkeypatch):
    """Advancing _now_et to the next ET day allows a new capture after today's was done."""
    db = MarketStrengthDB(":memory:")
    db.init_db()
    service, mock_get = _make_service(db)

    # First: capture on 2026-06-02
    monkeypatch.setattr(ms_module, "_now_et", lambda: _FIXED_ET)
    first = await service.capture()
    assert first["status"] == "captured"
    assert mock_get.call_count == 1

    # Second: same day → skipped
    second = await service.capture()
    assert second["status"] == "skipped"
    assert mock_get.call_count == 1

    # Advance to 2026-06-03
    next_day_et = datetime(2026, 6, 3, 3, 50, 0, tzinfo=ZoneInfo("America/New_York"))
    # Update mock_get to return the next day's data
    next_payload = {
        "results": [
            {
                "date": "2026-06-03",
                "analysis": "new",
                "performance": "new",
                "last_updated": "2026-06-03T09:00:00Z",
            }
        ]
    }
    mock_get.return_value = _make_mock_response(next_payload)
    monkeypatch.setattr(ms_module, "_now_et", lambda: next_day_et)

    third = await service.capture()
    assert third["status"] == "captured"
    assert third["date"] == "2026-06-03"
    assert mock_get.call_count == 2


# ---------------------------------------------------------------------------
# (4) Safety net: no_data on first call must NOT suppress later retries
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_data_response_does_not_suppress_retry(monkeypatch):
    """
    When AskEdgar returns empty results (no_data), capture must NOT write
    captured_at, and the next call must still hit AskEdgar (retry safety net).
    """
    db = MarketStrengthDB(":memory:")
    db.init_db()

    empty_payload = {"results": []}
    http_client = MagicMock()
    mock_get = AsyncMock(return_value=_make_mock_response(empty_payload))
    http_client.get = mock_get
    service = MarketStrengthService(db=db, http_client=http_client)

    monkeypatch.setattr(ms_module, "_now_et", lambda: _FIXED_ET)

    # First call — no data
    first = await service.capture()
    assert first == {"status": "skipped", "reason": "no_data"}
    assert mock_get.call_count == 1

    # DB must have NO row (no_data must not write anything)
    rows = db.get_history()
    assert len(rows) == 0

    # Second call — now AskEdgar has data; it must be called again
    mock_get.return_value = _make_mock_response(_CANNED_PAYLOAD)
    second = await service.capture()
    assert second["status"] == "captured"
    assert mock_get.call_count == 2


@pytest.mark.asyncio
async def test_no_data_null_date_does_not_suppress_retry(monkeypatch):
    """
    When AskEdgar returns a record with a null/missing date field, captured_at
    must not be written, and subsequent calls must still reach AskEdgar.
    """
    db = MarketStrengthDB(":memory:")
    db.init_db()

    null_date_payload = {
        "results": [
            {"date": None, "analysis": "x", "performance": "y", "last_updated": "..."}
        ]
    }
    http_client = MagicMock()
    mock_get = AsyncMock(return_value=_make_mock_response(null_date_payload))
    http_client.get = mock_get
    service = MarketStrengthService(db=db, http_client=http_client)

    monkeypatch.setattr(ms_module, "_now_et", lambda: _FIXED_ET)

    first = await service.capture()
    assert first == {"status": "skipped", "reason": "no_data"}
    assert mock_get.call_count == 1

    # Must not have written a row
    rows = db.get_history()
    assert len(rows) == 0

    # Next call must still hit AskEdgar
    mock_get.return_value = _make_mock_response(_CANNED_PAYLOAD)
    second = await service.capture()
    assert second["status"] == "captured"
    assert mock_get.call_count == 2


# ---------------------------------------------------------------------------
# (5) Existing rows with NULL captured_at (pre-migration rows) are NOT treated
#     as already-captured — the guard requires non-null captured_at.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_null_captured_at_row_does_not_suppress_capture(monkeypatch):
    """
    A pre-migration row (captured_at IS NULL) must not trigger the idempotency
    guard — the guard requires a non-null captured_at.
    """
    db = MarketStrengthDB(":memory:")
    db.init_db()

    # Insert a row with NO captured_at (simulates a pre-migration row)
    legacy_snapshot = MarketStrengthSnapshot(
        date=_CANNED_DATE,
        analysis="old",
        performance="old",
        last_updated="2026-06-02T09:00:00Z",
        captured_at=None,  # explicitly null
    )
    db.upsert(legacy_snapshot)

    service, mock_get = _make_service(db)
    monkeypatch.setattr(ms_module, "_now_et", lambda: _FIXED_ET)

    result = await service.capture()

    # Must proceed (not skipped), must call AskEdgar
    assert result["status"] == "captured"
    assert mock_get.call_count == 1

    # Row must now have captured_at stamped
    rows = db.get_history(limit=1)
    assert rows[0].captured_at is not None
    assert rows[0].captured_at[:10] == _FIXED_ET_DATE


# ---------------------------------------------------------------------------
# (6) MarketStrengthSnapshot backward compat — positional 4-arg construction
# ---------------------------------------------------------------------------

def test_snapshot_positional_four_arg_backward_compat():
    """Existing code constructing snapshot with 4 positional args must still work."""
    snap = MarketStrengthSnapshot("2026-06-02", "analysis", "performance", "2026-06-02T09:00:00Z")
    assert snap.date == "2026-06-02"
    assert snap.captured_at is None


# ---------------------------------------------------------------------------
# (7) init_db is idempotent — safe to call multiple times on same DB
# ---------------------------------------------------------------------------

def test_init_db_idempotent():
    """init_db called twice on the same in-memory DB must not raise."""
    db = MarketStrengthDB(":memory:")
    db.init_db()
    db.init_db()  # second call — must not raise

    # Table must be usable
    snap = MarketStrengthSnapshot("2026-06-02", None, None, None, "2026-06-02T09:00:00-04:00")
    db.upsert(snap)
    rows = db.get_history()
    assert len(rows) == 1
    assert rows[0].captured_at == "2026-06-02T09:00:00-04:00"
