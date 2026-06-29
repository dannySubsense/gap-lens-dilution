from datetime import datetime, timezone
from typing import Optional, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from app.core.config import settings
from app.db.usage_log_db import UsageLogDB, UsageRecord
from app.api.v1.admin_auth import require_admin_key
from app.services.usage_capture_service import UsageCaptureService
from app.services.balance_refresh_service import BalanceRefreshService, BalanceProbeError

_admin_db = UsageLogDB(settings.usage_log_db_path)
_admin_db.init_db()

_usage_capture_admin = UsageCaptureService(db=_admin_db)
_balance_refresh = BalanceRefreshService(usage_capture=_usage_capture_admin)

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_key)],
)

KNOWN_CONSUMERS: list[str] = ["danny", "kenny", "jt", "market-data"]


class UsageWriteRequest(BaseModel):
    """Body for POST /api/v1/admin/usage (market-data self-report)."""

    consumer: str
    endpoint: str
    ticker: Optional[str] = None
    cost_microdollars: Optional[int] = None
    credits_remaining_dollars: float
    ts: Optional[str] = None

    @field_validator("ts")
    @classmethod
    def validate_ts_utc(cls, v: Optional[str]) -> Optional[str]:
        """Accept ISO 8601 UTC only. Normalize to YYYY-MM-DDTHH:MM:SS+00:00."""
        if v is None or v == "":
            return None
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError("ts must be a parseable ISO 8601 string")
        if dt.tzinfo is None or dt.utcoffset().total_seconds() != 0:
            raise ValueError("ts must be UTC (Z or +00:00 offset)")
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


class ConsumerEndpointRow(BaseModel):
    endpoint: str
    total_cost_dollars: float


class ConsumerSummaryRow(BaseModel):
    consumer: str
    total_cost_dollars: float
    by_endpoint: list[ConsumerEndpointRow]


class RecentRequestRow(BaseModel):
    id: int
    ts: str
    consumer: str
    endpoint: str
    ticker: Optional[str]
    cost_dollars: float


class AdminSummaryResponse(BaseModel):
    balance_dollars: Optional[float]
    balance_ts: Optional[str] = None
    alert_triggered: bool
    alert_threshold_dollars: float
    consumer_summary_7d: list[ConsumerSummaryRow]
    recent_requests: list[RecentRequestRow]


class RefreshBalanceResponse(BaseModel):
    balance_dollars: float
    balance_ts: str
    cost_dollars: Optional[float]


_PROBE_ERROR_STATUS: dict[str, int] = {
    "null_usage":     502,
    "api_error":      502,
    "rate_limit":     503,
    "timeout":        504,
    "network":        504,
    "capture_failed": 502,
}


@admin_router.get("/summary", response_model=AdminSummaryResponse)
async def get_admin_summary() -> AdminSummaryResponse:
    """
    Build the admin summary response:
    1. Post-fill KNOWN_CONSUMERS with $0.00 for any consumer absent from the 7-day window.
    2. Append an "unknown" row only when SUM(cost_microdollars) > 0 for that consumer.
       The unknown row always has by_endpoint=[].
    3. Balance and alert fields come from get_latest_balance().
    """
    result = _admin_db.get_latest_balance()
    balance_dollars = result[0] if result else None
    balance_ts = result[1] if result else None
    alert_triggered = (
        False
        if balance_dollars is None
        else balance_dollars < settings.alert_threshold_dollars
    )

    summary_rows = _admin_db.get_7d_summary()

    # Accumulate endpoint costs per known consumer; accumulate unknown total separately.
    consumer_endpoints: dict[str, dict[str, int]] = {c: {} for c in KNOWN_CONSUMERS}
    consumer_totals: dict[str, int] = {c: 0 for c in KNOWN_CONSUMERS}
    unknown_total: int = 0

    for consumer, endpoint, sum_cost_microdollars in summary_rows:
        if consumer in KNOWN_CONSUMERS:
            consumer_totals[consumer] += sum_cost_microdollars
            ep_map = consumer_endpoints[consumer]
            ep_map[endpoint] = ep_map.get(endpoint, 0) + sum_cost_microdollars
        else:
            unknown_total += sum_cost_microdollars

    consumer_summary_7d: list[ConsumerSummaryRow] = []
    for c in KNOWN_CONSUMERS:
        by_endpoint = [
            ConsumerEndpointRow(endpoint=ep, total_cost_dollars=cost / 1_000_000)
            for ep, cost in consumer_endpoints[c].items()
        ]
        consumer_summary_7d.append(
            ConsumerSummaryRow(
                consumer=c,
                total_cost_dollars=consumer_totals[c] / 1_000_000,
                by_endpoint=by_endpoint,
            )
        )

    if unknown_total > 0:
        consumer_summary_7d.append(
            ConsumerSummaryRow(
                consumer="unknown",
                total_cost_dollars=unknown_total / 1_000_000,
                by_endpoint=[],
            )
        )

    records = _admin_db.get_recent(limit=50)
    recent_requests = [
        RecentRequestRow(
            id=record.id,
            ts=record.ts,
            consumer=record.consumer,
            endpoint=record.endpoint,
            ticker=record.ticker,
            cost_dollars=(record.cost_microdollars or 0) / 1_000_000,
        )
        for record in records
    ]

    return AdminSummaryResponse(
        balance_dollars=balance_dollars,
        balance_ts=balance_ts,
        alert_triggered=alert_triggered,
        alert_threshold_dollars=settings.alert_threshold_dollars,
        consumer_summary_7d=consumer_summary_7d,
        recent_requests=recent_requests,
    )


@admin_router.post("/refresh-balance", response_model=RefreshBalanceResponse)
async def refresh_balance() -> Union[RefreshBalanceResponse, JSONResponse]:
    try:
        balance_dollars, balance_ts, cost_dollars = await _balance_refresh.probe()
        return RefreshBalanceResponse(
            balance_dollars=balance_dollars,
            balance_ts=balance_ts,
            cost_dollars=cost_dollars,
        )
    except BalanceProbeError as exc:
        return JSONResponse(
            status_code=_PROBE_ERROR_STATUS[exc.code],
            content={"code": exc.code, "detail": exc.detail},
        )


@admin_router.post("/usage", status_code=200)
async def post_usage(body: UsageWriteRequest) -> dict:
    """
    Market-data self-report endpoint. Validates consumer == 'market-data'.

    When ts is absent from the request body, generates it with
    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00") — not .isoformat().
    """
    if body.consumer != "market-data":
        raise HTTPException(status_code=400, detail="consumer must be 'market-data'")

    ts = (
        body.ts
        if body.ts
        else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    )

    record = UsageRecord(
        id=None,
        ts=ts,
        consumer=body.consumer,
        endpoint=body.endpoint,
        ticker=body.ticker,
        cost_microdollars=body.cost_microdollars,
        credits_remaining_dollars=body.credits_remaining_dollars,
    )
    _admin_db.insert(record)
    return {"ok": True}
