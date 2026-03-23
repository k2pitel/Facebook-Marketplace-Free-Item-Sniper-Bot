import pytest

from bot.scanner import build_search_url, _parse_price, _parse_location


class TestBuildSearchUrl:
    def test_basic_url(self):
        url = build_search_url(city="Copenhagen", category="free")
        assert "facebook.com/marketplace" in url
        assert "copenhagen" in url
        assert "free" in url

    def test_price_params_included(self):
        url = build_search_url(
            city="Copenhagen", category="furniture", min_price=0, max_price=50
        )
        assert "minPrice=0" in url
        assert "maxPrice=50" in url

    def test_radius_included(self):
        url = build_search_url(city="Roskilde", category="free", radius_km=30)
        assert "radiusKm=30" in url

    def test_city_lowercased_and_stripped(self):
        url = build_search_url(city="New York", category="free")
        assert "newyork" in url


class TestParsePrice:
    def test_free_keyword(self):
        assert _parse_price("Free") == 0.0
        assert _parse_price("FREE item") == 0.0

    def test_dollar_price(self):
        assert _parse_price("$25") == 25.0

    def test_decimal_price(self):
        assert _parse_price("$12.50") == 12.50

    def test_price_in_sentence_with_periods(self):
        assert _parse_price("Nice sofa. Price: $99.99. Pickup only.") == 99.99

    def test_no_price(self):
        assert _parse_price("some random text") == 0.0


class TestParseLocation:
    def test_returns_last_alpha_line(self):
        text = "Nice sofa\n$0\nCopenhagen"
        result = _parse_location(text)
        assert "Copenhagen" in result

    def test_empty_text(self):
        result = _parse_location("")
        assert result == ""
