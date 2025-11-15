"""Tests for generator CLI and main function."""

from unittest.mock import MagicMock, patch

import pytest

from quotes.generator import main, parse_arguments, setup_logging, validate_arguments


class TestSetupLogging:
    """Tests for setup_logging function."""

    @patch("quotes.generator.logging.basicConfig")
    def test_setup_logging_not_verbose(self, mock_config):
        """Test logging setup when not verbose."""
        setup_logging(verbose=False)
        mock_config.assert_called_once()

    @patch("quotes.generator.logging.basicConfig")
    def test_setup_logging_verbose(self, mock_config):
        """Test logging setup when verbose."""
        setup_logging(verbose=True)
        mock_config.assert_called_once()


class TestParseArguments:
    """Tests for argument parsing."""

    def test_parse_arguments_defaults(self):
        """Test default argument values."""
        with patch("sys.argv", ["generator.py"]):
            args = parse_arguments()
            assert args.count == 1
            assert args.seed is None
            assert args.output is None
            assert args.format == "text"
            assert args.database == "download/quotes.db"
            assert args.verbose is False

    def test_parse_arguments_with_count(self):
        """Test parsing with custom count."""
        with patch("sys.argv", ["generator.py", "--count", "100"]):
            args = parse_arguments()
            assert args.count == 100

    def test_parse_arguments_with_seed(self):
        """Test parsing with seed."""
        with patch("sys.argv", ["generator.py", "--seed", "42"]):
            args = parse_arguments()
            assert args.seed == 42

    def test_parse_arguments_with_output(self):
        """Test parsing with output file."""
        with patch("sys.argv", ["generator.py", "--output", "quotes.json"]):
            args = parse_arguments()
            assert args.output == "quotes.json"

    def test_parse_arguments_with_format(self):
        """Test parsing with different formats."""
        for fmt in ["text", "json", "csv"]:
            with patch("sys.argv", ["generator.py", "--format", fmt]):
                args = parse_arguments()
                assert args.format == fmt

    def test_parse_arguments_short_options(self):
        """Test short option forms."""
        with patch(
            "sys.argv",
            ["generator.py", "-c", "50", "-s", "99", "-f", "json", "-v"],
        ):
            args = parse_arguments()
            assert args.count == 50
            assert args.seed == 99
            assert args.format == "json"
            assert args.verbose is True


class TestValidateArguments:
    """Tests for argument validation."""

    def test_validate_arguments_valid(self):
        """Test validation with valid arguments."""
        args = MagicMock()
        args.count = 100
        assert validate_arguments(args) is True

    def test_validate_arguments_count_too_low(self):
        """Test validation with count less than 1."""
        args = MagicMock()
        args.count = 0
        assert validate_arguments(args) is False

    def test_validate_arguments_count_negative(self):
        """Test validation with negative count."""
        args = MagicMock()
        args.count = -5
        assert validate_arguments(args) is False

    def test_validate_arguments_count_too_high(self):
        """Test validation with count exceeding max."""
        args = MagicMock()
        args.count = 10_000_001
        assert validate_arguments(args) is False

    def test_validate_arguments_max_count(self):
        """Test validation with maximum allowed count."""
        args = MagicMock()
        args.count = 10_000_000
        assert validate_arguments(args) is True


class TestMain:
    """Tests for main function."""

    @patch("quotes.generator.export_quotes")
    @patch("quotes.generator.generate_quotes")
    @patch("quotes.generator.validate_database")
    @patch("quotes.generator.parse_arguments")
    def test_main_success(
        self, mock_parse, mock_validate_db, mock_generate, mock_export
    ):
        """Test successful main execution."""
        mock_args = MagicMock()
        mock_args.count = 10
        mock_args.seed = None
        mock_args.database = "test.db"
        mock_args.format = "text"
        mock_args.output = None
        mock_args.verbose = False
        mock_parse.return_value = mock_args

        mock_validate_db.return_value = True
        mock_generate.return_value = [{"quote": "test", "id": 1}]

        result = main()
        assert result == 0

    @patch("quotes.generator.parse_arguments")
    def test_main_invalid_arguments(self, mock_parse):
        """Test main with invalid arguments."""
        mock_args = MagicMock()
        mock_args.count = 0  # Invalid
        mock_args.verbose = False
        mock_parse.return_value = mock_args

        result = main()
        assert result == 1

    @patch("quotes.generator.validate_database")
    @patch("quotes.generator.parse_arguments")
    def test_main_invalid_database(self, mock_parse, mock_validate_db):
        """Test main with invalid database."""
        mock_args = MagicMock()
        mock_args.count = 10
        mock_args.database = "nonexistent.db"
        mock_args.verbose = False
        mock_parse.return_value = mock_args

        mock_validate_db.return_value = False

        result = main()
        assert result == 1

    @patch("quotes.generator.generate_quotes")
    @patch("quotes.generator.validate_database")
    @patch("quotes.generator.parse_arguments")
    def test_main_no_quotes_generated(
        self, mock_parse, mock_validate_db, mock_generate
    ):
        """Test main when no quotes are generated."""
        mock_args = MagicMock()
        mock_args.count = 10
        mock_args.seed = None
        mock_args.database = "test.db"
        mock_args.verbose = False
        mock_parse.return_value = mock_args

        mock_validate_db.return_value = True
        mock_generate.return_value = []

        result = main()
        assert result == 1

    @patch("quotes.generator.export_quotes")
    @patch("quotes.generator.generate_quotes")
    @patch("quotes.generator.validate_database")
    @patch("quotes.generator.parse_arguments")
    def test_main_with_all_options(
        self, mock_parse, mock_validate_db, mock_generate, mock_export
    ):
        """Test main with all options specified."""
        mock_args = MagicMock()
        mock_args.count = 100
        mock_args.seed = 42
        mock_args.database = "custom.db"
        mock_args.format = "json"
        mock_args.output = "output.json"
        mock_args.verbose = True
        mock_parse.return_value = mock_args

        mock_validate_db.return_value = True
        mock_generate.return_value = [{"quote": "test", "id": 1}]

        result = main()
        assert result == 0

        # Verify generate was called with correct args
        mock_generate.assert_called_once_with("custom.db", 100, 42)

        # Verify export was called with correct args
        mock_export.assert_called_once()
        export_args = mock_export.call_args[0]
        assert export_args[1] == "json"
        assert export_args[2] == "output.json"
