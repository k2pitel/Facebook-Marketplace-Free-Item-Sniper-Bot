import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.filters import Listing
from bot.notifier import Notifier, _format_message


class TestFormatMessage:
    def test_free_price_label(self):
        listing = Listing(
            listing_id="1",
            title="Old sofa",
            price=0.0,
            location="Copenhagen",
            url="https://www.facebook.com/marketplace/item/1",
        )
        msg = _format_message(listing)
        assert "Free" in msg
        assert "Old sofa" in msg
        assert "Copenhagen" in msg

    def test_paid_price_shown(self):
        listing = Listing(
            listing_id="2",
            title="Bike",
            price=50.0,
            location="Roskilde",
            url="https://www.facebook.com/marketplace/item/2",
        )
        msg = _format_message(listing)
        assert "50.0" in msg


class TestNotifier:
    def _make_listing(self):
        return Listing(
            listing_id="42",
            title="Test item",
            price=0.0,
            location="Copenhagen",
            url="https://www.facebook.com/marketplace/item/42",
        )

    def test_console_notification_logs(self, caplog):
        config = {"notifications": {"console": True, "telegram": False, "discord": False}}
        notifier = Notifier(config)
        import logging
        with caplog.at_level(logging.INFO):
            asyncio.run(notifier.notify(self._make_listing()))
        assert any("Test item" in r.message for r in caplog.records)

    def test_no_channels_enabled(self):
        config = {"notifications": {"console": False, "telegram": False, "discord": False}}
        notifier = Notifier(config)
        asyncio.run(notifier.notify(self._make_listing()))
