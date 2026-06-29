import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.db.usage_log_db import UsageLogDB, UsageRecord
from app.core.consumer_context import get_current_consumer

logger = logging.getLogger(__name__)


@dataclass
class RawUsagePayload:
    cost_microdollars: Optional[int]
    credits_remaining_dollars: float


class UsageCaptureService:
    def __init__(self, db: UsageLogDB) -> None:
        self.db = db

    def capture(self, endpoint: str, ticker: Optional[str], usage_dict: dict, consumer: Optional[str] = None) -> Optional[str]:
        if not usage_dict:
            logger.warning(
                "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                endpoint,
                ticker,
            )
            return None
        if "credits_remaining_dollars" not in usage_dict:
            logger.warning(
                "AskEdgar response missing usage object: endpoint=%s ticker=%s",
                endpoint,
                ticker,
            )
            return None
        try:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
            consumer = consumer if consumer is not None else get_current_consumer()
            raw_balance = usage_dict["credits_remaining_dollars"]
            if isinstance(raw_balance, str):
                raw_balance = float(raw_balance.lstrip("$").replace(",", ""))
            record = UsageRecord(
                id=None,
                ts=ts,
                consumer=consumer,
                endpoint=endpoint,
                ticker=ticker,
                cost_microdollars=usage_dict.get("cost_microdollars"),
                credits_remaining_dollars=float(raw_balance),
            )
            self.db.insert(record)
            return ts
        except Exception as e:
            logger.error("Failed to capture usage: %s", e)
            return None
