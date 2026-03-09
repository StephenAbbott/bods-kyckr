"""Tests for country and jurisdiction resolution."""

from bods_kyckr.utils.countries import (
    jurisdiction_to_country_code,
    resolve_country,
    resolve_jurisdiction,
)


class TestResolveJurisdiction:
    def test_gb(self):
        result = resolve_jurisdiction("GB")
        assert result["code"] == "GB"
        assert "United Kingdom" in result["name"]

    def test_lowercase(self):
        result = resolve_jurisdiction("gb")
        assert result["code"] == "GB"

    def test_us(self):
        result = resolve_jurisdiction("US")
        assert result["code"] == "US"

    def test_none(self):
        assert resolve_jurisdiction(None) is None

    def test_empty(self):
        assert resolve_jurisdiction("") is None


class TestResolveCountry:
    def test_full_name(self):
        result = resolve_country("United Kingdom")
        assert result["code"] == "GB"

    def test_iso_code(self):
        result = resolve_country("GB")
        assert result["code"] == "GB"

    def test_common_abbreviation(self):
        result = resolve_country("UK")
        assert result["code"] == "GB"

    def test_none(self):
        assert resolve_country(None) is None

    def test_empty(self):
        assert resolve_country("") is None

    def test_germany(self):
        result = resolve_country("Germany")
        assert result["code"] == "DE"


class TestJurisdictionToCountryCode:
    def test_gb(self):
        assert jurisdiction_to_country_code("GB") == "GB"

    def test_lowercase(self):
        assert jurisdiction_to_country_code("gb") == "GB"

    def test_none(self):
        assert jurisdiction_to_country_code(None) is None
