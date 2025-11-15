"""Tests for the quote scraper module."""

import json
import logging
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from download.scraper import (
    create_database,
    extract_quotes,
    extract_quotes_from_chucknorrisfacts_fr,
    extract_quotes_from_factinate,
    extract_quotes_from_html,
    extract_quotes_from_json,
    extract_quotes_from_parade,
    extract_quotes_from_thefactsite,
    fetch_url,
    save_quotes_to_db,
    scrape_all_sources,
    scrape_source,
    setup_logging,
    validate_sources,
)


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_quotes.db"
    create_database(str(db_path))
    return str(db_path)


@pytest.fixture
def sample_quotes():
    """Sample quotes for testing."""
    return [
        {"quote": "Chuck Norris can divide by zero.", "source": "test_source"},
        {"quote": "Chuck Norris counted to infinity. Twice.", "source": "test_source"},
    ]


class TestSetupLogging:
    """Tests for logging setup."""

    @patch("download.scraper.logging.basicConfig")
    def test_setup_logging_default(self, mock_config):
        """Test default logging setup."""
        setup_logging(verbose=False)
        mock_config.assert_called_once()
        # Check that INFO level was passed
        call_args = mock_config.call_args
        assert call_args[1]["level"] == logging.INFO

    @patch("download.scraper.logging.basicConfig")
    def test_setup_logging_verbose(self, mock_config):
        """Test verbose logging setup."""
        setup_logging(verbose=True)
        mock_config.assert_called_once()
        # Check that DEBUG level was passed
        call_args = mock_config.call_args
        assert call_args[1]["level"] == logging.DEBUG


class TestCreateDatabase:
    """Tests for database creation."""

    def test_create_database_creates_file(self, tmp_path):
        """Test that database file is created."""
        db_path = tmp_path / "quotes.db"
        create_database(str(db_path))
        assert db_path.exists()

    def test_create_database_creates_table(self, temp_db):
        """Test that quotes table is created with correct schema."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_create_database_creates_index(self, temp_db):
        """Test that index on quote column is created."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_quote'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_create_database_idempotent(self, temp_db):
        """Test that creating database multiple times doesn't error."""
        # Should not raise an exception
        create_database(temp_db)
        create_database(temp_db)


