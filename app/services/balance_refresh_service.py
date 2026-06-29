import asyncio
import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.services.usage_capture_service import UsageCaptureService

logger = logging.getLogger(__name__)


class BalanceProbeError(Exception):
    """Raised when the AskEdgar probe call cannot produce a valid balance row.

    code values:
      "null_usage"     — AskEdgar returned 200 OK but usage field is null or missing
                         credits_remaining_dollars (documented zero-balance silent failure)
      "rate_limit"     — AskEdgar 429 after all retries exhausted
      "api_error"      — AskEdgar returned a non-2xx status
      "timeout"        — httpx.TimeoutException after all retries exhausted
      "network"        — httpx.RequestError (DNS/TLS/connection failure)
      "capture_failed" — UsageCaptureService.capture() returned None (DB insert failed
                         or swallowed an exception); the AskEdgar call may have succeeded
                         but no usage row was written, so balance_ts is unavailable
    """

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class BalanceRefreshService:
    PROBE_ENDPOINT: str = "/v1/dilution-rating"
    PROBE_TICKER: str = "AAPL"
    CONSUMER_TAG: str = "admin-refresh"
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0  # seconds

    def __init__(self, usage_capture: UsageCaptureService) -> None:
        self._usage_capture = usage_capture
        self._client = httpx.AsyncClient(
            timeout=settings.request_timeout,
            headers={"API-KEY": settings.askedgar_api_key},
            follow_redirects=True,
        )

    async def probe(self) -> tuple[float, str, Optional[float]]:
        """Make one paid AskEdgar call to /v1/dilution-rating?ticker=AAPL.

        Returns:
            (balance_dollars, balance_ts, cost_dollars)
            cost_dollars is None when cost_microdollars is absent from the usage object.

        Raises:
            BalanceProbeError with code in {null_usage, rate_limit, api_error,
                                            timeout, network, capture_failed}

        capture_failed contract:
            After a successful AskEdgar response, probe() calls capture() and checks
            its return value. If capture() returns None for any reason (DB insert
            exception swallowed internally, or any documented early-exit path),
            probe() raises BalanceProbeError("capture_failed"). This prevents the
            handler from returning a RefreshBalanceResponse with a None balance_ts,
            which would fail Pydantic validation and produce an unhandled 500.

        cost_dollars contract:
            raw_cost = usage.get("cost_microdollars")
            cost_dollars = raw_cost / 1_000_000 if raw_cost is not None else None
            A None cost_dollars is not an error — probe() returns it as-is.
        """
        url = f"{settings.askedgar_url}{self.PROBE_ENDPOINT}?ticker={self.PROBE_TICKER}"

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.get(url)
            except httpx.TimeoutException:
                raise BalanceProbeError("timeout", "AskEdgar request timed out")
            except httpx.RequestError as e:
                raise BalanceProbeError("network", str(e))

            if response.status_code == 429:
                if attempt == self.MAX_RETRIES - 1:
                    raise BalanceProbeError(
                        "rate_limit", "AskEdgar rate limit exceeded after retries"
                    )
                await asyncio.sleep(self.RETRY_DELAY)
                continue

            if response.status_code >= 400:
                raise BalanceProbeError("api_error", str(response.status_code))

            # 200 OK path — parse usage object
            data = response.json()
            usage = data.get("usage")
            if usage is None or "credits_remaining_dollars" not in usage:
                raise BalanceProbeError(
                    "null_usage",
                    "AskEdgar returned usage: null or missing credits_remaining_dollars",
                )

            ts = self._usage_capture.capture(
                self.PROBE_ENDPOINT,
                self.PROBE_TICKER,
                usage,
                consumer=self.CONSUMER_TAG,
            )
            if ts is None:
                raise BalanceProbeError(
                    "capture_failed",
                    "UsageCaptureService.capture() returned None",
                )

            raw_cost = usage.get("cost_microdollars")
            cost_dollars = raw_cost / 1_000_000 if raw_cost is not None else None

            raw_balance = usage["credits_remaining_dollars"]
            if isinstance(raw_balance, str):
                raw_balance = float(raw_balance.lstrip("$").replace(",", ""))
            balance_dollars = float(raw_balance)

            return (balance_dollars, ts, cost_dollars)

        # Unreachable with MAX_RETRIES > 0 — only 429 paths continue the loop,
        # and the final 429 raises before the loop can exhaust naturally.
        raise BalanceProbeError("rate_limit", "AskEdgar rate limit exceeded after retries")

    async def close(self) -> None:
        """Close the internal httpx.AsyncClient."""
        await self._client.aclose()
