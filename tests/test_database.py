import os
import tempfile

import pytest

from storage.database import Database


@pytest.fixture
def db(tmp_path):
    db_file = str(tmp_path / "test.db")
    database = Database(db_path=db_file)
    yield database
    database.close()


class TestDatabase:
    def test_new_listing_not_seen(self, db):
        assert db.is_seen("listing_001") is False

    def test_mark_seen_and_retrieve(self, db):
        db.mark_seen("listing_001")
        assert db.is_seen("listing_001") is True

    def test_mark_seen_idempotent(self, db):
        db.mark_seen("listing_001")
        db.mark_seen("listing_001")
        assert db.is_seen("listing_001") is True

    def test_multiple_listings(self, db):
        db.mark_seen("a")
        db.mark_seen("b")
        assert db.is_seen("a") is True
        assert db.is_seen("b") is True
        assert db.is_seen("c") is False

    def test_update_message_sent(self, db):
        db.mark_seen("listing_002", message_sent=False)
        db.update_message_sent("listing_002")
        cursor = db._conn.execute(
            "SELECT message_sent FROM listings WHERE listing_id = ?",
            ("listing_002",),
        )
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == 1

    def test_mark_seen_with_message_sent_true(self, db):
        db.mark_seen("listing_003", message_sent=True)
        cursor = db._conn.execute(
            "SELECT message_sent FROM listings WHERE listing_id = ?",
            ("listing_003",),
        )
        row = cursor.fetchone()
        assert row[0] == 1
