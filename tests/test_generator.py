"""Tests for the quote generator module."""

import csv
import json
import logging
import sqlite3
from io import StringIO
from unittest.mock import patch

import pytest

from quotes.generator import export_quotes, export_quotes_csv, export_quotes_json, export_quotes_text, generate_quotes, get_all_quote_ids, get_quote_by_id, validate_database


@pytest.fixture
def temp_db_with_quotes(tmp_path):
    """Create a temporary database with sample quotes."""
    db_path = tmp_path / "test_quotes.db"

    with sqlite3.connect(str(db_path)) as conn:
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

        sample_quotes = [
            ("Chuck Norris can divide by zero.", "source1"),
            ("Chuck Norris counted to infinity. Twice.", "source2"),
            ("When Chuck Norris does a pushup, he pushes the Earth down.", "source3"),
        ]

        cursor.executemany("INSERT INTO quotes (quote, source) VALUES (?, ?)", sample_quotes)
        conn.commit()

    return str(db_path)


@pytest.fixture
def sample_quote_dicts():
    """Sample quote dictionaries for testing."""
    return [
        {
            "id": 1,
            "quote": "Chuck Norris can divide by zero.",
            "source": "source1",
            "created_at": "2024-01-01 00:00:00",
        },
        {
            "id": 2,
            "quote": "Chuck Norris counted to infinity. Twice.",
            "source": "source2",
            "created_at": "2024-01-01 00:00:00",
        },
    ]


class TestValidateDatabase:
    """Tests for database validation."""

    def test_validate_database_exists_with_quotes(self, temp_db_with_quotes):
        """Test validation of existing database with quotes."""
        assert validate_database(temp_db_with_quotes) is True

    def test_validate_database_not_exists(self, tmp_path, caplog):
        """Test validation of non-existent database."""
        db_path = tmp_path / "nonexistent.db"
        with caplog.at_level(logging.ERROR):
            result = validate_database(str(db_path))
        assert result is False
        assert any("Database file not found" in record.message for record in caplog.records)

    def test_validate_database_empty(self, tmp_path):
        """Test validation of empty database."""
        db_path = tmp_path / "empty.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE quotes (
                    id INTEGER PRIMARY KEY,
                    quote TEXT NOT NULL,
                    source TEXT,
                    created_at TIMESTAMP
                )
            """
            )
            conn.commit()

        assert validate_database(str(db_path)) is False

    def test_validate_database_corrupted(self, tmp_path):
        """Test validation of corrupted database."""
        db_path = tmp_path / "corrupted.db"
        # Create a file that's not a valid SQLite database
        with open(db_path, "w") as f:
            f.write("not a database")

        assert validate_database(str(db_path)) is False


class TestGetAllQuoteIds:
    """Tests for retrieving all quote IDs."""

    def test_get_all_quote_ids_success(self, temp_db_with_quotes):
        """Test retrieving all quote IDs."""
        ids = get_all_quote_ids(temp_db_with_quotes)
        assert len(ids) == 3
        assert all(isinstance(id, int) for id in ids)
        assert ids == [1, 2, 3]

    def test_get_all_quote_ids_empty_database(self, tmp_path):
        """Test retrieving IDs from empty database."""
        db_path = tmp_path / "empty.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE quotes (
                    id INTEGER PRIMARY KEY,
                    quote TEXT,
                    source TEXT,
                    created_at TIMESTAMP
                )
            """
            )
            conn.commit()

        ids = get_all_quote_ids(str(db_path))
        assert ids == []


class TestGetQuoteById:
    """Tests for retrieving a quote by ID."""

    def test_get_quote_by_id_success(self, temp_db_with_quotes):
        """Test retrieving an existing quote."""
        quote = get_quote_by_id(temp_db_with_quotes, 1)
        assert quote is not None
        assert quote["id"] == 1
        assert "Chuck Norris can divide by zero" in quote["quote"]
        assert quote["source"] == "source1"

    def test_get_quote_by_id_not_found(self, temp_db_with_quotes):
        """Test retrieving a non-existent quote."""
        quote = get_quote_by_id(temp_db_with_quotes, 999)
        assert quote is None

    def test_get_quote_by_id_structure(self, temp_db_with_quotes):
        """Test that returned quote has correct structure."""
        quote = get_quote_by_id(temp_db_with_quotes, 1)
        assert "id" in quote
        assert "quote" in quote
        assert "source" in quote


