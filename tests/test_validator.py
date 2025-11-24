"""Tests for the URL validator module."""

import pytest

from scraper.validator import (
    is_chuck_norris_source,
    is_valid_url,
    normalize_url,
    validate_http_url,
    validate_sources,
)


class TestIsValidUrl:
    """Tests for is_valid_url function."""

    def test_valid_http_url(self):
        """Test validation of valid HTTP URL."""
        assert is_valid_url("http://example.com") is True

    def test_valid_https_url(self):
        """Test validation of valid HTTPS URL."""
        assert is_valid_url("https://example.com/path") is True

    def test_invalid_url_no_scheme(self):
        """Test rejection of URL without scheme."""
        assert is_valid_url("example.com") is False

    def test_invalid_url_no_domain(self):
        """Test rejection of URL without domain."""
        assert is_valid_url("http://") is False

    def test_invalid_url_empty_string(self):
        """Test rejection of empty string."""
        assert is_valid_url("") is False

    def test_invalid_url_malformed(self):
        """Test rejection of malformed URL."""
        assert is_valid_url("not-a-url") is False


class TestValidateSources:
    """Tests for validate_sources function."""

    def test_validate_mixed_urls(self):
        """Test validation of mixed valid and invalid URLs."""
        sources = [
            "https://example.com",
            "not-a-url",
            "http://test.com/path",
            "",
            "ftp://valid-but-unusual.com",
        ]
        valid = validate_sources(sources)
        assert len(valid) == 3  # http, https, and ftp URLs
        assert "https://example.com" in valid
        assert "http://test.com/path" in valid

    def test_validate_all_valid_urls(self):
        """Test validation when all URLs are valid."""
        sources = [
            "https://example1.com",
            "https://example2.com",
            "http://example3.com",
        ]
        valid = validate_sources(sources)
        assert len(valid) == 3

    def test_validate_all_invalid_urls(self):
        """Test validation when all URLs are invalid."""
        sources = ["not-a-url", "", "also-not-a-url"]
        valid = validate_sources(sources)
        assert len(valid) == 0

    def test_validate_empty_list(self):
        """Test validation of empty list."""
        valid = validate_sources([])
        assert valid == []


class TestValidateHttpUrl:
    """Tests for validate_http_url function."""

    def test_valid_http_scheme(self):
        """Test HTTP scheme is valid."""
        assert validate_http_url("http://example.com") is True

    def test_valid_https_scheme(self):
        """Test HTTPS scheme is valid."""
        assert validate_http_url("https://example.com") is True

    def test_invalid_ftp_scheme(self):
        """Test FTP scheme is invalid."""
        assert validate_http_url("ftp://example.com") is False

    def test_invalid_no_scheme(self):
        """Test URL without scheme is invalid."""
        assert validate_http_url("example.com") is False

    def test_invalid_malformed_url(self):
        """Test malformed URL is invalid."""
        assert validate_http_url("not-a-url") is False


class TestNormalizeUrl:
    """Tests for normalize_url function."""

    def test_normalize_trailing_slash(self):
        """Test removal of trailing slash."""
        url = "https://example.com/path/"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/path"

    def test_normalize_keeps_root_slash(self):
        """Test root slash is kept."""
        url = "https://example.com/"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/"

    def test_normalize_removes_fragment(self):
        """Test removal of URL fragment."""
        url = "https://example.com/path#section"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/path"

    def test_normalize_keeps_query(self):
        """Test query parameters are kept."""
        url = "https://example.com/path?key=value"
        normalized = normalize_url(url)
        assert normalized == "https://example.com/path?key=value"

    def test_normalize_malformed_url(self):
        """Test malformed URL is returned as-is."""
        url = "not-a-url"
        normalized = normalize_url(url)
        assert normalized == url


class TestIsChuckNorrisSource:
    """Tests for is_chuck_norris_source function."""

    def test_url_with_chucknorris_indicator(self):
        """Test URL containing 'chucknorris' is identified."""
        assert is_chuck_norris_source("https://chucknorris.io") is True

    def test_url_with_chuck_norris_indicator(self):
        """Test URL containing 'chuck-norris' is identified."""
        assert is_chuck_norris_source("https://chuck-norris-jokes.com") is True

    def test_url_with_norris_indicator(self):
        """Test URL containing 'norris' is identified."""
        assert is_chuck_norris_source("https://norris-facts.com") is True

    def test_content_with_chuck_norris(self):
        """Test content containing 'Chuck Norris' is identified."""
        url = "https://example.com"
        content = "Chuck Norris can divide by zero."
        assert is_chuck_norris_source(url, content) is True

    def test_neither_url_nor_content_match(self):
        """Test neither URL nor content match returns False."""
        url = "https://example.com"
        content = "Some random content"
        assert is_chuck_norris_source(url, content) is False

    def test_empty_url_and_content(self):
        """Test empty URL and content returns False."""
        assert is_chuck_norris_source("", "") is False
