"""Tests for scraper CLI and main function."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from scraper.scraper import main, parse_arguments, setup_logging


class TestSetupLogging:
    """Tests for setup_logging function."""

    @patch("scraper.scraper.logging.basicConfig")
    def test_setup_logging_not_verbose(self, mock_config):
        """Test logging setup when not verbose."""
        setup_logging(verbose=False)
        mock_config.assert_called_once()

    @patch("scraper.scraper.logging.basicConfig")
    def test_setup_logging_verbose(self, mock_config):
        """Test logging setup when verbose."""
        setup_logging(verbose=True)
        mock_config.assert_called_once()


class TestParseArguments:
    """Tests for argument parsing."""

    def test_parse_arguments_defaults(self):
        """Test default argument values."""
        with patch("sys.argv", ["scraper.py"]):
            args = parse_arguments()
            assert args.output == "scraper/quotes.db"
            assert args.format == "both"
            assert args.verbose is False
            assert args.sources is None
            assert args.dry_run is False
            assert args.threads == 4

    def test_parse_arguments_with_sources(self):
        """Test parsing with custom sources."""
        with patch(
            "sys.argv",
            ["scraper.py", "--sources", "https://example.com", "https://test.com"],
        ):
            args = parse_arguments()
            assert args.sources == ["https://example.com", "https://test.com"]

    def test_parse_arguments_with_output(self):
        """Test parsing with custom output."""
        with patch("sys.argv", ["scraper.py", "--output", "custom.db"]):
            args = parse_arguments()
            assert args.output == "custom.db"

    def test_parse_arguments_verbose(self):
        """Test parsing verbose flag."""
        with patch("sys.argv", ["scraper.py", "-v"]):
            args = parse_arguments()
            assert args.verbose is True

    def test_parse_arguments_short_options(self):
        """Test short option forms."""
        with patch(
            "sys.argv",
            ["scraper.py", "-s", "https://example.com", "-o", "out.db", "-v"],
        ):
            args = parse_arguments()
            assert args.sources == ["https://example.com"]
            assert args.output == "out.db"
            assert args.verbose is True

    def test_parse_arguments_dry_run(self):
        """Test dry-run flag parsing."""
        with patch("sys.argv", ["scraper.py", "--dry-run"]):
            args = parse_arguments()
            assert args.dry_run is True

        with patch("sys.argv", ["scraper.py", "--dryrun"]):
            args = parse_arguments()
            assert args.dry_run is True

        with patch("sys.argv", ["scraper.py", "-d"]):
            args = parse_arguments()
            assert args.dry_run is True

    def test_parse_arguments_threads(self):
        """Test threads parameter parsing."""
        with patch("sys.argv", ["scraper.py", "--threads", "8"]):
            args = parse_arguments()
            assert args.threads == 8

        with patch("sys.argv", ["scraper.py", "--thread", "2"]):
            args = parse_arguments()
            assert args.threads == 2

        with patch("sys.argv", ["scraper.py", "-t", "1"]):
            args = parse_arguments()
            assert args.threads == 1


class TestMain:
    """Tests for main function."""

    @patch("scraper.scraper.scrape_all_sources")
    @patch("scraper.scraper.create_database")
    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_success(self, mock_parse, mock_validate, mock_create, mock_scrape):
        """Test successful main execution."""
        mock_args = MagicMock()
        mock_args.sources = None
        mock_args.output = "test.db"
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_args.threads = 4
        mock_parse.return_value = mock_args

        mock_validate.return_value = ["https://example.com"]
        mock_scrape.return_value = 10

        result = main()
        assert result == 0

    @patch("scraper.scraper.scrape_all_sources")
    @patch("scraper.scraper.create_database")
    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_no_valid_sources(
        self, mock_parse, mock_validate, mock_create, mock_scrape
    ):
        """Test main with no valid sources."""
        mock_args = MagicMock()
        mock_args.sources = ["invalid"]
        mock_args.output = "test.db"
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_args.threads = 4
        mock_parse.return_value = mock_args

        mock_validate.return_value = []

        result = main()
        assert result == 1

    @patch("scraper.scraper.scrape_all_sources")
    @patch("scraper.scraper.create_database")
    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_no_quotes_saved(
        self, mock_parse, mock_validate, mock_create, mock_scrape
    ):
        """Test main when no quotes are saved."""
        mock_args = MagicMock()
        mock_args.sources = None
        mock_args.output = "test.db"
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_args.threads = 4
        mock_parse.return_value = mock_args

        mock_validate.return_value = ["https://example.com"]
        mock_scrape.return_value = 0

        result = main()
        assert result == 1

    @patch("scraper.scraper.scrape_all_sources")
    @patch("scraper.scraper.create_database")
    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.load_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_uses_default_sources(
        self, mock_parse, mock_load, mock_validate, mock_create, mock_scrape
    ):
        """Test that main uses default sources when none provided."""
        mock_args = MagicMock()
        mock_args.sources = None
        mock_args.output = "test.db"
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_args.threads = 4
        mock_parse.return_value = mock_args

        mock_load.return_value = ["https://api.chucknorris.io/jokes/random"]
        mock_validate.return_value = ["https://api.chucknorris.io/jokes/random"]
        mock_scrape.return_value = 5

        result = main()

        # Verify default sources were used
        mock_validate.assert_called_once()
        call_args = mock_validate.call_args[0][0]
        assert "https://api.chucknorris.io/jokes/random" in call_args

    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.load_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_dry_run(self, mock_parse, mock_load, mock_validate):
        """Test main function in dry-run mode."""
        mock_args = MagicMock()
        mock_args.sources = None
        mock_args.dry_run = True
        mock_args.verbose = False
        mock_parse.return_value = mock_args

        mock_load.return_value = ["https://api.chucknorris.io/jokes/random", "https://example.com"]
        mock_validate.return_value = ["https://api.chucknorris.io/jokes/random", "https://example.com"]

        with patch("scraper.scraper.logging.info") as mock_log:
            result = main()
            assert result == 0

            # Verify dry-run logging
            log_calls = [call.args[0] for call in mock_log.call_args_list]
            assert "DRY RUN MODE: Validating sources and simulating scraping" in log_calls
            assert "Found 2 valid sources to scrape:" in log_calls
            assert "Dry run completed. No network calls were made." in log_calls

    @patch("scraper.scraper.scrape_all_sources")
    @patch("scraper.scraper.create_database")
    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_with_threading(self, mock_parse, mock_validate, mock_create, mock_scrape):
        """Test main function with custom thread count."""
        mock_args = MagicMock()
        mock_args.sources = None
        mock_args.output = "test.db"
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_args.threads = 8
        mock_parse.return_value = mock_args

        mock_validate.return_value = ["https://example.com"]
        mock_scrape.return_value = 10

        result = main()
        assert result == 0

        # Verify scrape_all_sources was called with correct thread count
        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        assert call_args[1]['max_workers'] == 8

    @patch("scraper.scraper.scrape_all_sources")
    @patch("scraper.scraper.create_database")
    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_format_both(self, mock_parse, mock_validate, mock_create, mock_scrape):
        """Test main function with format='both'."""
        mock_args = MagicMock()
        mock_args.sources = None
        mock_args.output = "test.db"
        mock_args.format = "both"
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_args.threads = 4
        mock_parse.return_value = mock_args

        mock_validate.return_value = ["https://example.com"]
        mock_scrape.return_value = 10

        result = main()
        assert result == 0

        # Verify both formats were used
        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        assert call_args[0][3] == ["sqlite", "csv"]  # formats is the 4th positional arg
        assert call_args[0][1] == "scraper/quotes.db"  # db_path (default for both)
        assert call_args[0][2] == "scraper/quotes.csv"  # csv_path (default for both)

    @patch("scraper.scraper.scrape_all_sources")
    @patch("scraper.scraper.create_database")
    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_format_sqlite(self, mock_parse, mock_validate, mock_create, mock_scrape):
        """Test main function with format='sqlite'."""
        mock_args = MagicMock()
        mock_args.sources = None
        mock_args.output = "custom.db"
        mock_args.format = "sqlite"
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_args.threads = 4
        mock_parse.return_value = mock_args

        mock_validate.return_value = ["https://example.com"]
        mock_scrape.return_value = 10

        result = main()
        assert result == 0

        # Verify sqlite format was used
        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        assert call_args[0][3] == ["sqlite"]  # formats
        assert call_args[0][1] == "custom.db"  # db_path
        assert call_args[0][2] is None  # csv_path

    @patch("scraper.scraper.scrape_all_sources")
    @patch("scraper.scraper.create_database")
    @patch("scraper.scraper.validate_sources")
    @patch("scraper.scraper.parse_arguments")
    def test_main_format_csv(self, mock_parse, mock_validate, mock_create, mock_scrape):
        """Test main function with format='csv'."""
        mock_args = MagicMock()
        mock_args.sources = None
        mock_args.output = "custom.csv"
        mock_args.format = "csv"
        mock_args.verbose = False
        mock_args.dry_run = False
        mock_args.threads = 4
        mock_parse.return_value = mock_args

        mock_validate.return_value = ["https://example.com"]
        mock_scrape.return_value = 10

        result = main()
        assert result == 0

        # Verify csv format was used
        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        assert call_args[0][3] == ["csv"]  # formats
        assert call_args[0][1] is None  # db_path
        assert call_args[0][2] == "custom.csv"  # csv_path