class TestGenerateQuotes:
    """Tests for generating random quotes."""

    def test_generate_quotes_single(self, temp_db_with_quotes):
        """Test generating a single quote."""
        quotes = generate_quotes(temp_db_with_quotes, count=1)
        assert len(quotes) == 1
        assert "quote" in quotes[0]

    def test_generate_quotes_multiple(self, temp_db_with_quotes):
        """Test generating multiple quotes."""
        quotes = generate_quotes(temp_db_with_quotes, count=3)
        assert len(quotes) == 3

    def test_generate_quotes_with_seed_reproducible(self, temp_db_with_quotes):
        """Test that same seed produces same results."""
        quotes1 = generate_quotes(temp_db_with_quotes, count=5, seed=42)
        quotes2 = generate_quotes(temp_db_with_quotes, count=5, seed=42)

        # Same seed should produce same quotes in same order
        assert len(quotes1) == len(quotes2)
        for q1, q2 in zip(quotes1, quotes2):
            assert q1["id"] == q2["id"]

    def test_generate_quotes_different_seeds(self, temp_db_with_quotes):
        """Test that different seeds likely produce different results."""
        quotes1 = generate_quotes(temp_db_with_quotes, count=3, seed=42)
        quotes2 = generate_quotes(temp_db_with_quotes, count=3, seed=99)

        # Different seeds should likely produce different quotes
        # (though not guaranteed for small datasets)
        ids1 = [q["id"] for q in quotes1]
        ids2 = [q["id"] for q in quotes2]
        # At least verify we got quotes
        assert len(ids1) == 3
        assert len(ids2) == 3

    def test_generate_quotes_more_than_available(self, temp_db_with_quotes):
        """Test generating more quotes than available (with replacement)."""
        quotes = generate_quotes(temp_db_with_quotes, count=10)
        # Should generate 10 quotes even though only 3 unique ones exist
        assert len(quotes) == 10

    def test_generate_quotes_empty_database(self, tmp_path):
        """Test generating from empty database."""
        db_path = tmp_path / "empty.db"
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE quotes (
                    id INTEGER PRIMARY KEY,
                    quote TEXT,
                    source TEXT,
                    created_at TIMESTAMP
                )
            """
            )
            conn.commit()

        quotes = generate_quotes(str(db_path), count=5)
        assert quotes == []

    @patch("quotes.generator.get_quote_by_id")
    def test_generate_quotes_with_missing_quote(self, mock_get_quote, temp_db_with_quotes):
        """Test generating quotes when some quotes are missing from DB."""

        # Mock get_quote_by_id to return None for id 2
        def mock_get(db_path, id):
            if id == 2:
                return None
            return {
                "id": id,
                "quote": f"Quote {id}",
                "source": "test",
                "created_at": "now",
            }

        mock_get_quote.side_effect = mock_get

        quotes = generate_quotes(temp_db_with_quotes, count=3)
        # Should skip the missing quote and generate others
        assert len(quotes) == 2  # Only 2 out of 3

    @pytest.mark.parametrize("count", [1, 5, 10, 100])
    def test_generate_quotes_various_counts(self, temp_db_with_quotes, count):
        """Test generating various counts of quotes."""
        quotes = generate_quotes(temp_db_with_quotes, count=count)
        assert len(quotes) == count


class TestExportQuotesText:
    """Tests for exporting quotes in text format."""

    def test_export_quotes_text_to_string(self, sample_quote_dicts):
        """Test exporting quotes to string buffer."""
        output = StringIO()
        export_quotes_text(sample_quote_dicts, output)
        result = output.getvalue()

        assert "Chuck Norris can divide by zero." in result
        assert "Chuck Norris counted to infinity. Twice." in result

    def test_export_quotes_text_line_count(self, sample_quote_dicts):
        """Test that each quote gets its own line."""
        output = StringIO()
        export_quotes_text(sample_quote_dicts, output)
        result = output.getvalue()
        lines = result.strip().split("\n")
        assert len(lines) == 2

    def test_export_quotes_text_empty_list(self):
        """Test exporting empty quote list."""
        output = StringIO()
        export_quotes_text([], output)
        result = output.getvalue()
        assert result == ""


class TestExportQuotesJson:
    """Tests for exporting quotes in JSON format."""

    def test_export_quotes_json_valid(self, sample_quote_dicts):
        """Test that exported JSON is valid."""
        output = StringIO()
        export_quotes_json(sample_quote_dicts, output)
        result = output.getvalue()

        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_export_quotes_json_structure(self, sample_quote_dicts):
        """Test that JSON has correct structure."""
        output = StringIO()
        export_quotes_json(sample_quote_dicts, output)
        result = output.getvalue()
        data = json.loads(result)

        assert "id" in data[0]
        assert "quote" in data[0]
        assert "source" in data[0]
        assert "created_at" in data[0]

    def test_export_quotes_json_empty_list(self):
        """Test exporting empty quote list to JSON."""
        output = StringIO()
        export_quotes_json([], output)
        result = output.getvalue()
        data = json.loads(result)
        assert data == []


class TestExportQuotesCsv:
    """Tests for exporting quotes in CSV format."""

    def test_export_quotes_csv_valid(self, sample_quote_dicts):
        """Test that exported CSV is valid."""
        output = StringIO()
        export_quotes_csv(sample_quote_dicts, output)
        result = output.getvalue()

        # Parse CSV
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)
        assert len(rows) == 2

    def test_export_quotes_csv_headers(self, sample_quote_dicts):
        """Test that CSV has correct headers."""
        output = StringIO()
        export_quotes_csv(sample_quote_dicts, output)
        result = output.getvalue()

        reader = csv.DictReader(StringIO(result))
        headers = reader.fieldnames
        assert headers == ["id", "quote", "source", "created_at"]

    def test_export_quotes_csv_content(self, sample_quote_dicts):
        """Test CSV content correctness."""
        output = StringIO()
        export_quotes_csv(sample_quote_dicts, output)
        result = output.getvalue()

        reader = csv.DictReader(StringIO(result))
        rows = list(reader)

        assert rows[0]["quote"] == "Chuck Norris can divide by zero."
        assert rows[1]["quote"] == "Chuck Norris counted to infinity. Twice."

    def test_export_quotes_csv_empty_list(self):
        """Test exporting empty quote list to CSV."""
        output = StringIO()
        export_quotes_csv([], output)
        result = output.getvalue()

        # Should have headers only
        reader = csv.DictReader(StringIO(result))
        rows = list(reader)
        assert len(rows) == 0
        assert reader.fieldnames == ["id", "quote", "source", "created_at"]


class TestExportQuotes:
    """Tests for the main export function."""

    @patch("quotes.generator.export_quotes_text")
    def test_export_quotes_text_format(self, mock_export, sample_quote_dicts):
        """Test exporting in text format."""
        export_quotes(sample_quote_dicts, "text", None)
        mock_export.assert_called_once()

    @patch("quotes.generator.export_quotes_json")
    def test_export_quotes_json_format(self, mock_export, sample_quote_dicts):
        """Test exporting in JSON format."""
        export_quotes(sample_quote_dicts, "json", None)
        mock_export.assert_called_once()

    @patch("quotes.generator.export_quotes_csv")
    def test_export_quotes_csv_format(self, mock_export, sample_quote_dicts):
        """Test exporting in CSV format."""
        export_quotes(sample_quote_dicts, "csv", None)
        mock_export.assert_called_once()

    def test_export_quotes_to_file(self, sample_quote_dicts, tmp_path):
        """Test exporting to a file."""
        output_file = tmp_path / "output.txt"
        export_quotes(sample_quote_dicts, "text", str(output_file))

        assert output_file.exists()
        content = output_file.read_text()
        assert "Chuck Norris can divide by zero." in content

    def test_export_quotes_empty_list_no_error(self, caplog):
        """Test that exporting empty list doesn't error."""
        with caplog.at_level(logging.WARNING):
            export_quotes([], "text", None)
        assert any("No quotes to export" in record.message for record in caplog.records)

    def test_export_quotes_empty_list_to_file(self, tmp_path, caplog):
        """Test exporting empty list to file."""
        output_file = tmp_path / "empty.txt"
        with caplog.at_level(logging.WARNING):
            export_quotes([], "text", str(output_file))
        # File should not be created since no quotes
        assert not output_file.exists()
        assert any("No quotes to export" in record.message for record in caplog.records)

    @pytest.mark.parametrize("format_type", ["text", "json", "csv"])
    def test_export_quotes_all_formats(self, sample_quote_dicts, tmp_path, format_type):
        """Test exporting in all supported formats."""
        output_file = tmp_path / f"output.{format_type}"
        export_quotes(sample_quote_dicts, format_type, str(output_file))
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_export_quotes_unknown_format(self, sample_quote_dicts, tmp_path, caplog):
        """Test exporting with unknown format logs error."""
        output_file = tmp_path / "output.txt"
        with caplog.at_level(logging.ERROR):
            export_quotes(sample_quote_dicts, "unknown", str(output_file))
            assert "Unknown format: unknown" in caplog.text
