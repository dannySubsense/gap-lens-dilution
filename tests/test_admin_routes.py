"""
Tests for the admin APIRouter (Slice 6).

Uses FastAPI TestClient with a fresh :memory: UsageLogDB injected via monkeypatch
on the module-level _admin_db attribute so every test starts from an empty database.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.v1.admin_routes as admin_module
from app.db.usage_log_db import UsageLogDB, UsageRecord


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    """Replace the module-level _admin_db with a fresh :memory: instance.

    Pre-sets _conn with check_same_thread=False so the TestClient's async
    event loop thread can share the in-memory connection created here.
    Disables ADMIN_API_KEY so tests don't need to send auth headers.
    """
    import sqlite3 as _sqlite3
    from app.core.config import settings

    db = UsageLogDB(":memory:")
    db._conn = _sqlite3.connect(":memory:", check_same_thread=False)
    db.init_db()
    monkeypatch.setattr(admin_module, "_admin_db", db)
    monkeypatch.setattr(settings, "admin_api_key", "")
    return db


@pytest.fixture
def client():
    app = FastAPI()
    from app.api.v1.admin_routes import admin_router

    app.include_router(admin_router, prefix="/api/v1")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _insert(db: UsageLogDB, **kwargs) -> None:
    defaults = dict(
        id=None,
        ts="2026-06-20T10:00:00+00:00",
        consumer="danny",
        endpoint="/v1/dilution",
        ticker="MITI",
        cost_microdollars=9000,
        credits_remaining_dollars=45.0,
    )
    defaults.update(kwargs)
    db.insert(UsageRecord(**defaults))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_get_summary_200(client):
    """GET /summary returns 200 with required top-level fields."""
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "balance_dollars" in data
    assert "alert_triggered" in data
    assert "consumer_summary_7d" in data
    assert "recent_requests" in data


def test_empty_db_balance_null_alert_false(client):
    """Empty DB: balance_dollars is null, balance_ts is null, alert_triggered is false,
    alert_threshold_dollars is 5.0, and all four named consumers are present with zeroed spend."""
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance_dollars"] is None
    assert data["balance_ts"] is None
    assert data["alert_triggered"] is False
    assert data["alert_threshold_dollars"] == 5.0
    summary = data["consumer_summary_7d"]
    assert len(summary) == 4
    consumers = [row["consumer"] for row in summary]
    for c in ["danny", "kenny", "jt", "market-data"]:
        assert c in consumers
    for row in summary:
        assert row["total_cost_dollars"] == 0.0
        assert row["by_endpoint"] == []


def test_alert_triggered_below_threshold(fresh_db, client):
    """Insert record with credits_remaining_dollars=1.0 (below $5 threshold): alert is true."""
    _insert(fresh_db, credits_remaining_dollars=1.0)
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    assert resp.json()["alert_triggered"] is True


def test_alert_not_triggered_above_threshold(fresh_db, client):
    """Insert record with credits_remaining_dollars=10.0 (above $5 threshold): alert is false."""
    _insert(fresh_db, credits_remaining_dollars=10.0)
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    assert resp.json()["alert_triggered"] is False


def test_all_four_consumers_present(fresh_db, client):
    """Insert a record for 'danny' only; all four named consumers must appear."""
    _insert(fresh_db, consumer="danny")
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    consumers = [row["consumer"] for row in resp.json()["consumer_summary_7d"]]
    for c in ["danny", "kenny", "jt", "market-data"]:
        assert c in consumers


def test_post_usage_market_data_ok(client):
    """POST with consumer='market-data' returns 200 {"ok": true}."""
    payload = {
        "consumer": "market-data",
        "endpoint": "/v1/dilution",
        "ticker": "MITI",
        "cost_microdollars": 9649,
        "credits_remaining_dollars": 45.83,
        "ts": "2026-06-20T09:00:00+00:00",
    }
    resp = client.post("/api/v1/admin/usage", json=payload)
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}


def test_post_usage_danny_rejected(client):
    """POST with consumer='danny' returns 400."""
    payload = {
        "consumer": "danny",
        "endpoint": "/v1/dilution",
        "credits_remaining_dollars": 45.83,
    }
    resp = client.post("/api/v1/admin/usage", json=payload)
    assert resp.status_code == 400


def test_post_usage_no_ts_auto_generated(client):
    """POST with no ts field: record is written (auto-generated ts)."""
    payload = {
        "consumer": "market-data",
        "endpoint": "/v1/market-strength",
        "credits_remaining_dollars": 40.0,
    }
    resp = client.post("/api/v1/admin/usage", json=payload)
    assert resp.status_code == 200

    summary = client.get("/api/v1/admin/summary").json()
    assert len(summary["recent_requests"]) == 1


def test_get_summary_shows_posted_record(client):
    """POST a record then GET: record appears in recent_requests."""
    payload = {
        "consumer": "market-data",
        "endpoint": "/v1/dilution",
        "ticker": "AAPL",
        "cost_microdollars": 5000,
        "credits_remaining_dollars": 42.0,
        "ts": "2026-06-20T11:00:00+00:00",
    }
    client.post("/api/v1/admin/usage", json=payload)

    summary = client.get("/api/v1/admin/summary").json()
    recent = summary["recent_requests"]
    assert len(recent) == 1
    assert recent[0]["consumer"] == "market-data"
    assert recent[0]["endpoint"] == "/v1/dilution"
    assert recent[0]["ticker"] == "AAPL"
    assert isinstance(recent[0]["id"], int)
    assert isinstance(summary["balance_ts"], str) and len(summary["balance_ts"]) > 0


def test_recent_requests_empty_list_not_null(client):
    """Empty DB: recent_requests is [] not null."""
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["recent_requests"] == []


def test_ticker_null_in_recent_requests(fresh_db, client):
    """A record with ticker=None appears in recent_requests with ticker: null."""
    _insert(fresh_db, ticker=None)
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    recent = resp.json()["recent_requests"]
    assert len(recent) == 1
    assert recent[0]["ticker"] is None


def test_cost_microdollars_null_shows_zero_dollars(fresh_db, client):
    """A record with cost_microdollars=None appears in recent_requests with cost_dollars=0.0."""
    _insert(fresh_db, cost_microdollars=None)
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    recent = resp.json()["recent_requests"]
    assert len(recent) == 1
    assert recent[0]["cost_dollars"] == 0.0


def test_post_usage_malformed_ts_rejected(client):
    """POST with a non-parseable ts value returns 422."""
    resp = client.post("/api/v1/admin/usage", json={
        "consumer": "market-data",
        "endpoint": "/v1/float-outstanding",
        "credits_remaining_dollars": 45.83,
        "ts": "not-a-timestamp",
    })
    assert resp.status_code == 422
