"""Tests for OSFIDScraper."""

import pytest
from osf_scraper.discovery import OSFIDScraper


@pytest.fixture
def scraper():
    return OSFIDScraper()


class TestExtractId:
    def test_plain_id_unchanged(self, scraper):
        assert scraper._extract_id("abc12") == "abc12"

    def test_url_with_trailing_slash(self, scraper):
        assert scraper._extract_id("https://osf.io/abc12/") == "abc12"

    def test_url_without_trailing_slash(self, scraper):
        assert scraper._extract_id("https://osf.io/abc12") == "abc12"

    def test_empty_string(self, scraper):
        assert scraper._extract_id("") == ""


class TestAddFilter:
    def test_adds_filter_to_plain_url(self, scraper):
        url = scraper._add_filter(
            "https://api.osf.io/v2/registrations/",
            "filter[category]",
            "preregistration",
        )
        assert (
            "filter%5Bcategory%5D=preregistration" in url
            or "filter[category]=preregistration" in url
        )

    def test_preserves_existing_params(self, scraper):
        url = scraper._add_filter(
            "https://api.osf.io/v2/registrations/?page=2",
            "filter[category]",
            "preregistration",
        )
        assert "page=2" in url
        assert "preregistration" in url

    def test_overwrites_existing_filter(self, scraper):
        url = scraper._add_filter(
            "https://api.osf.io/v2/registrations/?filter%5Bcategory%5D=other",
            "filter[category]",
            "preregistration",
        )
        assert "preregistration" in url
        assert "other" not in url
