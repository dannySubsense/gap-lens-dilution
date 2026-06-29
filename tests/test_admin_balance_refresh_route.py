"""
Tests for POST /api/v1/admin/refresh-balance route (Slice 3).

Monkeypatches admin_module._balance_refresh with an AsyncMock so no real
AskEdgar calls are made.  Mirrors the fresh_db fixture pattern from
tests/test_admin_routes.py for _admin_db isolation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.api.v1.admin_routes as admin_module
from app.db.usage_log_db import UsageLogDB
from app.services.balance_refresh_service import BalanceProbeError
from app.middleware.tailscale_guard_middleware import TailscaleGuardMiddleware


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def fresh_db(monkeypatch):
    """Replace the module-level _admin_db with a fresh :memory: instance.

    Disables ADMIN_API_KEY so most tests do not need auth headers.
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
def mock_balance_refresh(monkeypatch):
    """Replace _balance_refresh with a MagicMock whose probe() is an AsyncMock."""
    mock = MagicMock()
    mock.probe = AsyncMock()
    monkeypatch.setattr(admin_module, "_balance_refresh", mock)
    return mock


@pytest.fixture
def client():
    """TestClient without TailscaleGuardMiddleware — for auth/behaviour tests."""
    app = FastAPI()
    from app.api.v1.admin_routes import admin_router

    app.include_router(admin_router, prefix="/api/v1")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_refresh_balance_200(mock_balance_refresh, client):
    """Successful probe returns 200 with balance_dollars, balance_ts, cost_dollars."""
    mock_balance_refresh.probe.return_value = (
        12.45,
        "2026-06-28T14:32:01+00:00",
        0.000012,
    )
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance_dollars"] == 12.45
    assert data["balance_ts"] == "2026-06-28T14:32:01+00:00"
    assert abs(data["cost_dollars"] - 0.000012) < 1e-10


def test_refresh_balance_200_cost_null(mock_balance_refresh, client):
    """Successful probe with None cost returns 200 and cost_dollars is null in JSON."""
    mock_balance_refresh.probe.return_value = (
        12.45,
        "2026-06-28T14:32:01+00:00",
        None,
    )
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 200
    data = resp.json()
    assert data["balance_dollars"] == 12.45
    assert data["cost_dollars"] is None


def test_refresh_balance_null_usage_returns_502(mock_balance_refresh, client):
    """BalanceProbeError('null_usage') → 502 with code field in body."""
    mock_balance_refresh.probe.side_effect = BalanceProbeError("null_usage")
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 502
    assert resp.json()["code"] == "null_usage"


def test_refresh_balance_api_error_returns_502(mock_balance_refresh, client):
    """BalanceProbeError('api_error') → 502 with code field in body."""
    mock_balance_refresh.probe.side_effect = BalanceProbeError("api_error", "404")
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 502
    assert resp.json()["code"] == "api_error"


def test_refresh_balance_capture_failed_returns_502(mock_balance_refresh, client):
    """BalanceProbeError('capture_failed') → 502 with code field in body."""
    mock_balance_refresh.probe.side_effect = BalanceProbeError("capture_failed")
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 502
    assert resp.json()["code"] == "capture_failed"


def test_refresh_balance_rate_limit_returns_503(mock_balance_refresh, client):
    """BalanceProbeError('rate_limit') → 503 with code field in body."""
    mock_balance_refresh.probe.side_effect = BalanceProbeError("rate_limit")
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 503
    assert resp.json()["code"] == "rate_limit"


def test_refresh_balance_timeout_returns_504(mock_balance_refresh, client):
    """BalanceProbeError('timeout') → 504 with code field in body."""
    mock_balance_refresh.probe.side_effect = BalanceProbeError("timeout")
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 504
    assert resp.json()["code"] == "timeout"


def test_refresh_balance_network_error_returns_504(mock_balance_refresh, client):
    """BalanceProbeError('network') → 504 with code field in body."""
    mock_balance_refresh.probe.side_effect = BalanceProbeError("network", "DNS")
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 504
    assert resp.json()["code"] == "network"


def test_refresh_balance_requires_tailscale_ip(mock_balance_refresh):
    """Non-Tailscale client IP → 403 from TailscaleGuardMiddleware (AC-11).

    TestClient's default scope client address is ('testclient', 50000), which
    does not start with '100.' or '127.', so the middleware returns 403.
    """
    app = FastAPI()
    from app.api.v1.admin_routes import admin_router

    app.add_middleware(TailscaleGuardMiddleware)
    app.include_router(admin_router, prefix="/api/v1")
    tc = TestClient(app, raise_server_exceptions=False)
    resp = tc.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 403


def test_refresh_balance_requires_bearer_token(mock_balance_refresh, client, monkeypatch):
    """Missing Authorization header with admin_api_key set → 401 (AC-12)."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "admin_api_key", "secret")
    resp = client.post("/api/v1/admin/refresh-balance")
    assert resp.status_code == 401


def test_get_summary_no_askedgar_call(mock_balance_refresh, client):
    """GET /summary must not invoke _balance_refresh.probe (AC-15)."""
    resp = client.get("/api/v1/admin/summary")
    assert resp.status_code == 200
    mock_balance_refresh.probe.assert_not_called()
