import asyncio
from typing import Any, Dict

import aiohttp

from bot.filters import Listing
from utils.logger import get_logger

logger = get_logger(__name__)


def _format_message(listing: Listing) -> str:
    price_str = "Free" if listing.price == 0.0 else f"{listing.price}"
    return (
        f"🛍 New listing detected!\n"
        f"Title: {listing.title}\n"
        f"Price: {price_str}\n"
        f"Location: {listing.location}\n"
        f"Link: {listing.url}"
    )


class Notifier:
    """Sends notifications through configured channels."""

    def __init__(self, config: Dict[str, Any]) -> None:
        notif_cfg = config.get("notifications", {})
        self._console = notif_cfg.get("console", True)
        self._telegram = notif_cfg.get("telegram", False)
        self._discord = notif_cfg.get("discord", False)

        telegram_cfg = config.get("telegram", {})
        self._telegram_token: str = telegram_cfg.get("bot_token", "")
        self._telegram_chat_id: str = str(telegram_cfg.get("chat_id", ""))

        discord_cfg = config.get("discord", {})
        self._discord_webhook: str = discord_cfg.get("webhook_url", "")

    async def notify(self, listing: Listing) -> None:
        """Send notification for *listing* over all enabled channels."""
        text = _format_message(listing)

        if self._console:
            logger.info("[NOTIFICATION] %s", text)

        tasks = []
        if self._telegram and self._telegram_token and self._telegram_chat_id:
            tasks.append(self._send_telegram(text))
        if self._discord and self._discord_webhook:
            tasks.append(self._send_discord(text))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_telegram(self, text: str) -> None:
        url = (
            f"https://api.telegram.org/bot{self._telegram_token}/sendMessage"
        )
        payload = {"chat_id": self._telegram_chat_id, "text": text}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        logger.info("Telegram notification sent.")
                    else:
                        body = await resp.text()
                        logger.error("Telegram error %s: %s", resp.status, body)
        except Exception as exc:
            logger.error("Telegram notification failed: %s", exc)

    async def _send_discord(self, text: str) -> None:
        payload = {"content": text}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self._discord_webhook,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status in (200, 204):
                        logger.info("Discord notification sent.")
                    else:
                        body = await resp.text()
                        logger.error("Discord error %s: %s", resp.status, body)
        except Exception as exc:
            logger.error("Discord notification failed: %s", exc)
