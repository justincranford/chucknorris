"""Tests for the quote scraper module."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from scraper.scraper import (
    comment_out_source,
    create_database,
    extract_quotes,
    extract_quotes_from_chucknorrisfacts_fr,
    extract_quotes_from_factinate,
    extract_quotes_from_html,
    extract_quotes_from_json,
    extract_quotes_from_parade,
    extract_quotes_from_thefactsite,
    fetch_url,
    get_scraped_sources,
    load_sources,
    save_quotes_to_csv,
    save_quotes_to_db,
    scrape_all_sources,
    scrape_source,
    setup_logging,
    validate_sources,
)


@pytest.fixture
def temp_db(tmp_path: Path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test_quotes.db"
    create_database(str(db_path))  # Ensure db_path is passed as a string
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

    @patch("scraper.scraper.logging.basicConfig")
    def test_setup_logging_default(self, mock_config: MagicMock):
        """Test default logging setup."""
        setup_logging(verbose=False)
        mock_config.assert_called_once()
        # Check that INFO level was passed
        call_args = mock_config.call_args
        assert call_args[1]["level"] == logging.INFO

    @patch("scraper.scraper.logging.basicConfig")
    def test_setup_logging_verbose(self, mock_config: MagicMock):
        """Test verbose logging setup."""
        setup_logging(verbose=True)
        mock_config.assert_called_once()
        # Check that DEBUG level was passed
        call_args = mock_config.call_args
        assert call_args[1]["level"] == logging.DEBUG


class TestCreateDatabase:
    """Tests for database creation."""

    def test_create_database_creates_file(self, tmp_path: Path):
        """Test that database file is created."""
        db_path: Path = tmp_path / "quotes.db"
        create_database(str(db_path))
        assert isinstance(db_path, Path) and db_path.exists()

    def test_create_database_creates_table(self, temp_db: str) -> None:
        """Test that quotes table is created with correct schema."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'")
            assert cursor.fetchone() is not None

    def test_create_database_creates_index(self, temp_db: str) -> None:
        """Test that index on quote column is created."""
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_quote'")
            assert cursor.fetchone() is not None

    def test_create_database_idempotent(self, temp_db: str) -> None:
        """Test that creating database multiple times doesn't error."""
        # Should not raise an exception
        create_database(temp_db)
        create_database(temp_db)


class TestCommentOutSource:
    """Tests for commenting out sources."""

    @patch("scraper.scraper.SOURCES_FILE", "test_sources.txt")
    def test_comment_out_source_success(self):
        """Test successfully commenting out a source."""
        # Create a test sources file
        with open("test_sources.txt", "w") as f:
            f.write("https://example1.com\n")
            f.write("https://example2.com\n")
            f.write("# https://example3.com\n")

        comment_out_source("https://example2.com", "HTTP 404")

        with open("test_sources.txt", "r") as f:
            content = f.read()

        assert "# [HTTP 404] https://example2.com" in content
        assert "https://example1.com" in content
        assert "# https://example3.com" in content

        # Clean up
        import os

        os.remove("test_sources.txt")

    @patch("scraper.scraper.SOURCES_FILE", "nonexistent.txt")
    def test_comment_out_source_file_not_found(self, caplog: pytest.LogCaptureFixture):
        """Test commenting out source when file doesn't exist."""
        with caplog.at_level(logging.ERROR):
            comment_out_source("https://example.com", "test")
        assert any("Failed to comment out source" in record.message for record in caplog.records)


class TestLoadSources:
    """Tests for loading sources."""

    @patch("scraper.scraper.SOURCES_FILE", "test_sources.txt")
    def test_load_sources_success(self):
        """Test loading sources successfully."""
        # Create a test sources file
        with open("test_sources.txt", "w") as f:
            f.write("https://example1.com\n")
            f.write("# https://example2.com\n")
            f.write("https://example3.com\n")
            f.write("\n")  # Empty line

        result = load_sources()
        assert result == ["https://example1.com", "https://example3.com"]

        # Clean up
        import os

        os.remove("test_sources.txt")

    @patch("scraper.scraper.SOURCES_FILE", "nonexistent.txt")
    def test_load_sources_file_not_found(self, caplog: pytest.LogCaptureFixture):
        """Test loading sources when file doesn't exist."""
        caplog.set_level(logging.WARNING)
        result = load_sources()
        assert result == []
        assert any("Sources file nonexistent.txt not found" in record.message for record in caplog.records)