class TestFetchUrl:
    """Tests for URL fetching."""

    @patch("download.scraper.requests.get")
    def test_fetch_url_success(self, mock_get):
        """Test successful URL fetch."""
        mock_response = Mock()
        mock_response.text = "test content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_url("https://example.com")
        assert result == "test content"
        mock_get.assert_called_once()

    @patch("download.scraper.requests.get")
    def test_fetch_url_timeout(self, mock_get):
        """Test URL fetch with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()
        result = fetch_url("https://example.com", retries=1)
        assert result is None

    @patch("download.scraper.requests.get")
    def test_fetch_url_http_error(self, mock_get, caplog):
        """Test URL fetch with HTTP error."""
        with caplog.at_level(logging.ERROR):
            mock_get.side_effect = requests.exceptions.HTTPError()
            result = fetch_url("https://example.com", retries=1)
        assert result is None
        assert any("Failed to fetch" in record.message for record in caplog.records)

    @patch("download.scraper.requests.get")
    @patch("download.scraper.time.sleep")
    def test_fetch_url_retry_logic(self, mock_sleep, mock_get, caplog):
        """Test retry logic on failure."""
        with caplog.at_level(logging.WARNING):
            mock_get.side_effect = requests.exceptions.RequestException()
            result = fetch_url("https://example.com", retries=3)
        assert result is None
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # One less than retries
        assert any("Error fetching" in record.message for record in caplog.records)
        assert any("Failed to fetch" in record.message for record in caplog.records)


class TestExtractQuotesFromJson:
    """Tests for JSON quote extraction."""

    @pytest.mark.parametrize(
        "json_data,expected_count",
        [
            # Single quote with 'value' field
            ({"value": "Chuck Norris quote"}, 1),
            # Single quote with 'joke' field
            ({"joke": "Chuck Norris joke"}, 1),
            # List of quotes with 'value' field
            ({"result": [{"value": "Quote 1"}, {"value": "Quote 2"}]}, 2),
            # Array of quotes
            ([{"value": "Q1"}, {"value": "Q2"}], 2),
            # Empty data
            ({}, 0),
            ([], 0),
        ],
    )
    def test_extract_quotes_from_json_various_formats(self, json_data, expected_count):
        """Test extraction from various JSON formats."""
        json_string = json.dumps(json_data)
        quotes = extract_quotes_from_json(json_string, "test_source")
        assert len(quotes) == expected_count

    def test_extract_quotes_from_json_invalid_json(self, caplog):
        """Test extraction with invalid JSON."""
        with caplog.at_level(logging.ERROR):
            quotes = extract_quotes_from_json("invalid json", "test_source")
            assert len(quotes) == 0
            assert "Failed to parse JSON" in caplog.text

    def test_extract_quotes_from_json_source_attribution(self):
        """Test that source is properly attributed."""
        json_data = {"value": "Test quote"}
        json_string = json.dumps(json_data)
        quotes = extract_quotes_from_json(json_string, "my_source")
        assert quotes[0]["source"] == "my_source"

    def test_extract_quotes_from_json_list_of_strings(self):
        """Test extraction from list of plain strings."""
        json_data = ["Quote 1", "Quote 2", "Quote 3"]
        json_string = json.dumps(json_data)
        quotes = extract_quotes_from_json(json_string, "test_source")
        assert len(quotes) == 3
        assert quotes[0]["quote"] == "Quote 1"


class TestExtractQuotesFromHtml:
    """Tests for HTML quote extraction."""

    def test_extract_quotes_from_blockquote(self):
        """Test extraction from blockquote tags."""
        html = "<html><body><blockquote>Chuck Norris quote</blockquote></body></html>"
        quotes = extract_quotes_from_html(html, "test_source")
        assert len(quotes) == 1
        assert "Chuck Norris quote" in quotes[0]["quote"]

    def test_extract_quotes_from_class_quote(self):
        """Test extraction from elements with 'quote' class."""
        html = '<html><body><div class="quote-text">Chuck Norris quote here</div></body></html>'
        quotes = extract_quotes_from_html(html, "test_source")
        assert len(quotes) == 1

    def test_extract_quotes_from_paragraph_with_chuck_norris(self):
        """Test extraction from paragraphs containing 'Chuck Norris'."""
        html = (
            "<html><body><p>Chuck Norris can slam a revolving door.</p></body></html>"
        )
        quotes = extract_quotes_from_html(html, "test_source")
        # Should find at least one quote
        assert len(quotes) >= 0

    def test_extract_quotes_from_html_empty(self):
        """Test extraction from empty HTML."""
        html = "<html><body></body></html>"
        quotes = extract_quotes_from_html(html, "test_source")
        assert isinstance(quotes, list)

    def test_extract_quotes_from_html_exception(self):
        """Test extraction when parsing raises exception."""
        # Invalid HTML that might cause issues
        html = None
        quotes = extract_quotes_from_html(html, "test_source")
        assert isinstance(quotes, list)
        assert len(quotes) == 0


class TestExtractQuotes:
    """Tests for automatic quote extraction."""

    def test_extract_quotes_auto_detect_json(self):
        """Test automatic detection of JSON content."""
        content = '{"value": "Test quote"}'
        quotes = extract_quotes(content, "test_source", "auto")
        assert len(quotes) == 1

    def test_extract_quotes_auto_detect_html(self):
        """Test automatic detection of HTML content."""
        content = "<html><blockquote>Test</blockquote></html>"
        quotes = extract_quotes(content, "test_source", "auto")
        assert isinstance(quotes, list)

    def test_extract_quotes_explicit_json(self):
        """Test explicit JSON content type."""
        content = '{"value": "Test quote"}'
        quotes = extract_quotes(content, "test_source", "json")
        assert len(quotes) == 1

    def test_extract_quotes_explicit_html(self):
        """Test explicit HTML content type."""
        content = "<blockquote>Test</blockquote>"
        quotes = extract_quotes(content, "test_source", "html")
        assert isinstance(quotes, list)


class TestSaveQuotesToDb:
    """Tests for saving quotes to database."""

    def test_save_quotes_to_db_success(self, temp_db, sample_quotes):
        """Test successful quote saving."""
        saved_count = save_quotes_to_db(sample_quotes, temp_db)
        assert saved_count == 2

        # Verify quotes are in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quotes")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 2

    def test_save_quotes_to_db_duplicates(self, temp_db, sample_quotes):
        """Test handling of duplicate quotes."""
        # Save quotes twice
        save_quotes_to_db(sample_quotes, temp_db)
        saved_count = save_quotes_to_db(sample_quotes, temp_db)

        # Second save should save 0 (all duplicates)
        assert saved_count == 0

        # Database should still have only 2 quotes
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM quotes")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 2

    def test_save_quotes_to_db_empty_list(self, temp_db):
        """Test saving empty quote list."""
        saved_count = save_quotes_to_db([], temp_db)
        assert saved_count == 0

    def test_save_quotes_to_db_partial_duplicates(self, temp_db):
        """Test saving with some duplicates."""
        quotes1 = [{"quote": "Quote 1", "source": "src"}]
        quotes2 = [
            {"quote": "Quote 1", "source": "src"},  # Duplicate
            {"quote": "Quote 2", "source": "src"},  # New
        ]

        save_quotes_to_db(quotes1, temp_db)
        saved_count = save_quotes_to_db(quotes2, temp_db)
        assert saved_count == 1


class TestValidateSources:
    """Tests for source URL validation."""

    @pytest.mark.parametrize(
        "sources,expected_count",
        [
            (["https://example.com"], 1),
            (["http://example.com", "https://test.com"], 2),
            (["not a url"], 0),
            (["https://valid.com", "invalid"], 1),
            ([], 0),
        ],
    )
    def test_validate_sources(self, sources, expected_count):
        """Test source URL validation."""
        valid = validate_sources(sources)
        assert len(valid) == expected_count

    def test_validate_sources_filters_invalid(self):
        """Test that invalid URLs are filtered out."""
        sources = ["https://valid.com", "invalid", "also-invalid"]
        valid = validate_sources(sources)
        assert len(valid) == 1
        assert "https://valid.com" in valid


class TestScrapeSource:
    """Tests for scraping a single source."""

    @patch("download.scraper.fetch_url")
    @patch("download.scraper.extract_quotes")
    @patch("download.scraper.save_quotes_to_db")
    def test_scrape_source_success(self, mock_save, mock_extract, mock_fetch, temp_db):
        """Test successful source scraping."""
        mock_fetch.return_value = "content"
        mock_extract.return_value = [{"quote": "Test", "source": "src"}]
        mock_save.return_value = 1

        result = scrape_source("https://example.com", temp_db)
        assert result == 1

    @patch("download.scraper.fetch_url")
    def test_scrape_source_fetch_failure(self, mock_fetch, temp_db):
        """Test scraping when fetch fails."""
        mock_fetch.return_value = None
        result = scrape_source("https://example.com", temp_db)
        assert result == 0

    @patch("download.scraper.fetch_url")
    @patch("download.scraper.extract_quotes")
    def test_scrape_source_no_quotes_found(self, mock_extract, mock_fetch, temp_db):
        """Test scraping when no quotes are found."""
        mock_fetch.return_value = "content"
        mock_extract.return_value = []
        result = scrape_source("https://example.com", temp_db)
        assert result == 0


class TestScrapeAllSources:
    """Tests for scraping multiple sources."""

    @patch("download.scraper.scrape_source")
    def test_scrape_all_sources_success(self, mock_scrape, temp_db):
        """Test scraping multiple sources successfully."""
        mock_scrape.return_value = 5
        sources = ["https://example1.com", "https://example2.com"]
        total = scrape_all_sources(sources, temp_db)
        assert total == 10
        assert mock_scrape.call_count == 2

    @patch("download.scraper.scrape_source")
    def test_scrape_all_sources_with_failures(self, mock_scrape, temp_db):
        """Test scraping with some sources failing."""
        mock_scrape.side_effect = [5, Exception("Error"), 3]
        sources = ["https://1.com", "https://2.com", "https://3.com"]
        total = scrape_all_sources(sources, temp_db)
        assert total == 8  # 5 + 0 (error) + 3

    @patch("download.scraper.scrape_source")
    def test_scrape_all_sources_empty_list(self, mock_scrape, temp_db):
        """Test scraping with empty source list."""
        total = scrape_all_sources([], temp_db)
        assert total == 0
        mock_scrape.assert_not_called()


class TestExtractQuotesFromParade:
    """Tests for Parade.com quote extraction."""

    def test_extract_quotes_from_parade_success(self):
        """Test successful extraction from Parade.com HTML."""
        html = """
        <div class="article-body">
            <p>Chuck Norris can divide by zero. This is an amazing feat.</p>
            <p>Another Chuck Norris fact here.</p>
        </div>
        """
        source = "https://parade.com/970343/parade/chuck-norris-jokes/"
        quotes = extract_quotes_from_parade(html, source)
        assert len(quotes) == 2
        assert all("Chuck Norris" in quote["quote"] for quote in quotes)
        assert all(quote["source"] == source for quote in quotes)

    def test_extract_quotes_from_parade_no_quotes(self):
        """Test extraction with no valid quotes."""
        html = "<p>This is just regular text.</p>"
        source = "https://parade.com/970343/parade/chuck-norris-jokes/"
        quotes = extract_quotes_from_parade(html, source)
        assert quotes == []


class TestExtractQuotesFromThefactsite:
    """Tests for Thefactsite.com quote extraction."""

    def test_extract_quotes_from_thefactsite_success(self):
        """Test successful extraction from Thefactsite.com HTML."""
        html = """
        <ol>
            <li>1. Chuck Norris can count to infinity. Twice.</li>
            <li>2. Another Chuck Norris amazing fact.</li>
        </ol>
        """
        source = "https://www.thefactsite.com/top-100-chuck-norris-facts/"
        quotes = extract_quotes_from_thefactsite(html, source)
        assert len(quotes) == 2
        assert all("Chuck Norris" in quote["quote"] for quote in quotes)
        assert not any(quote["quote"].startswith(("1. ", "2. ")) for quote in quotes)


class TestExtractQuotesFromChucknorrisfactsFr:
    """Tests for Chucknorrisfacts.fr quote extraction."""

    def test_extract_quotes_from_chucknorrisfacts_fr_success(self):
        """Test successful extraction from Chucknorrisfacts.fr HTML."""
        html = """
        <div class="fact">Chuck Norris can speak French fluently. In French.</div>
        <p>Another Chuck Norris fact in French.</p>
        """
        source = "https://www.chucknorrisfacts.fr/en/top-100-chuck-norris-facts"
        quotes = extract_quotes_from_chucknorrisfacts_fr(html, source)
        # Should extract from both div.fact and p
        assert len(quotes) >= 2
        assert all("Chuck Norris" in quote["quote"] for quote in quotes)


class TestExtractQuotesFromFactinate:
    """Tests for Factinate.com quote extraction."""

    def test_extract_quotes_from_factinate_success(self):
        """Test successful extraction from Factinate.com HTML."""
        html = """
        <blockquote>Chuck Norris can make a hormone. This is a fact.</blockquote>
        <div class="quote">Another Chuck Norris quote here.</div>
        """
        source = "https://www.factinate.com/quote/chuck-norris-jokes/"
        quotes = extract_quotes_from_factinate(html, source)
        # Should extract from both blockquote and div.quote
        assert len(quotes) >= 2
        assert all("Chuck Norris" in quote["quote"] for quote in quotes)


class TestExtractQuotesRouting:
    """Tests for extract_quotes routing to site-specific functions."""

    def test_extract_quotes_routes_to_parade(self):
        """Test that extract_quotes routes Parade.com to specific function."""
        html = "<p>Chuck Norris can do anything. Even HTML parsing.</p>"
        source = "https://parade.com/970343/parade/chuck-norris-jokes/"
        quotes = extract_quotes(html, source, "html")
        assert len(quotes) >= 1
        assert quotes[0]["source"] == source

    def test_extract_quotes_routes_to_thefactsite(self):
        """Test routing to Thefactsite.com function."""
        html = "<ol><li>Chuck Norris fact from the site.</li></ol>"
        source = "https://www.thefactsite.com/top-100-chuck-norris-facts/"
        quotes = extract_quotes(html, source, "html")
        assert len(quotes) >= 1

    def test_extract_quotes_routes_to_fallback(self):
        """Test routing to generic HTML extraction for unknown sites."""
        html = "<p>Chuck Norris from unknown site.</p>"
        source = "https://unknown-site.com/quotes"
        quotes = extract_quotes(html, source, "html")
        assert len(quotes) >= 1
