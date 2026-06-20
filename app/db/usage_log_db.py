import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


@dataclass
class UsageRecord:
    ts: str
    consumer: str
    endpoint: str
    ticker: Optional[str]
    cost_microdollars: Optional[int]
    credits_remaining_dollars: float
    id: Optional[int] = None


class UsageLogDB:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        # Connection is not opened here; each method calls _connect().
        # For :memory: databases, the same connection must be reused across
        # calls because each sqlite3.connect(':memory:') creates a new empty
        # database. The _conn attribute caches the connection for :memory: paths.
        self._conn: Optional[sqlite3.Connection] = None

    def _connect(self) -> sqlite3.Connection:
        """Return a connection for this database path.

        For file-backed databases, opens a new connection (caller uses it as a
        context manager and it is closed on exit).  For :memory: databases,
        returns a single cached connection so that DDL and data survive across
        method calls within the same UsageLogDB instance.
        """
        if self.db_path == ":memory:":
            if self._conn is None:
                self._conn = sqlite3.connect(self.db_path)
            return self._conn
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        """Create the SQLite file and table if they do not exist. Idempotent."""
        if self.db_path != ":memory:":
            parent = os.path.dirname(self.db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS askedgar_usage_log (
                    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts                        TEXT    NOT NULL,
                    consumer                  TEXT    NOT NULL,
                    endpoint                  TEXT    NOT NULL,
                    ticker                    TEXT,
                    cost_microdollars         INTEGER,
                    credits_remaining_dollars REAL    NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_usage_ts "
                "ON askedgar_usage_log (ts)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_usage_consumer "
                "ON askedgar_usage_log (consumer)"
            )
            conn.execute("PRAGMA journal_mode = WAL")
            conn.commit()
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def insert(self, record: UsageRecord) -> None:
        """INSERT a new row; id is assigned by the database (AUTOINCREMENT)."""
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO askedgar_usage_log
                    (ts, consumer, endpoint, ticker,
                     cost_microdollars, credits_remaining_dollars)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.ts,
                    record.consumer,
                    record.endpoint,
                    record.ticker,
                    record.cost_microdollars,
                    record.credits_remaining_dollars,
                ),
            )
            conn.commit()
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_recent(self, limit: int = 50) -> list[UsageRecord]:
        """Return the most recent rows, newest first."""
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT id, ts, consumer, endpoint, ticker,
                       cost_microdollars, credits_remaining_dollars
                FROM askedgar_usage_log
                ORDER BY ts DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        finally:
            if self.db_path != ":memory:":
                conn.close()
        return [
            UsageRecord(
                id=row[0],
                ts=row[1],
                consumer=row[2],
                endpoint=row[3],
                ticker=row[4],
                cost_microdollars=row[5],
                credits_remaining_dollars=row[6],
            )
            for row in rows
        ]

    def get_7d_summary(self) -> list[tuple[str, str, int]]:
        """Return (consumer, endpoint, sum_cost_microdollars) for the last 7 days.

        Uses COALESCE(cost_microdollars, 0) so NULL cost rows contribute 0 to
        the sum rather than being silently excluded.  Cutoff is computed with
        datetime.now(timezone.utc) — not datetime.utcnow() (deprecated Python 3.12).
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M:%S+00:00"
        )
        conn = self._connect()
        try:
            rows = conn.execute(
                """
                SELECT consumer, endpoint,
                       SUM(COALESCE(cost_microdollars, 0))
                FROM askedgar_usage_log
                WHERE ts >= ?
                GROUP BY consumer, endpoint
                """,
                (cutoff,),
            ).fetchall()
        finally:
            if self.db_path != ":memory:":
                conn.close()
        return [(row[0], row[1], row[2]) for row in rows]

    def get_latest_balance(self) -> tuple[float, str] | None:
        """Return (credits_remaining_dollars, ts) of the newest record, or None.

        Uses ORDER BY ts DESC LIMIT 1.  Lexicographic sort is correct only when
        all stored ts values share the canonical YYYY-MM-DDTHH:MM:SS+00:00 format.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT credits_remaining_dollars, ts
                FROM askedgar_usage_log
                ORDER BY ts DESC
                LIMIT 1
                """
            ).fetchone()
        finally:
            if self.db_path != ":memory:":
                conn.close()
        if row is None:
            return None
        return (row[0], row[1])
