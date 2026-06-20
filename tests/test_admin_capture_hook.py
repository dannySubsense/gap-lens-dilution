"""
Slice 7: DilutionService + IntelService capture hook injection

Tests:
1. DilutionService._make_request calls capture() when usage_capture_service is set and "usage" key present
2. DilutionService._make_request does NOT call capture() when usage_capture_service=None
3. DilutionService._make_request does NOT call capture() and logs WARNING when "usage" key absent
4. IntelService.get_pump_and_dump calls capture() with correct endpoint literal and ticker
5. DilutionService() (no args) initializes without error; _usage_capture is None
6. IntelService(dilution_svc, None) (no usage arg) initializes without error; _usage_capture is None
"""

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.dilution import DilutionService
from app.services.intel import IntelService


USAGE_DICT = {"cost_microdollars": 9649, "credits_remaining_dollars": 45.83}


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Build a mock httpx response that returns json_data from .json()."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


# ---------------------------------------------------------------------------
# Test 1: capture() called when usage_capture_service is set and usage present
# ---------------------------------------------------------------------------

async def test_dilution_make_request_calls_capture():
    mock_svc = MagicMock()
    svc = DilutionService(usage_capture_service=mock_svc)

    json_data = {
        "usage": USAGE_DICT,
        "results": [{"ticker": "AAPL"}],
    }
    svc.client.get = AsyncMock(return_value=_mock_response(json_data))

    await svc._make_request("/v1/screener", "AAPL")

    mock_svc.capture.assert_called_once_with("/v1/screener", "AAPL", USAGE_DICT)


# ---------------------------------------------------------------------------
# Test 2: capture() NOT called when usage_capture_service=None
# ---------------------------------------------------------------------------

async def test_dilution_make_request_no_service():
    svc = DilutionService(usage_capture_service=None)

    json_data = {
        "usage": USAGE_DICT,
        "results": [{"ticker": "AAPL"}],
    }
    svc.client.get = AsyncMock(return_value=_mock_response(json_data))

    # Must not raise; capture is simply not called
    await svc._make_request("/v1/screener", "AAPL")

    # No capture service to assert on — pass if no exception raised


# ---------------------------------------------------------------------------
# Test 3: capture() NOT called and WARNING logged when "usage" key absent
# ---------------------------------------------------------------------------

async def test_dilution_make_request_no_usage_key(caplog):
    mock_svc = MagicMock()
    svc = DilutionService(usage_capture_service=mock_svc)

    json_data = {"results": [{"ticker": "AAPL"}]}  # no "usage" key
    svc.client.get = AsyncMock(return_value=_mock_response(json_data))

    with caplog.at_level(logging.WARNING, logger="app.services.dilution"):
        await svc._make_request("/v1/screener", "AAPL")

    mock_svc.capture.assert_not_called()
    assert any("missing usage object" in record.message for record in caplog.records), (
        "Expected WARNING about missing usage object to be logged"
    )


# ---------------------------------------------------------------------------
# Test 4: IntelService.get_pump_and_dump calls capture() correctly
# ---------------------------------------------------------------------------

async def test_intel_capture_called():
    mock_svc = MagicMock()
    dilution_svc = DilutionService()
    intel_svc = IntelService(dilution_svc, None, usage_capture_service=mock_svc)

    json_data = {
        "usage": USAGE_DICT,
        "results": [{"ticker": "AAPL", "score": 72}],
    }
    intel_svc.client.get = AsyncMock(return_value=_mock_response(json_data))

    await intel_svc.get_pump_and_dump("AAPL")

    mock_svc.capture.assert_called_once_with(
        "/v1/pump-and-dump-tracker", "AAPL", USAGE_DICT
    )


# ---------------------------------------------------------------------------
# Test 5: DilutionService() (no args) initializes without error
# ---------------------------------------------------------------------------

def test_dilution_init_no_args_ok():
    svc = DilutionService()
    assert svc._usage_capture is None


# ---------------------------------------------------------------------------
# Test 6: IntelService(dilution_svc, None) (no usage arg) initializes without error
# ---------------------------------------------------------------------------

def test_intel_init_no_usage_arg_ok():
    dilution_svc = DilutionService()
    intel_svc = IntelService(dilution_svc, None)
    assert intel_svc._usage_capture is None
