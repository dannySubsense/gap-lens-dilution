"""
Tests for UsageLogDB — Slice 2: UsageLogDB

9 tests covering init idempotency, insert/retrieval, ordering, 7-day summary
filtering and aggregation, balance queries, and nullable cost handling.

All tests use UsageLogDB(":memory:") + init_db().
All ts fixtures use canonical format: YYYY-MM-DDTHH:MM:SS+00:00.
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.db.usage_log_db import UsageLogDB, UsageRecord


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts_days_ago(days: int) -> str:
    """Return canonical ts string for N days before now (UTC)."""
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime(
        "%Y-%m-%dT%H:%M:%S+00:00"
    )


def _make_db() -> UsageLogDB:
    db = UsageLogDB(":memory:")
    db.init_db()
    return db


def _record(
    ts: str,
    consumer: str = "danny",
    endpoint: str = "/v1/dilution",
    ticker: str | None = "AAPL",
    cost_microdollars: int | None = 9800,
    credits_remaining_dollars: float = 47.23,
) -> UsageRecord:
    return UsageRecord(
        ts=ts,
        consumer=consumer,
        endpoint=endpoint,
        ticker=ticker,
        cost_microdollars=cost_microdollars,
        credits_remaining_dollars=credits_remaining_dollars,
    )


# ---------------------------------------------------------------------------
# 1. init_db idempotency
# ---------------------------------------------------------------------------

def test_init_db_idempotent():
    """Calling init_db() twice on the same in-memory DB must not raise."""
    db = UsageLogDB(":memory:")
    db.init_db()
    db.init_db()  # second call — must not raise


# ---------------------------------------------------------------------------
# 2. insert and get_recent basic round-trip
# ---------------------------------------------------------------------------

def test_insert_and_get_recent():
    """Inserting one record and calling get_recent(1) returns it with correct fields."""
    db = _make_db()
    ts = "2026-06-20T14:32:00+00:00"
    rec = _record(ts=ts, consumer="danny", endpoint="/v1/dilution", ticker="MITI",
                  cost_microdollars=9800, credits_remaining_dollars=47.23)
    db.insert(rec)

    results = db.get_recent(1)
    assert len(results) == 1
    r = results[0]
    assert r.ts == ts
    assert r.consumer == "danny"
    assert r.endpoint == "/v1/dilution"
    assert r.ticker == "MITI"
    assert r.cost_microdollars == 9800
    assert r.credits_remaining_dollars == 47.23
    assert r.id is not None  # auto-assigned by DB


# ---------------------------------------------------------------------------
# 3. get_recent respects limit and returns newest first
# ---------------------------------------------------------------------------

def test_get_recent_limit():
    """Insert 3 records; get_recent(2) returns only 2, newest first."""
    db = _make_db()
    ts1 = "2026-06-20T10:00:00+00:00"
    ts2 = "2026-06-20T11:00:00+00:00"
    ts3 = "2026-06-20T12:00:00+00:00"

    db.insert(_record(ts=ts1))
    db.insert(_record(ts=ts2))
    db.insert(_record(ts=ts3))

    results = db.get_recent(2)
    assert len(results) == 2
    assert results[0].ts == ts3  # newest first
    assert results[1].ts == ts2


# ---------------------------------------------------------------------------
# 4. get_7d_summary excludes records older than 7 days
# ---------------------------------------------------------------------------

def test_get_7d_summary_excludes_old():
    """A record with ts 8 days ago must not appear in the 7-day summary."""
    db = _make_db()
    old_ts = _ts_days_ago(8)
    db.insert(_record(ts=old_ts, consumer="danny", endpoint="/v1/dilution",
                      cost_microdollars=5000, credits_remaining_dollars=50.0))

    summary = db.get_7d_summary()
    assert summary == []


# ---------------------------------------------------------------------------
# 5. get_7d_summary sums cost_microdollars for same consumer+endpoint
# ---------------------------------------------------------------------------

def test_get_7d_summary_sums_correctly():
    """Two records with the same consumer+endpoint sum their cost_microdollars."""
    db = _make_db()
    recent_ts = _ts_days_ago(1)

    db.insert(_record(ts=recent_ts, consumer="danny", endpoint="/v1/dilution",
                      cost_microdollars=5000, credits_remaining_dollars=47.0))
    db.insert(_record(ts=recent_ts, consumer="danny", endpoint="/v1/dilution",
                      cost_microdollars=3000, credits_remaining_dollars=46.0))

    summary = db.get_7d_summary()
    assert len(summary) == 1
    consumer, endpoint, total = summary[0]
    assert consumer == "danny"
    assert endpoint == "/v1/dilution"
    assert total == 8000


# ---------------------------------------------------------------------------
# 6. get_latest_balance returns None on empty table
# ---------------------------------------------------------------------------

def test_get_latest_balance_empty():
    """get_latest_balance() returns None when no records exist."""
    db = _make_db()
    assert db.get_latest_balance() is None


# ---------------------------------------------------------------------------
# 7. get_latest_balance returns row with lexicographically latest ts
# ---------------------------------------------------------------------------

def test_get_latest_balance_correct():
    """Insert 2 records; get_latest_balance() returns the one with the later ts."""
    db = _make_db()
    ts_earlier = "2026-06-20T10:00:00+00:00"
    ts_later   = "2026-06-20T14:32:00+00:00"

    db.insert(_record(ts=ts_earlier, credits_remaining_dollars=50.0))
    db.insert(_record(ts=ts_later,   credits_remaining_dollars=47.23))

    result = db.get_latest_balance()
    assert result is not None
    balance, ts = result
    assert ts == ts_later
    assert balance == pytest.approx(47.23)


# ---------------------------------------------------------------------------
# 8. cost_microdollars=None is stored and retrieved as None
# ---------------------------------------------------------------------------

def test_cost_microdollars_nullable():
    """Inserting a record with cost_microdollars=None retrieves it as None."""
    db = _make_db()
    ts = "2026-06-20T14:32:00+00:00"
    db.insert(_record(ts=ts, cost_microdollars=None))

    results = db.get_recent(1)
    assert len(results) == 1
    assert results[0].cost_microdollars is None


# ---------------------------------------------------------------------------
# 9. cost_microdollars=0 is included in get_7d_summary (COALESCE treats 0 as 0)
# ---------------------------------------------------------------------------

def test_cost_microdollars_zero():
    """A record with cost_microdollars=0 contributes 0 to the 7-day summary sum."""
    db = _make_db()
    recent_ts = _ts_days_ago(1)

    db.insert(_record(ts=recent_ts, consumer="danny", endpoint="/v1/dilution",
                      cost_microdollars=0, credits_remaining_dollars=47.0))

    summary = db.get_7d_summary()
    assert len(summary) == 1
    consumer, endpoint, total = summary[0]
    assert consumer == "danny"
    assert endpoint == "/v1/dilution"
    assert total == 0  # present in summary, not skipped
