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
        mock_parse.return_value = mock_args

        mock_load.return_value = ["https://api.chucknorris.io/jokes/random"]
        mock_validate.return_value = ["https://api.chucknorris.io/jokes/random"]
        mock_scrape.return_value = 5

        result = main()

        # Verify default sources were used
        mock_validate.assert_called_once()
        call_args = mock_validate.call_args[0][0]
        assert "https://api.chucknorris.io/jokes/random" in call_args
