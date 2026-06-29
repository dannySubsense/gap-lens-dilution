import re
from unittest.mock import MagicMock

import pytest

from app.core.consumer_context import set_current_consumer
from app.db.usage_log_db import UsageLogDB
from app.services.usage_capture_service import UsageCaptureService


def _make_db() -> UsageLogDB:
    db = UsageLogDB(":memory:")
    db.init_db()
    return db


VALID_USAGE = {
    "cost_microdollars": 9649,
    "credits_remaining_dollars": 12.34,
}


def test_successful_capture_writes_record():
    db = _make_db()
    svc = UsageCaptureService(db)
    set_current_consumer("danny")
    svc.capture("/filings", "AAPL", VALID_USAGE)
    records = db.get_recent(1)
    assert len(records) == 1
    assert records[0].consumer == "danny"


def test_successful_capture_ts_format():
    db = _make_db()
    svc = UsageCaptureService(db)
    svc.capture("/filings", "AAPL", VALID_USAGE)
    records = db.get_recent(1)
    assert len(records) == 1
    ts_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")
    assert ts_pattern.match(records[0].ts), (
        f"ts '{records[0].ts}' does not match expected format"
    )


def test_capture_none_usage_dict():
    db = _make_db()
    svc = UsageCaptureService(db)
    svc.capture("/filings", "AAPL", None)
    assert db.get_recent(1) == []


def test_capture_empty_usage_dict():
    db = _make_db()
    svc = UsageCaptureService(db)
    svc.capture("/filings", "AAPL", {})
    assert db.get_recent(1) == []


def test_capture_missing_credits_remaining():
    db = _make_db()
    svc = UsageCaptureService(db)
    svc.capture("/filings", "AAPL", {"cost_microdollars": 9649})
    assert db.get_recent(1) == []


def test_capture_db_raises_no_propagation():
    mock_db = MagicMock(spec=UsageLogDB)
    mock_db.insert.side_effect = RuntimeError("DB exploded")
    svc = UsageCaptureService(mock_db)
    # Must not raise
    svc.capture("/filings", "AAPL", VALID_USAGE)


def test_cost_microdollars_none():
    db = _make_db()
    svc = UsageCaptureService(db)
    usage = {"credits_remaining_dollars": 12.34}
    svc.capture("/filings", "AAPL", usage)
    records = db.get_recent(1)
    assert len(records) == 1
    assert records[0].cost_microdollars is None


def test_cost_microdollars_zero():
    db = _make_db()
    svc = UsageCaptureService(db)
    usage = {"cost_microdollars": 0, "credits_remaining_dollars": 12.34}
    svc.capture("/filings", "AAPL", usage)
    records = db.get_recent(1)
    assert len(records) == 1
    assert records[0].cost_microdollars == 0


def test_consumer_override_writes_explicit_consumer():
    db = _make_db()
    svc = UsageCaptureService(db)
    set_current_consumer("danny")
    svc.capture("/v1/dilution-rating", "AAPL", VALID_USAGE, consumer="admin-refresh")
    records = db.get_recent(1)
    assert len(records) == 1
    assert records[0].consumer == "admin-refresh"


def test_capture_returns_ts_string_on_success():
    db = _make_db()
    svc = UsageCaptureService(db)
    result = svc.capture("/filings", "AAPL", VALID_USAGE)
    assert result is not None
    ts_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")
    assert ts_pattern.match(result), (
        f"return value '{result}' does not match expected YYYY-MM-DDTHH:MM:SS+00:00 format"
    )


def test_capture_returns_none_on_empty_usage():
    db = _make_db()
    svc = UsageCaptureService(db)
    result = svc.capture("/ep", "T", {})
    assert result is None
