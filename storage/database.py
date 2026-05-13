import sqlite3
from datetime import datetime, timezone
from typing import Optional


class Database:
    """SQLite-backed store for processed marketplace listings."""

    def __init__(self, db_path: str = "storage/listings.db") -> None:
        self._db_path = db_path
        # check_same_thread=False is safe here: the bot runs in a single
        # asyncio event loop and all DB calls are sequential.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_table()

    def _create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS listings (
                listing_id      TEXT PRIMARY KEY,
                timestamp_seen  TEXT NOT NULL,
                message_sent    INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._conn.commit()

    def is_seen(self, listing_id: str) -> bool:
        """Return True if the listing has already been processed."""
        cursor = self._conn.execute(
            "SELECT 1 FROM listings WHERE listing_id = ?", (listing_id,)
        )
        return cursor.fetchone() is not None

    def mark_seen(self, listing_id: str, message_sent: bool = False) -> None:
        """Record a listing as processed."""
        self._conn.execute(
            """
            INSERT OR IGNORE INTO listings (listing_id, timestamp_seen, message_sent)
            VALUES (?, ?, ?)
            """,
            (listing_id, datetime.now(timezone.utc).isoformat(), int(message_sent)),
        )
        self._conn.commit()

    def update_message_sent(self, listing_id: str) -> None:
        """Mark that a message has been sent for the listing."""
        self._conn.execute(
            "UPDATE listings SET message_sent = 1 WHERE listing_id = ?",
            (listing_id,),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
