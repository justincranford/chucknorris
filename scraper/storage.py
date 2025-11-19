#!/usr/bin/env python3
"""Database and file storage operations for Chuck Norris Quote Scraper."""

import csv as _csv
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List


def create_database(db_path: str) -> None:  # pragma: no cover
    """Create the SQLite database and quotes table.

    Args:
        db_path: Path to the SQLite database file.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'")
        table_exists = cursor.fetchone()

        if not table_exists:
            # Create new table
            cursor.execute(
                """
                CREATE TABLE quotes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quote TEXT NOT NULL UNIQUE,
                    source TEXT
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_quote ON quotes(quote)
            """
            )

        conn.commit()
    finally:
        cursor.close()
        conn.close()
    logging.info(f"Database created/verified at {db_path}")


def save_quotes_to_db(quotes: List[Dict[str, str]], db_path: str) -> int:  # pragma: no cover
    """Save quotes to the SQLite database.

    Args:
        quotes: List of quote dictionaries.
        db_path: Path to the SQLite database file.

    Returns:
        Number of quotes successfully saved.
    """
    if not quotes:
        logging.warning("No quotes to save")
        return 0

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        saved_count = 0
        duplicate_count = 0

        for quote_data in quotes:
            try:
                cursor.execute(
                    "INSERT INTO quotes (quote, source) VALUES (?, ?)",
                    (quote_data["quote"], quote_data["source"]),
                )
                saved_count += 1
            except sqlite3.IntegrityError:
                # Duplicate quote
                duplicate_count += 1
                logging.debug(f"Skipping duplicate quote: {quote_data['quote'][:50]}...")

        conn.commit()
    finally:
        cursor.close()
        conn.close()

    logging.info(f"Saved {saved_count} new quotes, skipped {duplicate_count} duplicates")
    return saved_count


def save_quotes_to_csv(quotes: List[Dict[str, str]], csv_path: str) -> int:
    """Save quotes to a CSV file.

    Args:
        quotes: List of quote dictionaries.
        csv_path: Path to the CSV file.

    Returns:
        Number of quotes successfully saved.
    """
    if not quotes:
        logging.warning("No quotes to save")
        return 0

    # Check if file exists to determine if we need headers
    file_exists = Path(csv_path).exists()

    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["source", "quote"]
        writer = _csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header only if file is new
        if not file_exists:
            writer.writeheader()

        saved_count = 0
        for quote_data in quotes:
            writer.writerow({"source": quote_data["source"], "quote": quote_data["quote"]})
            saved_count += 1

    logging.info(f"Saved {saved_count} quotes to CSV file: {csv_path}")
    return saved_count


def get_scraped_sources(csv_path: str, db_path: str) -> set[str]:
    """Return a set of unique source URLs that have already been scraped and
    saved in the CSV file and/or SQLite database.

    Args:
        csv_path: Path to the CSV file where quotes were saved.
        db_path: Path to the SQLite database file where quotes were saved.

    Returns:
        A set of source URLs (strings).
    """
    scraped: set[str] = set()

    # Read CSV file if it exists
    try:
        if Path(csv_path).exists():
            with open(csv_path, newline="", encoding="utf-8") as csvfile:
                reader = _csv.DictReader(csvfile)
                for row in reader:
                    src = row.get("source")
                    if src:
                        scraped.add(src)
    except Exception:
        logging.debug("Failed to read CSV for scraped sources; continuing")

    # Read SQLite DB if it exists
    try:
        if Path(db_path).exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT DISTINCT source FROM quotes")
                for (src,) in cursor.fetchall():
                    if src:
                        scraped.add(src)
            finally:
                cursor.close()
                conn.close()
    except Exception:
        logging.debug("Failed to read DB for scraped sources; continuing")

    return scraped
