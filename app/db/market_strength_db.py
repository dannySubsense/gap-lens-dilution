import os
import sqlite3
from dataclasses import dataclass
from typing import Optional


@dataclass
class MarketStrengthSnapshot:
    date: str
    analysis: Optional[str]
    performance: Optional[str]
    last_updated: Optional[str]
    captured_at: Optional[str] = None


class MarketStrengthDB:
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
        method calls within the same MarketStrengthDB instance.
        """
        if self.db_path == ":memory:":
            if self._conn is None:
                self._conn = sqlite3.connect(self.db_path)
            return self._conn
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        """Create the SQLite file and table if they do not exist. Idempotent.

        Also adds the captured_at column to existing databases that predate it,
        using PRAGMA table_info to check before issuing ALTER TABLE.
        """
        if self.db_path != ":memory:":
            parent = os.path.dirname(self.db_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS market_strength_snapshots (
                    date         TEXT PRIMARY KEY NOT NULL,
                    analysis     TEXT,
                    performance  TEXT,
                    last_updated TEXT,
                    captured_at  TEXT
                )
                """
            )
            # Add captured_at to existing databases that predate this column.
            columns = {
                row[1]
                for row in conn.execute(
                    "PRAGMA table_info(market_strength_snapshots)"
                ).fetchall()
            }
            if "captured_at" not in columns:
                conn.execute(
                    "ALTER TABLE market_strength_snapshots ADD COLUMN captured_at TEXT"
                )
            conn.commit()
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def upsert(self, snapshot: MarketStrengthSnapshot) -> None:
        """INSERT OR REPLACE into market_strength_snapshots."""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO market_strength_snapshots "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    snapshot.date,
                    snapshot.analysis,
                    snapshot.performance,
                    snapshot.last_updated,
                    snapshot.captured_at,
                ),
            )
            conn.commit()
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_by_date(self, date: str) -> Optional[MarketStrengthSnapshot]:
        """Return the row matching the given date, or None."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT date, analysis, performance, last_updated, captured_at "
                "FROM market_strength_snapshots WHERE date = ?",
                (date,),
            ).fetchone()
        finally:
            if self.db_path != ":memory:":
                conn.close()
        if row is None:
            return None
        return MarketStrengthSnapshot(
            date=row[0],
            analysis=row[1],
            performance=row[2],
            last_updated=row[3],
            captured_at=row[4],
        )

    def get_latest_captured(self) -> Optional["MarketStrengthSnapshot"]:
        """Return the row with the most recent captured_at, or None.

        Ignores rows with NULL captured_at (pre-migration rows). Used by the
        capture() idempotency guard so it checks capture time, not market date.
        """
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT date, analysis, performance, last_updated, captured_at "
                "FROM market_strength_snapshots "
                "WHERE captured_at IS NOT NULL "
                "ORDER BY captured_at DESC LIMIT 1"
            ).fetchone()
        finally:
            if self.db_path != ":memory:":
                conn.close()
        if row is None:
            return None
        return MarketStrengthSnapshot(
            date=row[0],
            analysis=row[1],
            performance=row[2],
            last_updated=row[3],
            captured_at=row[4],
        )

    def get_history(
        self,
        date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list:
        """
        Return rows sorted descending by date.
        Filtered by exact date match when date is provided.
        Truncated to limit rows when limit is not None (limit=0 returns []).
        """
        if limit == 0:
            return []

        query = (
            "SELECT date, analysis, performance, last_updated, captured_at "
            "FROM market_strength_snapshots"
        )
        params: list = []

        if date is not None:
            query += " WHERE date = ?"
            params.append(date)

        query += " ORDER BY date DESC"

        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)

        conn = self._connect()
        try:
            rows = conn.execute(query, params).fetchall()
        finally:
            if self.db_path != ":memory:":
                conn.close()

        return [
            MarketStrengthSnapshot(
                date=row[0],
                analysis=row[1],
                performance=row[2],
                last_updated=row[3],
                captured_at=row[4],
            )
            for row in rows
        ]
