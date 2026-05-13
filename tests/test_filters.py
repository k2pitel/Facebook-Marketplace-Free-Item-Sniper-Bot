import pytest

from bot.filters import Listing, ListingFilter, category_to_path


class TestListingFilter:
    def _make_listing(self, title="sofa table", price=0.0):
        return Listing(
            listing_id="123",
            title=title,
            price=price,
            location="Copenhagen",
            url="https://www.facebook.com/marketplace/item/123",
        )

    def test_passes_free_item_no_keywords(self):
        f = ListingFilter(min_price=0, max_price=0)
        assert f.passes(self._make_listing(price=0.0)) is True

    def test_blocks_paid_item_when_max_zero(self):
        f = ListingFilter(min_price=0, max_price=0)
        assert f.passes(self._make_listing(price=5.0)) is False

    def test_include_keywords_match(self):
        f = ListingFilter(include_keywords=["sofa", "chair"])
        assert f.passes(self._make_listing(title="old sofa")) is True

    def test_include_keywords_no_match(self):
        f = ListingFilter(include_keywords=["sofa", "chair"])
        assert f.passes(self._make_listing(title="bicycle")) is False

    def test_exclude_keywords_block(self):
        f = ListingFilter(exclude_keywords=["broken", "damaged"])
        assert f.passes(self._make_listing(title="broken sofa")) is False

    def test_exclude_keywords_allow_clean(self):
        f = ListingFilter(exclude_keywords=["broken", "damaged"])
        assert f.passes(self._make_listing(title="nice sofa")) is True

    def test_include_and_exclude_combined(self):
        f = ListingFilter(
            include_keywords=["sofa"], exclude_keywords=["broken"]
        )
        assert f.passes(self._make_listing(title="broken sofa")) is False
        assert f.passes(self._make_listing(title="clean sofa")) is True

    def test_no_filters_passes_everything(self):
        f = ListingFilter()
        assert f.passes(self._make_listing(price=100.0, title="anything")) is True

    def test_price_range(self):
        f = ListingFilter(min_price=0, max_price=50)
        assert f.passes(self._make_listing(price=25.0)) is True
        assert f.passes(self._make_listing(price=51.0)) is False
        assert f.passes(self._make_listing(price=0.0)) is True

    def test_case_insensitive_keywords(self):
        f = ListingFilter(include_keywords=["SOFA"], exclude_keywords=["BROKEN"])
        assert f.passes(self._make_listing(title="sofa for free")) is True
        assert f.passes(self._make_listing(title="Broken sofa")) is False


class TestCategoryToPath:
    def test_known_categories(self):
        assert category_to_path("furniture") == "furniture"
        assert category_to_path("free_stuff") == "free"
        assert category_to_path("electronics") == "electronics"

    def test_unknown_category_passthrough(self):
        assert category_to_path("garden") == "garden"

    def test_case_insensitive(self):
        assert category_to_path("Furniture") == "furniture"
