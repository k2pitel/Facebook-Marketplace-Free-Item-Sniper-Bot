import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from bot.filters import ListingFilter
from bot.messenger import Messenger
from bot.notifier import Notifier
from bot.scanner import MarketplaceScanner, build_search_url
from storage.database import Database
from utils.logger import get_logger
from utils.randomizer import MessageRandomizer

logger = get_logger(__name__)

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config" / "config.yaml"


def load_config(path: str = str(DEFAULT_CONFIG_PATH)) -> Dict[str, Any]:
    """Load and return the YAML configuration file."""
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


async def run(config: Dict[str, Any]) -> None:
    location_cfg = config.get("location", {})
    city: str = location_cfg.get("city", "Copenhagen")
    radius_km: int = int(location_cfg.get("radius_km", 25))

    categories = config.get("categories", ["free"])

    price_cfg = config.get("price_filter", {})
    min_price: float = float(price_cfg.get("min", 0))
    max_price_raw = price_cfg.get("max")
    max_price = float(max_price_raw) if max_price_raw is not None else None

    listing_filter = ListingFilter(
        min_price=min_price,
        max_price=max_price,
        include_keywords=config.get("include_keywords", []),
        exclude_keywords=config.get("exclude_keywords", []),
        categories=categories,
    )

    messages: list = config.get("messages", ["Hi! Is this still available?"])
    randomizer = MessageRandomizer(messages)

    auto_message: bool = bool(config.get("auto_message", False))
    scan_interval: int = int(config.get("scan_interval_seconds", 30))

    os.makedirs("storage", exist_ok=True)
    db = Database()
    notifier = Notifier(config)
    scanner = MarketplaceScanner(headless=True)
    messenger = Messenger(headless=True) if auto_message else None

    try:
        await scanner.start()
        if messenger:
            await messenger.start()

        logger.info("Bot started. City: %s | Radius: %s km", city, radius_km)

        while True:
            for category in categories:
                url = build_search_url(
                    city=city,
                    category=category,
                    min_price=min_price,
                    max_price=max_price,
                    radius_km=radius_km,
                )
                listings = await scanner.get_listings(url)

                for listing in listings:
                    if db.is_seen(listing.listing_id):
                        continue

                    if not listing_filter.passes(listing):
                        logger.warning(
                            "Listing skipped (keyword filter): %s",
                            listing.listing_id,
                        )
                        db.mark_seen(listing.listing_id, message_sent=False)
                        continue

                    logger.info(
                        "New listing detected: %s – %s",
                        listing.listing_id,
                        listing.title,
                    )
                    await notifier.notify(listing)

                    message_sent = False
                    if messenger:
                        message = randomizer.pick()
                        message_sent = await messenger.send_message(listing, message)

                    db.mark_seen(listing.listing_id, message_sent=message_sent)

            await asyncio.sleep(scan_interval)

    except asyncio.CancelledError:
        logger.info("Bot shutting down…")
    finally:
        await scanner.stop()
        if messenger:
            await messenger.stop()
        db.close()


def main() -> None:
    config_path = sys.argv[1] if len(sys.argv) > 1 else str(DEFAULT_CONFIG_PATH)
    config = load_config(config_path)
    asyncio.run(run(config))


if __name__ == "__main__":
    main()
