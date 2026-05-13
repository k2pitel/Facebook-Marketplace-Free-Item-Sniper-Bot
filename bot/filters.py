from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Listing:
    listing_id: str
    title: str = ""
    price: float = 0.0
    location: str = ""
    url: str = ""
    category: str = ""
    description: str = ""


class ListingFilter:
    """Applies price, keyword and category filters to listings."""

    def __init__(
        self,
        min_price: float = 0.0,
        max_price: Optional[float] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
    ) -> None:
        self.min_price = min_price
        self.max_price = max_price
        self.include_keywords: List[str] = [
            kw.lower() for kw in (include_keywords or [])
        ]
        self.exclude_keywords: List[str] = [
            kw.lower() for kw in (exclude_keywords or [])
        ]
        self.categories: List[str] = [c.lower() for c in (categories or [])]

    def passes(self, listing: Listing) -> bool:
        """Return True if the listing passes all configured filters."""
        if not self._price_ok(listing.price):
            return False
        text = f"{listing.title} {listing.description}".lower()
        if not self._keywords_ok(text):
            return False
        return True

    def _price_ok(self, price: float) -> bool:
        if price < self.min_price:
            return False
        if self.max_price is not None and price > self.max_price:
            return False
        return True

    def _keywords_ok(self, text: str) -> bool:
        for kw in self.exclude_keywords:
            if kw in text:
                return False
        if self.include_keywords:
            for kw in self.include_keywords:
                if kw in text:
                    return True
            return False
        return True


CATEGORY_PATH_MAP = {
    "furniture": "furniture",
    "electronics": "electronics",
    "free": "free",
    "free_stuff": "free",
    "tools": "tools",
    "clothing": "clothing",
    "garden": "garden",
    "toys": "toys",
    "sports": "sports",
    "vehicles": "vehicles",
}


def category_to_path(category: str) -> str:
    """Map a category name to its Facebook Marketplace URL path segment."""
    return CATEGORY_PATH_MAP.get(category.lower(), category.lower())
