import asyncio
import sqlite3
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import httpx

from app.core.config import settings
from app.db.market_strength_db import MarketStrengthDB, MarketStrengthSnapshot


def _now_et() -> datetime:
    """Return the current wall-clock time in US/Eastern (ET).

    Exposed as a module-level function so tests can monkeypatch it to a fixed
    datetime without touching internal service state.
    """
    return datetime.now(ZoneInfo("America/New_York"))


class MarketStrengthCaptureError(Exception):
    """Raised when the capture job encounters a non-recoverable error
    (AskEdgar 5xx, SQLite write failure)."""


class MarketStrengthService:
    def __init__(self, db: MarketStrengthDB, http_client: httpx.AsyncClient) -> None:
        self.db = db
        self.http_client = http_client

    async def capture(self) -> dict:
        """
        Fetch AskEdgar /v1/market-strength, upsert to SQLite.
        Returns {"status": "captured", "date": str} | {"status": "skipped", "reason": str}.
        Raises MarketStrengthCaptureError on 5xx or write failure.

        Idempotency: if a row already exists in the DB whose captured_at date
        (first 10 chars, ET calendar date) matches today's ET date, the method
        returns {"status": "skipped", "reason": "already_captured"} immediately
        without making any HTTP call.  Only a SUCCESSFUL capture writes
        captured_at — the no_data/404/empty paths do not suppress later retries.
        """
        import app.services.market_strength_service as _self_module

        now_et = _self_module._now_et()
        today_et = now_et.date().isoformat()  # "YYYY-MM-DD"

        # --- Idempotency guard ---
        last = self.db.get_latest_captured()
        if last is not None and last.captured_at[:10] == today_et:
            return {"status": "skipped", "reason": "already_captured"}

        try:
            response = await self.http_client.get(
                f"{settings.askedgar_url}/v1/market-strength",
                params={"latest": "true"},
            )
        except asyncio.TimeoutError as exc:
            raise MarketStrengthCaptureError(str(exc)) from exc
        except httpx.RequestError as exc:
            raise MarketStrengthCaptureError(str(exc)) from exc

        if response.status_code == 404:
            return {"status": "skipped", "reason": "no_data"}

        if response.status_code >= 500:
            raise MarketStrengthCaptureError("AskEdgar returned 5xx")

        response.raise_for_status()

        data = response.json()
        results = data.get("results")

        if results is not None and len(results) == 0:
            return {"status": "skipped", "reason": "no_data"}

        record = results[0] if results else data

        if not record.get("date"):
            return {"status": "skipped", "reason": "no_data"}

        snapshot = MarketStrengthSnapshot(
            date=record.get("date"),
            analysis=record.get("analysis"),
            performance=record.get("performance"),
            last_updated=record.get("last_updated"),
            captured_at=now_et.isoformat(),
        )

        try:
            self.db.upsert(snapshot)
        except sqlite3.Error as exc:
            raise MarketStrengthCaptureError(str(exc)) from exc

        return {"status": "captured", "date": snapshot.date}

    def get_latest_snapshot(self) -> Optional[MarketStrengthSnapshot]:
        """
        Synchronous read of the most recent row in SQLite, ordered by date descending.
        Returns None if the table is empty or on any Exception.
        Used by IntelService as the AskEdgar fallback path.
        """
        try:
            rows = self.db.get_history(limit=1)
            return rows[0] if rows else None
        except Exception:
            return None

    def get_history(
        self,
        date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list:
        """Delegate to MarketStrengthDB.get_history."""
        return self.db.get_history(date=date, limit=limit)
