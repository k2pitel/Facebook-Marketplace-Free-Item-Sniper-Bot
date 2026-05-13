import asyncio
import re
from typing import List, Optional
from urllib.parse import urlencode

from playwright.async_api import Browser, Page, async_playwright

from bot.filters import Listing, category_to_path
from utils.logger import get_logger

logger = get_logger(__name__)

BASE_URL = "https://www.facebook.com/marketplace"


def build_search_url(
    city: str,
    category: str,
    min_price: float = 0.0,
    max_price: Optional[float] = None,
    radius_km: int = 25,
) -> str:
    """Construct a Facebook Marketplace search URL."""
    city_slug = city.lower().replace(" ", "")
    cat_path = category_to_path(category)
    params = {
        "minPrice": int(min_price),
        "sortBy": "creation_time_descend",
        "radiusKm": radius_km,
    }
    if max_price is not None:
        params["maxPrice"] = int(max_price)
    return f"{BASE_URL}/{city_slug}/{cat_path}?{urlencode(params)}"


class MarketplaceScanner:
    """Playwright-based scanner that loads a Marketplace search page and
    extracts listing metadata."""

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless
        )
        logger.info("Browser started.")

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Browser stopped.")

    async def get_listings(self, url: str) -> List[Listing]:
        """Load *url* and return a list of Listing objects found on the page."""
        if self._browser is None:
            raise RuntimeError("Scanner not started. Call start() first.")

        page: Page = await self._browser.new_page()
        listings: List[Listing] = []
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(2)
            listings = await self._extract_listings(page, url)
        except Exception as exc:
            logger.error("Failed to load page %s: %s", url, exc)
        finally:
            await page.close()

        return listings

    async def _extract_listings(self, page: Page, source_url: str) -> List[Listing]:
        """Parse listing cards from the loaded page."""
        results: List[Listing] = []

        listing_links = await page.query_selector_all("a[href*='/marketplace/item/']")

        seen_ids: set = set()
        for link in listing_links:
            href = await link.get_attribute("href")
            if not href:
                continue

            match = re.search(r"/marketplace/item/(\d+)", href)
            if not match:
                continue
            listing_id = match.group(1)
            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)

            title = await self._safe_inner_text(link) or ""
            price = 0.0
            location = ""

            try:
                parent = await link.query_selector("xpath=..")
                if parent:
                    parent_text = await parent.inner_text()
                    price = _parse_price(parent_text)
                    location = _parse_location(parent_text)
            except Exception:
                pass

            full_url = f"https://www.facebook.com/marketplace/item/{listing_id}"
            results.append(
                Listing(
                    listing_id=listing_id,
                    title=title.strip(),
                    price=price,
                    location=location.strip(),
                    url=full_url,
                )
            )

        logger.info("Found %d listings at %s", len(results), source_url)
        return results

    @staticmethod
    async def _safe_inner_text(element) -> str:
        try:
            return await element.inner_text()
        except Exception:
            return ""


def _parse_price(text: str) -> float:
    """Extract the first numeric price value from a block of text."""
    free_pattern = re.compile(r"\bfree\b", re.IGNORECASE)
    if free_pattern.search(text):
        return 0.0
    # Match a price like $99, $99.99, 1,000, etc.  The pattern uses a
    # non-greedy decimal component so trailing periods are not captured.
    match = re.search(r"[\$€£]?\s*(\d[\d,]*(?:\.\d+)?)", text)
    if match:
        raw_price = match.group(1).replace(",", "")
        try:
            return float(raw_price)
        except ValueError:
            pass
    return 0.0


def _parse_location(text: str) -> str:
    """Attempt to extract a location string from listing card text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in reversed(lines):
        if any(char.isalpha() for char in line) and len(line) < 60:
            return line
    return ""
