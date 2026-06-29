"""
Tests for BalanceRefreshService and BalanceProbeError (Slice 2).

All tests are async — asyncio_mode=auto is configured in pytest.ini.
The httpx client is replaced on each service instance via svc._client
so that no real network calls are made.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.balance_refresh_service import BalanceRefreshService, BalanceProbeError
from app.services.usage_capture_service import UsageCaptureService


# ---------------------------------------------------------------------------
# Shared fixtures and helpers
# ---------------------------------------------------------------------------

VALID_TS = "2026-06-28T14:32:01+00:00"

VALID_USAGE = {
    "cost_microdollars": 9649,
    "credits_remaining_dollars": 12.45,
}

VALID_RESPONSE_BODY = {"usage": VALID_USAGE, "data": {}}


def _make_response(status_code: int, body: dict = None) -> MagicMock:
    """Return a mock httpx Response with the given status code and JSON body."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    if body is not None:
        mock_resp.json.return_value = body
    return mock_resp


def _make_svc(capture_return=VALID_TS):
    """
    Create a BalanceRefreshService backed by a mock UsageCaptureService.

    Returns (svc, mock_capture) so tests can inspect capture() call args.
    The service's internal httpx client is NOT replaced here — each test that
    needs to control HTTP responses should set svc._client after calling this.
    """
    mock_capture = MagicMock(spec=UsageCaptureService)
    mock_capture.capture.return_value = capture_return
    svc = BalanceRefreshService(usage_capture=mock_capture)
    return svc, mock_capture


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


async def test_probe_success_returns_tuple():
    """Happy path: 200 response with valid usage → returns (float, str, float)."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    svc._client.get = AsyncMock(return_value=_make_response(200, VALID_RESPONSE_BODY))

    result = await svc.probe()
    balance_dollars, balance_ts, cost_dollars = result

    assert isinstance(balance_dollars, float)
    assert balance_dollars == 12.45
    assert isinstance(balance_ts, str)
    assert balance_ts == VALID_TS
    assert isinstance(cost_dollars, float)
    assert cost_dollars == pytest.approx(9649 / 1_000_000)


async def test_probe_null_usage_raises_balance_probe_error():
    """200 response with usage: null → BalanceProbeError(code='null_usage')."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    svc._client.get = AsyncMock(return_value=_make_response(200, {"usage": None}))

    with pytest.raises(BalanceProbeError) as exc_info:
        await svc.probe()
    assert exc_info.value.code == "null_usage"


async def test_probe_missing_credits_remaining_raises_balance_probe_error():
    """200 response with usage present but no credits_remaining_dollars → null_usage."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    svc._client.get = AsyncMock(
        return_value=_make_response(200, {"usage": {"cost_microdollars": 9000}})
    )

    with pytest.raises(BalanceProbeError) as exc_info:
        await svc.probe()
    assert exc_info.value.code == "null_usage"


async def test_probe_rate_limit_retries_then_raises():
    """429 on all 3 attempts → BalanceProbeError(code='rate_limit') after 3 calls."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    svc._client.get = AsyncMock(return_value=_make_response(429))

    with patch(
        "app.services.balance_refresh_service.asyncio.sleep", new_callable=AsyncMock
    ) as mock_sleep:
        with pytest.raises(BalanceProbeError) as exc_info:
            await svc.probe()

    assert exc_info.value.code == "rate_limit"
    assert svc._client.get.call_count == 3
    # Slept after attempts 0 and 1 (not after the final attempt that raises)
    assert mock_sleep.call_count == 2


async def test_probe_api_error_raises():
    """Non-429 4xx/5xx → BalanceProbeError(code='api_error')."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    svc._client.get = AsyncMock(return_value=_make_response(500))

    with pytest.raises(BalanceProbeError) as exc_info:
        await svc.probe()
    assert exc_info.value.code == "api_error"


async def test_probe_timeout_raises():
    """httpx.TimeoutException → BalanceProbeError(code='timeout')."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    svc._client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    with pytest.raises(BalanceProbeError) as exc_info:
        await svc.probe()
    assert exc_info.value.code == "timeout"


async def test_probe_network_error_raises():
    """httpx.RequestError → BalanceProbeError(code='network')."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    svc._client.get = AsyncMock(
        side_effect=httpx.RequestError("connection refused")
    )

    with pytest.raises(BalanceProbeError) as exc_info:
        await svc.probe()
    assert exc_info.value.code == "network"


async def test_probe_capture_returns_none_raises_capture_failed():
    """Successful AskEdgar call but capture() returns None → capture_failed."""
    svc, _ = _make_svc(capture_return=None)
    svc._client = MagicMock()
    svc._client.get = AsyncMock(return_value=_make_response(200, VALID_RESPONSE_BODY))

    with pytest.raises(BalanceProbeError) as exc_info:
        await svc.probe()
    assert exc_info.value.code == "capture_failed"


async def test_probe_writes_consumer_tag():
    """probe() must call capture() with consumer='admin-refresh'."""
    svc, mock_capture = _make_svc()
    svc._client = MagicMock()
    svc._client.get = AsyncMock(return_value=_make_response(200, VALID_RESPONSE_BODY))

    await svc.probe()

    mock_capture.capture.assert_called_once_with(
        "/v1/dilution-rating",
        "AAPL",
        VALID_USAGE,
        consumer="admin-refresh",
    )


async def test_cost_dollars_calculation():
    """cost_microdollars=9649 → cost_dollars ≈ 9649/1_000_000."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    usage = {"cost_microdollars": 9649, "credits_remaining_dollars": 12.45}
    svc._client.get = AsyncMock(return_value=_make_response(200, {"usage": usage}))

    _, _, cost_dollars = await svc.probe()

    assert cost_dollars == pytest.approx(9649 / 1_000_000)


async def test_cost_dollars_none_when_microdollars_absent():
    """usage without cost_microdollars key → cost_dollars is None (not an error)."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    usage = {"credits_remaining_dollars": 12.45}  # no cost_microdollars
    svc._client.get = AsyncMock(return_value=_make_response(200, {"usage": usage}))

    _, _, cost_dollars = await svc.probe()

    assert cost_dollars is None


async def test_close_closes_client():
    """close() must call aclose() on the internal httpx.AsyncClient."""
    svc, _ = _make_svc()
    svc._client = MagicMock()
    svc._client.aclose = AsyncMock()

    await svc.close()

    svc._client.aclose.assert_called_once()
