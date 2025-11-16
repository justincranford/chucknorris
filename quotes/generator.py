#!/usr/bin/env python3
"""Chuck Norris Quote Generator.

This module provides functionality to generate random Chuck Norris quotes
from a SQLite database. It supports multiple output formats and reproducible
random generation with seeds.
"""

import argparse
import csv
import json
import logging
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TextIO

# Constants
DEFAULT_DATABASE = "scraper/quotes.db"
DEFAULT_COUNT = 1
MAX_COUNT = 10_000_000
DEFAULT_FORMAT = "text"
VALID_FORMATS = ["text", "json", "csv"]


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the generator.

    Args:
        verbose: If True, set logging level to DEBUG, otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def validate_database(db_path: str) -> bool:  # pragma: no cover
    """Validate that the database exists and has quotes.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        True if database is valid and has quotes, False otherwise.
    """
    if not Path(db_path).exists():
        logging.error(f"Database file not found: {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM quotes")
            count = cursor.fetchone()[0]
        finally:
            cursor.close()
            conn.close()

        if count == 0:
            logging.error("Database is empty. Please run the scraper first.")
            return False

        logging.info(f"Database contains {count} quotes")
        return True

    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return False


def get_all_quote_ids(db_path: str) -> List[int]:  # pragma: no cover
    """Retrieve all quote IDs from the database.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        List of quote IDs.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM quotes")
        ids = [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()
        conn.close()

    logging.debug(f"Retrieved {len(ids)} quote IDs")
    return ids


def get_quote_by_id(db_path: str, quote_id: int) -> Optional[Dict[str, Any]]:  # pragma: no cover
    """Retrieve a quote by its ID.

    Args:
        db_path: Path to the SQLite database file.
        quote_id: The ID of the quote to retrieve.

    Returns:
        Dictionary containing quote data, or None if not found.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id, quote, source FROM quotes WHERE id = ?",
            (quote_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()

    if row:
        return {
            "id": row[0],
            "quote": row[1],
            "source": row[2],
        }
    return None


def generate_quotes(
    db_path: str,
    count: int,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Generate random quotes from the database.

    Args:
        db_path: Path to the SQLite database file.
        count: Number of quotes to generate.
        seed: Random seed for reproducibility (None for random).

    Returns:
        List of quote dictionaries.
    """
    # Set random seed if provided
    if seed is not None:
        random.seed(seed)
        logging.debug(f"Using random seed: {seed}")

    # Get all quote IDs
    all_ids = get_all_quote_ids(db_path)

    if not all_ids:
        logging.error("No quotes available in database")
        return []

    # Determine actual count (can't generate more than available)
    actual_count = min(count, len(all_ids))

    if actual_count < count:
        logging.warning(f"Requested {count} quotes, but only {len(all_ids)} available. " f"Generating {actual_count} quotes.")

    # Sample quote IDs
    if count > len(all_ids):
        # Allow duplicates if count exceeds available quotes
        selected_ids = random.choices(all_ids, k=count)
    else:
        # No duplicates if we have enough quotes
        selected_ids = random.sample(all_ids, count)

    # Retrieve quotes
    quotes = []
    for quote_id in selected_ids:
        quote = get_quote_by_id(db_path, quote_id)
        if quote:
            quotes.append(quote)

    logging.info(f"Generated {len(quotes)} quotes")
    return quotes


def export_quotes_text(quotes: List[Dict[str, Any]], output: Optional[TextIO] = None) -> None:
    """Export quotes in plain text format.

    Args:
        quotes: List of quote dictionaries.
        output: Output file handle (None for stdout).
    """
    file_handle = output if output else sys.stdout

    for quote in quotes:
        file_handle.write(f"{quote['quote']}\n")

    if output:
        logging.debug(f"Exported {len(quotes)} quotes in text format")


def export_quotes_json(quotes: List[Dict[str, Any]], output: Optional[TextIO] = None) -> None:
    """Export quotes in JSON format.

    Args:
        quotes: List of quote dictionaries.
        output: Output file handle (None for stdout).
    """
    file_handle = output if output else sys.stdout

    # Prepare data for JSON export
    json_data = [
        {
            "id": quote["id"],
            "quote": quote["quote"],
            "source": quote["source"],
        }
        for quote in quotes
    ]

    json.dump(json_data, file_handle, indent=2, ensure_ascii=False)
    file_handle.write("\n")

    if output:
        logging.debug(f"Exported {len(quotes)} quotes in JSON format")


def export_quotes_csv(quotes: List[Dict[str, Any]], output: Optional[TextIO] = None) -> None:
    """Export quotes in CSV format.

    Args:
        quotes: List of quote dictionaries.
        output: Output file handle (None for stdout).
    """
    file_handle = output if output else sys.stdout

    fieldnames = ["id", "quote", "source"]
    writer = csv.DictWriter(file_handle, fieldnames=fieldnames)

    writer.writeheader()
    for quote in quotes:
        writer.writerow(
            {
                "id": quote["id"],
                "quote": quote["quote"],
                "source": quote["source"],
            }
        )

    if output:
        logging.debug(f"Exported {len(quotes)} quotes in CSV format")


def export_quotes(
    quotes: List[Dict[str, Any]],
    format_type: str,
    output_path: Optional[str] = None,
) -> None:
    """Export quotes in the specified format.

    Args:
        quotes: List of quote dictionaries.
        format_type: Output format ('text', 'json', or 'csv').
        output_path: Output file path (None for stdout).
    """
    if not quotes:
        logging.warning("No quotes to export")
        return

    # Determine output destination
    if output_path:
        output_file = open(output_path, "w", encoding="utf-8")
    else:
        output_file = None

    try:
        if format_type == "text":
            export_quotes_text(quotes, output_file)
        elif format_type == "json":
            export_quotes_json(quotes, output_file)
        elif format_type == "csv":
            export_quotes_csv(quotes, output_file)
        else:
            logging.error(f"Unknown format: {format_type}")

        if output_path:
            logging.info(f"Exported quotes to {output_path}")

    finally:
        if output_file:
            output_file.close()


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Generate random Chuck Norris quotes from the database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a single random quote
  python generator.py

  # Generate 10 random quotes
  python generator.py --count 10

  # Generate quotes with a specific seed for reproducibility
  python generator.py --count 5 --seed 42

  # Output to a file in JSON format
  python generator.py --count 100 --format json --output quotes.json

  # Generate CSV format
  python generator.py --count 50 --format csv --output quotes.csv

  # Use a custom database
  python generator.py --database ./my_quotes.db --count 5
        """,
    )

    parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=DEFAULT_COUNT,
        help=(f"Number of quotes to generate (default: {DEFAULT_COUNT}, max: {MAX_COUNT:,})"),  # noqa: E501
    )

    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        help="Random seed for reproducible output (default: None for truly random)",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (default: stdout)",
    )

    parser.add_argument(
        "-f",
        "--format",
        default=DEFAULT_FORMAT,
        choices=VALID_FORMATS,
        help=f"Output format (default: {DEFAULT_FORMAT})",
    )

    parser.add_argument(
        "-d",
        "--database",
        default=DEFAULT_DATABASE,
        help=f"Path to the quotes database (default: {DEFAULT_DATABASE})",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """Validate parsed arguments.

    Args:
        args: Parsed arguments namespace.

    Returns:
        True if arguments are valid, False otherwise.
    """
    if args.count < 1:
        logging.error("Count must be at least 1")
        return False

    if args.count > MAX_COUNT:
        logging.error(f"Count cannot exceed {MAX_COUNT:,}")
        return False

    return True


def main() -> int:
    """Main entry point for the generator.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_arguments()
    setup_logging(args.verbose)

    # Validate arguments
    if not validate_arguments(args):
        return 1

    logging.info("Chuck Norris Quote Generator started")

    # Validate database
    if not validate_database(args.database):
        return 1

    # Generate quotes
    quotes = generate_quotes(args.database, args.count, args.seed)

    if not quotes:
        logging.error("Failed to generate quotes")
        return 1

    # Export quotes
    export_quotes(quotes, args.format, args.output)

    logging.info("Quote generation completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
