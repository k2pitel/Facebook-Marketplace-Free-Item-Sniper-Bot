import asyncio
from typing import Optional

from playwright.async_api import Browser, Page, async_playwright

from bot.filters import Listing
from utils.logger import get_logger

logger = get_logger(__name__)

_MESSAGE_BUTTON_SELECTORS = [
    "div[aria-label='Message']",
    "div[aria-label='Send message']",
    "a[aria-label='Message']",
    "span:has-text('Message')",
]

_COMPOSER_SELECTORS = [
    "div[aria-label='Message']",
    "div[contenteditable='true']",
    "textarea",
]


class Messenger:
    """Opens listing pages and sends messages to sellers via Facebook Messenger.

    NOTE: The Playwright browser instance must already be authenticated with
    Facebook (e.g. by loading a saved browser profile or cookie jar containing
    an active login session). Without authentication, Facebook will redirect to
    the login page and no messages will be sent.
    """

    def __init__(self, headless: bool = True) -> None:
        self._headless = headless
        self._browser: Optional[Browser] = None
        self._playwright = None

    async def start(self) -> None:
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless
        )
        logger.info("Messenger browser started.")

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        logger.info("Messenger browser stopped.")

    async def send_message(self, listing: Listing, message: str) -> bool:
        """Attempt to send *message* to the seller of *listing*.

        Returns True on success, False otherwise.
        """
        if self._browser is None:
            raise RuntimeError("Messenger not started. Call start() first.")

        page: Page = await self._browser.new_page()
        try:
            logger.info("Opening listing page: %s", listing.url)
            await page.goto(
                listing.url, wait_until="domcontentloaded", timeout=30_000
            )
            await asyncio.sleep(2)

            button = await self._find_element(page, _MESSAGE_BUTTON_SELECTORS)
            if button is None:
                logger.warning(
                    "Message button not found for listing %s", listing.listing_id
                )
                return False

            await button.click()
            await asyncio.sleep(1)

            composer = await self._find_element(page, _COMPOSER_SELECTORS)
            if composer is None:
                logger.warning(
                    "Message composer not found for listing %s", listing.listing_id
                )
                return False

            await composer.fill(message)
            await composer.press("Enter")
            await asyncio.sleep(1)

            logger.info(
                "Message sent to seller for listing %s: %s",
                listing.listing_id,
                message,
            )
            return True

        except Exception as exc:
            logger.error(
                "Error sending message for listing %s: %s",
                listing.listing_id,
                exc,
            )
            return False
        finally:
            await page.close()

    @staticmethod
    async def _find_element(page: Page, selectors):
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    return element
            except Exception:
                continue
        return None