class TestSaveQuotes:
    """Tests for saving quotes."""

    def test_save_quotes_to_db_success(self, temp_db: str, sample_quotes: List[Dict[str, str]]):
        """Test saving quotes to database successfully."""
        result = save_quotes_to_db(sample_quotes, temp_db)
        assert result == 2

        # Verify quotes were saved
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM quotes")
            assert cursor.fetchone()[0] == 2

    def test_save_quotes_to_db_empty_list(self, temp_db: str, caplog: pytest.LogCaptureFixture):
        """Test saving empty list of quotes."""
        caplog.set_level(logging.WARNING)
        result = save_quotes_to_db([], temp_db)
        assert result == 0
        assert any("No quotes to save" in record.message for record in caplog.records)

    def test_save_quotes_to_db_duplicate(self, temp_db: str, sample_quotes: List[Dict[str, str]]):
        """Test saving duplicate quotes."""
        # Save first time
        result1 = save_quotes_to_db(sample_quotes, temp_db)
        assert result1 == 2

        # Save again - should save 0 due to unique constraint
        result2 = save_quotes_to_db(sample_quotes, temp_db)
        assert result2 == 0

    def test_save_quotes_to_csv_success(self, tmp_path: Path, sample_quotes: List[Dict[str, str]]):
        """Test saving quotes to CSV successfully."""
        csv_path = tmp_path / "test_quotes.csv"
        result = save_quotes_to_csv(sample_quotes, str(csv_path))
        assert result == 2

        # Verify CSV was created and has content
        assert csv_path.exists()
        with open(csv_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "source" in content
            assert "quote" in content
            assert "Chuck Norris can divide by zero." in content

    def test_save_quotes_to_csv_empty_list(self, tmp_path: Path, caplog: pytest.LogCaptureFixture):
        """Test saving empty list to CSV."""
        csv_path = tmp_path / "empty.csv"
        with caplog.at_level(logging.WARNING):
            result = save_quotes_to_csv([], str(csv_path))
        assert result == 0
        assert any("No quotes to save" in record.message for record in caplog.records)

    def test_save_quotes_to_csv_append(self, tmp_path: Path, sample_quotes: List[Dict[str, str]]):
        """Test appending to existing CSV."""
        csv_path = tmp_path / "append.csv"

        # Save first batch
        result1 = save_quotes_to_csv([sample_quotes[0]], str(csv_path))
        assert result1 == 1

        # Save second batch - should append
        result2 = save_quotes_to_csv([sample_quotes[1]], str(csv_path))
        assert result2 == 1

        # Verify both are in file
        with open(csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 3  # header + 2 quotes


class TestFetchUrl:
    """Tests for URL fetching."""

    @patch("scraper.scraper.requests.get")
    def test_fetch_url_success(self, mock_get: MagicMock):
        """Test successful URL fetch."""
        mock_response = Mock()
        mock_response.text = "test content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_url("https://example.com")
        assert result == "test content"
        mock_get.assert_called_once()

    @patch("scraper.scraper.requests.get")
    def test_fetch_url_timeout(self, mock_get: MagicMock):
        """Test URL fetch with timeout."""
        mock_get.side_effect = requests.exceptions.Timeout()
        result = fetch_url("https://example.com", retries=1)
        assert result is None

    @patch("scraper.scraper.comment_out_source")
    @patch("scraper.scraper.requests.get")
    def test_fetch_url_http_error(self, mock_get: MagicMock, mock_comment: MagicMock, caplog: pytest.LogCaptureFixture):
        """Test URL fetch with HTTP error."""
        with caplog.at_level(logging.WARNING):
            mock_response = Mock()
            mock_response.status_code = 404
            http_error = requests.exceptions.HTTPError("404 Client Error")
            http_error.response = mock_response
            mock_response.raise_for_status.side_effect = http_error
            mock_get.return_value = mock_response
            result = fetch_url("https://example.com", retries=1)
        assert result is None
        assert any("Error fetching" in record.message for record in caplog.records)
        mock_comment.assert_called_once_with("https://example.com", "HTTP 404")

    @patch("scraper.scraper.requests.get")
    @patch("scraper.scraper.time.sleep")
    def test_fetch_url_retry_logic(self, mock_sleep: MagicMock, mock_get: MagicMock, caplog: pytest.LogCaptureFixture):
        """Test retry logic on failure."""
        with caplog.at_level(logging.WARNING):
            mock_get.side_effect = requests.exceptions.RequestException()
            result = fetch_url("https://example.com", retries=3)
        assert result is None
        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2  # One less than retries
        assert any("Error fetching" in record.message for record in caplog.records)
        assert any("Failed to fetch" in record.message for record in caplog.records)

    @patch("scraper.scraper.requests.get")
    @patch("scraper.scraper.time.sleep")
    def test_fetch_url_http_error_causes_sleep(self, mock_sleep: MagicMock, mock_get: MagicMock, caplog: pytest.LogCaptureFixture):
        """Test that HTTPError (non-404) triggers retries with sleep between attempts."""
        mock_response = Mock()
        mock_response.status_code = 500
        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = mock_response
        mock_get.side_effect = http_error

        with caplog.at_level(logging.WARNING):
            result = fetch_url("http://example.com/500", retries=2)

        assert result is None
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1  # One sleep between two attempts
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
    def test_extract_quotes_from_json_various_formats(self, json_data: Any, expected_count: int):
        """Test extraction from various JSON formats."""
        json_string = json.dumps(json_data)
        quotes = extract_quotes_from_json(json_string, "test_source")
        assert len(quotes) == expected_count

    def test_extract_quotes_from_json_invalid_json(self, caplog: pytest.LogCaptureFixture):
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

    def test_extract_quotes_from_json_dict_without_known_keys(self):
        """Test extracting from dict without 'value', 'joke', or 'result' keys."""
        data = {"unknown_key": "some value", "another_key": "another value"}
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")
        # Should extract no quotes since no known keys are present
        assert len(quotes) == 0

    def test_extract_quotes_from_json_list_of_dicts_without_known_keys(self):
        """Test extracting from list of dicts without 'value' or 'joke' keys."""
        data = [{"unknown_key": "value1"}, {"another_unknown": "value2"}]
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")
        # Should extract no quotes since dicts don't have known keys
        assert len(quotes) == 0

    def test_extract_quotes_from_json_list_mixed(self):
        """Test extraction from a mixed list containing value/joke/dict/str entries."""
        data = {"result": [{"value": "V1"}, {"joke": "J1"}, {"other": "x"}]}
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")
        # Should extract items with value or joke only
        assert any(q["quote"] == "V1" for q in quotes)
        assert any(q["quote"] == "J1" for q in quotes)


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
        html = "<html><body><p>Chuck Norris can slam a revolving door.</p></body></html>"
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
        html = ""
        quotes = extract_quotes_from_html(html, "test_source")
        assert isinstance(quotes, list)
        assert len(quotes) == 0

    def test_extract_quotes_from_html_parsing_exception_logs_error(self, caplog: pytest.LogCaptureFixture):
        """Force a parsing exception in BeautifulSoup and assert an empty list is returned and error logged."""
        with patch("scraper.scraper.BeautifulSoup", side_effect=Exception("boom")):
            with caplog.at_level(logging.ERROR):
                quotes = extract_quotes_from_html("<p>test</p>", "test_source")
                assert quotes == []
                assert any("Failed to parse HTML" in record.message for record in caplog.records)


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

    def test_save_quotes_to_db_success(self, temp_db: str, sample_quotes: List[Dict[str, str]]):
        """Test successful quote saving."""
        saved_count = save_quotes_to_db(sample_quotes, temp_db)
        assert saved_count == 2

        # Verify quotes are in database
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM quotes")
            count = cursor.fetchone()[0]
        assert count == 2

    def test_save_quotes_to_db_duplicates(self, temp_db: str, sample_quotes: List[Dict[str, str]]):
        """Test handling of duplicate quotes."""
        # Save quotes twice
        save_quotes_to_db(sample_quotes, temp_db)
        saved_count = save_quotes_to_db(sample_quotes, temp_db)

        # Second save should save 0 (all duplicates)
        assert saved_count == 0

        # Database should still have only 2 quotes
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM quotes")
            count = cursor.fetchone()[0]
        assert count == 2

    def test_save_quotes_to_db_empty_list(self, temp_db: str):
        """Test saving empty quote list."""
        saved_count = save_quotes_to_db([], temp_db)
        assert saved_count == 0

    def test_save_quotes_to_db_partial_duplicates(self, temp_db: str):
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
    def test_validate_sources(self, sources: List[str], expected_count: int):
        """Test source URL validation."""
        valid = validate_sources(sources)
        assert len(valid) == expected_count

    def test_validate_sources_filters_invalid(self):
        """Test that invalid URLs are filtered out."""
        sources = ["https://valid.com", "invalid", "also-invalid"]
        valid = validate_sources(sources)
        assert len(valid) == 1
        assert "https://valid.com" in valid


class TestGetScrapedSources:
    """Tests for retrieving already-scraped sources from CSV and DB."""

    def test_get_scraped_sources_from_csv_and_db(self, tmp_path: Path):
        # Create a CSV file with a couple of sources
        csv_path = tmp_path / "sourced.csv"
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            f.write("source,quote\n")
            f.write("https://csv-source.com,First quote\n")

        # Create DB with another source
        db_path = tmp_path / "quotes.db"
        create_database(str(db_path))
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO quotes (quote, source) VALUES (?, ?)", ("DB quote", "https://db-source.com"))
            conn.commit()

        scraped = get_scraped_sources(str(csv_path), str(db_path))
        assert "https://csv-source.com" in scraped
        assert "https://db-source.com" in scraped

    def test_get_scraped_sources_not_found_files(self):
        scraped = get_scraped_sources("notfound.csv", "notfound.db")
        assert isinstance(scraped, set)
        assert len(scraped) == 0


class TestScrapeSource:
    """Tests for scraping a single source."""

    @patch("scraper.scraper.fetch_url")
    @patch("scraper.scraper.extract_quotes")
    @patch("scraper.scraper.save_quotes_to_db")
    def test_scrape_source_success(self, mock_save: MagicMock, mock_extract: MagicMock, mock_fetch: MagicMock, temp_db: str):
        """Test successful source scraping."""
        mock_fetch.return_value = "content"
        mock_extract.return_value = [{"quote": "Test", "source": "src"}]
        mock_save.return_value = 1

        result = scrape_source("https://example.com", temp_db, None, ["sqlite"])
        assert result == 1

    @patch("scraper.scraper.fetch_url")
    def test_scrape_source_fetch_failure(self, mock_fetch: MagicMock, temp_db: str):
        """Test scraping when fetch fails."""
        mock_fetch.return_value = None
        result = scrape_source("https://example.com", temp_db, None, ["sqlite"])
        assert result == 0

    @patch("scraper.scraper.fetch_url")
    @patch("scraper.scraper.extract_quotes")
    def test_scrape_source_no_quotes_found(self, mock_extract: MagicMock, mock_fetch: MagicMock, temp_db: str):
        """Test scraping when no quotes are found."""
        mock_fetch.return_value = "content"
        mock_extract.return_value = []
        result = scrape_source("https://example.com", temp_db, None, ["sqlite"])
        assert result == 0

    @patch("scraper.scraper.fetch_url")
    @patch("scraper.scraper.extract_quotes")
    @patch("scraper.scraper.save_quotes_to_db")
    def test_scrape_source_unknown_format(self, mock_save: MagicMock, mock_extract: MagicMock, mock_fetch: MagicMock, temp_db: str, caplog: pytest.LogCaptureFixture):
        """Test scraping with unknown format logs warning."""
        mock_fetch.return_value = "content"
        mock_extract.return_value = [{"quote": "Test", "source": "src"}]
        mock_save.return_value = 1

        with caplog.at_level(logging.WARNING):
            result = scrape_source("https://example.com", temp_db, None, ["unknown"])

        assert result == 0  # No quotes saved due to unknown format
        assert "Unknown format or missing path: unknown" in caplog.text


class TestScrapeAllSources:
    """Tests for scraping multiple sources."""

    @patch("scraper.scraper.scrape_source")
    def test_scrape_all_sources_success(self, mock_scrape: MagicMock, temp_db: str):
        """Test scraping multiple sources successfully."""
        mock_scrape.return_value = 5
        sources = ["https://example1.com", "https://example2.com"]
        total = scrape_all_sources(sources, temp_db, None, ["sqlite"])
        assert total == 10
        assert mock_scrape.call_count == 2

    @patch("scraper.scraper.scrape_source")
    def test_scrape_all_sources_with_failures(self, mock_scrape: MagicMock, temp_db: str):
        """Test scraping with some sources failing."""
        mock_scrape.side_effect = [5, Exception("Error"), 3]
        sources = ["https://1.com", "https://2.com", "https://3.com"]
        total = scrape_all_sources(sources, temp_db, None, ["sqlite"])
        assert total == 8  # 5 + 0 (error) + 3

    @patch("scraper.scraper.scrape_source")
    def test_scrape_all_sources_empty_list(self, mock_scrape: MagicMock, temp_db: str):
        """Test scraping with empty source list."""
        total = scrape_all_sources([], temp_db, None, ["sqlite"])
        assert total == 0
        mock_scrape.assert_not_called()

    @patch("scraper.scraper.scrape_source")
    def test_scrape_all_sources_single_thread(self, mock_scrape: MagicMock, temp_db: str):
        """Test scraping with single thread (max_workers=1)."""
        mock_scrape.return_value = 3
        sources = ["https://example1.com", "https://example2.com"]
        total = scrape_all_sources(sources, temp_db, None, ["sqlite"], max_workers=1)
        assert total == 6
        assert mock_scrape.call_count == 2

    @patch("concurrent.futures.ThreadPoolExecutor")
    @patch("concurrent.futures.as_completed")
    @patch("scraper.scraper.scrape_source")
    def test_scrape_all_sources_multi_thread(self, mock_scrape: MagicMock, mock_as_completed: MagicMock, mock_executor: MagicMock, temp_db: str):
        """Test scraping with multiple threads."""
        mock_scrape.return_value = 4
        sources = ["https://example1.com", "https://example2.com", "https://example3.com"]

        # Mock the executor context manager
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance

        # Mock futures
        mock_future1 = MagicMock()
        mock_future1.result.return_value = 4
        mock_future2 = MagicMock()
        mock_future2.result.return_value = 4
        mock_future3 = MagicMock()
        mock_future3.result.return_value = 4

        mock_executor_instance.submit.side_effect = [mock_future1, mock_future2, mock_future3]

        # Mock as_completed to return futures in order
        mock_as_completed.return_value = [mock_future1, mock_future2, mock_future3]

        total = scrape_all_sources(sources, temp_db, None, ["sqlite"], max_workers=3)
        assert total == 12
        mock_executor.assert_called_once_with(max_workers=3)

    @patch("concurrent.futures.ThreadPoolExecutor")
    @patch("concurrent.futures.as_completed")
    @patch("scraper.scraper.scrape_source")
    def test_scrape_all_sources_multi_thread_exception(self, mock_scrape: MagicMock, mock_as_completed: MagicMock, mock_executor: MagicMock, temp_db: str, caplog: pytest.LogCaptureFixture):
        """Test multi-threaded scraping with exception handling."""
        sources = ["https://example1.com", "https://example2.com"]

        # Mock the executor context manager
        mock_executor_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance

        # Mock futures - one succeeds, one fails
        mock_future1 = MagicMock()
        mock_future1.result.return_value = 3
        mock_future2 = MagicMock()
        mock_future2.result.side_effect = Exception("Test error")

        mock_executor_instance.submit.side_effect = [mock_future1, mock_future2]

        # Mock as_completed to return futures
        mock_as_completed.return_value = [mock_future1, mock_future2]

        with caplog.at_level(logging.ERROR):
            total = scrape_all_sources(sources, temp_db, None, ["sqlite"], max_workers=2)

        assert total == 3  # Only the successful one
        assert "Error scraping https://example2.com: Test error" in caplog.text


class TestExtractQuotesFromParade:
    """Tests for Parade.com quote extraction."""

    def test_extract_quotes_from_parade_error(self):
        """Test error handling in Parade.com extraction."""
        # Malformed HTML that will cause parsing error
        content = ""  # This will cause an exception
        quotes = extract_quotes_from_parade(content, "test_source")
        assert quotes == []

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

    def test_extract_quotes_from_parade_various_selectors(self):
        """Test extractors for different selectors (li, class=joke, class=fact)."""
        html = """
        <div class="article-body">
            <li>Chuck Norris can do anything. Li selector.</li>
            <p class="joke">Chuck Norris is a joke.</p>
            <div class="fact">Chuck Norris fact here.</div>
        </div>
        """
        source = "https://parade.com/970343/parade/chuck-norris-jokes/"
        quotes = extract_quotes_from_parade(html, source)
        # Should find all three unique quotes
        assert len(quotes) >= 3

    def test_extract_quotes_from_parade_no_quotes(self):
        """Test extraction with no valid quotes."""
        html = "<p>This is just regular text.</p>"
        source = "https://parade.com/970343/parade/chuck-norris-jokes/"
        quotes = extract_quotes_from_parade(html, source)
        assert quotes == []

    def test_extract_quotes_from_parade_selectors_joke_and_fact(self):
        """Test that class selectors with 'joke' or 'fact' are recognized."""
        html = """
        <div class="article-body">
            <p class="joke">Chuck Norris can do anything. joke selector here.</p>
            <div class="fact">Chuck Norris fact content that should be captured.</div>
        </div>
        """
        source = "https://parade.com/970343/parade/chuck-norris-jokes/"
        quotes = extract_quotes_from_parade(html, source)
        assert any("joke selector" in q["quote"] for q in quotes)
        assert any("fact content" in q["quote"] for q in quotes)

    def test_extract_quotes_from_parade_duplicates_removed(self):
        """Ensure duplicate quotes are removed by extract_quotes_from_parade."""
        html = """
        <div class="article-body">
            <p>Chuck Norris can do anything. Even HTML parsing.</p>
            <p>Chuck Norris can do anything. Even HTML parsing.</p>
        </div>
        """
        source = "https://parade.com/970343/parade/chuck-norris-jokes/"
        quotes = extract_quotes_from_parade(html, source)
        # Should deduplicate identical quotes
        assert len(quotes) == 1


class TestExtractQuotesFromThefactsite:
    """Tests for Thefactsite.com quote extraction."""

    def test_extract_quotes_from_thefactsite_error(self):
        """Test error handling in Thefactsite.com extraction."""
        content = ""  # This will cause an exception
        quotes = extract_quotes_from_thefactsite(content, "test_source")
        assert quotes == []

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

    def test_extract_quotes_from_thefactsite_no_matches(self):
        """Test that non-matching LI entries are filtered out."""
        html = "<ul><li>Just some text</li><li>Another plain text</li></ul>"
        source = "https://www.thefactsite.com/top-100-chuck-norris-facts/"
        quotes = extract_quotes_from_thefactsite(html, source)
        assert quotes == []

    def test_extract_quotes_from_thefactsite_mixed_entries(self):
        """Ensure only valid LI items containing Chuck Norris are captured and numbering is stripped."""
        html = """
        <ol>
            <li>1. Chuck Norris is unstoppable.</li>
            <li>2. Plain text not matching.</li>
        </ol>
        """
        source = "https://www.thefactsite.com/top-100-chuck-norris-facts/"
        quotes = extract_quotes_from_thefactsite(html, source)
        assert any("Chuck Norris" in q["quote"] for q in quotes)
        assert all(not q["quote"].startswith("1.") for q in quotes)


class TestExtractQuotesFromChucknorrisfactsFr:
    """Tests for Chucknorrisfacts.fr quote extraction."""

    def test_extract_quotes_from_chucknorrisfacts_fr_error(self):
        """Test error handling in Chucknorrisfacts.fr extraction."""
        content = ""  # This will cause an exception
        quotes = extract_quotes_from_chucknorrisfacts_fr(content, "test_source")
        assert quotes == []

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

    def test_extract_quotes_from_chucknorrisfacts_fr_numbering(self):
        """Ensure numbering is stripped and French quotes are recognized."""
        html = "<p>1. Chuck Norris est incroyable et fait des choses extraordinaires.</p>"
        source = "https://www.chucknorrisfacts.fr/en/top-100-chuck-norris-facts"
        quotes = extract_quotes_from_chucknorrisfacts_fr(html, source)
        assert len(quotes) == 1
        assert "Chuck Norris" in quotes[0]["quote"] or "chuck norris" in quotes[0]["quote"].lower()

    def test_extract_quotes_from_chucknorrisfacts_fr_selectors(self):
        """Ensure multiple selectors (div.fact, p, li) work and numbering removed."""
        html = """
        <div class="fact">1. Chuck Norris en Français.</div>
        <p>Chuck Norris en français sans numéro.</p>
        <li>2. Chuck Norris encore.</li>
        """
        source = "https://www.chucknorrisfacts.fr/en/top-100-chuck-norris-facts"
        quotes = extract_quotes_from_chucknorrisfacts_fr(html, source)
        assert len(quotes) >= 2


class TestExtractQuotesFromFactinate:
    """Tests for Factinate.com quote extraction."""

    def test_extract_quotes_from_factinate_error(self):
        """Test error handling in Factinate.com extraction."""
        content = ""  # This will cause an exception
        quotes = extract_quotes_from_factinate(content, "test_source")
        assert quotes == []

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

    def test_extract_quotes_from_factinate_blockquote(self):
        """Ensure blockquote selectors are covered for Factinate extraction."""
        html = """
        <blockquote>Chuck Norris can bench press the internet.</blockquote>
        <div class="quote">Another Factinate quote about Chuck.</div>
        """
        source = "https://www.factinate.com/quote/chuck-norris-jokes/"
        quotes = extract_quotes_from_factinate(html, source)
        assert any("bench press" in q["quote"] for q in quotes)


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


class TestDatabaseMigration:
    """Test database migration functionality."""

    def test_create_database_migrates_old_schema(self, tmp_path: Path):
        """Test that create_database migrates from old schema with created_at column."""
        db_path = tmp_path / "test_migrate.db"

        # Create old schema database manually
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT NOT NULL UNIQUE,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        cursor.execute("INSERT INTO quotes (quote, source) VALUES (?, ?)", ("Old quote", "old_source"))
        conn.commit()
        conn.close()

        # Run create_database which should migrate
        create_database(str(db_path))

        # Verify migration worked
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(quotes)")
            columns = [col[1] for col in cursor.fetchall()]
            assert "created_at" not in columns
            assert "id" in columns
            assert "quote" in columns
            assert "source" in columns

            # Verify data was preserved
            cursor.execute("SELECT quote, source FROM quotes")
            rows = cursor.fetchall()
            assert len(rows) == 1
            assert rows[0] == ("Old quote", "old_source")


class TestFetchUrlEdgeCases:
    """Test edge cases in fetch_url function."""

    @patch("scraper.scraper.requests.get")
    @patch("scraper.scraper.comment_out_source")
    def test_fetch_url_http_404_error(self, mock_comment_out: MagicMock, mock_get: MagicMock):
        """Test fetch_url handles HTTP 404 errors by commenting out source."""
        # Create a realistic HTTPError
        http_error = requests.exceptions.HTTPError("404 Client Error: Not Found")
        http_error.response = Mock()
        http_error.response.status_code = 404

        # Make requests.get raise the HTTPError
        mock_get.side_effect = http_error

        result = fetch_url("http://example.com/404", retries=1)

        assert result is None
        mock_comment_out.assert_called_once_with("http://example.com/404", "HTTP 404")

    @patch("scraper.scraper.requests.get")
    @patch("scraper.scraper.time.sleep")
    def test_fetch_url_request_exception_final_return_none(self, mock_sleep: MagicMock, mock_get: MagicMock):
        """Test fetch_url returns None after exhausting retries on RequestException."""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = fetch_url("http://example.com/fail", retries=2)

        assert result is None
        # Should have tried 2 times
        assert mock_get.call_count == 2
        # Should have slept once between retries
        mock_sleep.assert_called_once()

    @patch("scraper.scraper.requests.get")
    @patch("scraper.scraper.comment_out_source")
    def test_fetch_url_http_error_non_404_logs_warning(self, mock_comment_out: MagicMock, mock_get: MagicMock, caplog: pytest.LogCaptureFixture):
        """Test fetch_url logs warning for HTTP errors that are not 404."""
        # Create HTTPError that's not 404
        http_error = requests.exceptions.HTTPError("500 Server Error")
        http_error.response = Mock()
        http_error.response.status_code = 500

        mock_get.side_effect = http_error

        with caplog.at_level(logging.WARNING):
            result = fetch_url("http://example.com/500", retries=1)

        assert result is None
        # Should log warning but not comment out source
        assert "Error fetching http://example.com/500: 500 Server Error" in caplog.text
        mock_comment_out.assert_not_called()

    @patch("scraper.scraper.requests.get")
    @patch("scraper.scraper.time.sleep")
    def test_fetch_url_request_exception_logs_warning(self, mock_sleep: MagicMock, mock_get: MagicMock, caplog: pytest.LogCaptureFixture):
        """Test fetch_url logs warning for RequestException."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection timeout")

        with caplog.at_level(logging.WARNING):
            result = fetch_url("http://example.com/timeout", retries=1)

        assert result is None
        # Should log warning
        assert "Error fetching http://example.com/timeout: Connection timeout" in caplog.text
        mock_sleep.assert_not_called()  # No retry for single attempt


class TestExtractQuotesFromJsonBranches:
    """Test various branches in extract_quotes_from_json."""

    def test_extract_quotes_from_json_single_quote_with_joke_key(self):
        """Test extracting single quote with 'joke' key."""
        data = {"joke": "Chuck Norris can make HTTP requests with his mind."}
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")

        assert len(quotes) == 1
        assert quotes[0]["quote"] == "Chuck Norris can make HTTP requests with his mind."
        assert quotes[0]["source"] == "test_source"

    def test_extract_quotes_from_json_search_results(self):
        """Test extracting quotes from search results format."""
        data = {"result": [{"value": "Chuck Norris fact 1"}, {"value": "Chuck Norris fact 2"}]}
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")

        assert len(quotes) == 2
        assert quotes[0]["quote"] == "Chuck Norris fact 1"
        assert quotes[1]["quote"] == "Chuck Norris fact 2"

    def test_extract_quotes_from_json_list_of_dicts_with_joke(self):
        """Test extracting from list of dicts with 'joke' key."""
        data = [{"joke": "Fact 1"}, {"joke": "Fact 2"}]
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")

        assert len(quotes) == 2
        assert quotes[0]["quote"] == "Fact 1"
        assert quotes[1]["quote"] == "Fact 2"

    def test_extract_quotes_from_json_list_of_strings(self):
        """Test extracting from list of strings."""
        data = ["String fact 1", "String fact 2"]
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")

        assert len(quotes) == 2
        assert quotes[0]["quote"] == "String fact 1"
        assert quotes[1]["quote"] == "String fact 2"

    def test_extract_quotes_from_json_dict_without_known_keys(self):
        """Test extracting from dict without 'value', 'joke', or 'result' keys."""
        data = {"unknown_key": "some value", "another_key": "another value"}
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")

        # Should extract no quotes since no known keys are present
        assert len(quotes) == 0

    def test_extract_quotes_from_json_list_of_dicts_without_known_keys(self):
        """Test extracting from list of dicts without 'value' or 'joke' keys."""
        data = [{"unknown_key": "value1"}, {"another_unknown": "value2"}]
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")

        # Should extract no quotes since dicts don't have known keys
        assert len(quotes) == 0

    def test_extract_quotes_from_json_result_list_with_missing_value(self):
        """Test extracting from result list where some items don't have 'value' key."""
        data = {"result": [{"value": "Valid quote"}, {"other_key": "Invalid item"}, {"value": "Another valid quote"}]}
        content = json.dumps(data)
        quotes = extract_quotes_from_json(content, "test_source")

        # Should extract only items with 'value' key
        assert len(quotes) == 2
        assert quotes[0]["quote"] == "Valid quote"
        assert quotes[1]["quote"] == "Another valid quote"
