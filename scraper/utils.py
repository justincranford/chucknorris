#!/usr/bin/env python3
"""Utility module for Chuck Norris Quote Scraper.

This module provides utility functions for logging, validation, and source management.
"""

import csv as _csv
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

# Constants
SOURCES_FILE = "scraper/sources.txt"
DEFAULT_OUTPUT_DB = "scraper/quotes.db"
DEFAULT_OUTPUT_CSV = "scraper/quotes.csv"


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the scraper.

    Args:
        verbose: If True, set logging level to DEBUG, otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_sources(sources_file: Optional[str] = None) -> List[str]:
    """Load sources from the sources.txt file.

    Args:
        sources_file: Path to the sources file (defaults to SOURCES_FILE if None).

    Returns:
        List of source URLs (excluding commented lines).
    """
    if sources_file is None:
        # Import at runtime to allow patching of scraper.scraper.SOURCES_FILE
        try:
            import scraper.scraper as scraper_module

            sources_file = getattr(scraper_module, "SOURCES_FILE", SOURCES_FILE)
        except (ImportError, AttributeError):
            sources_file = SOURCES_FILE

    sources: List[str] = []
    try:
        with open(sources_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    sources.append(line)
    except FileNotFoundError:
        logging.warning(f"Sources file {sources_file} not found, using empty list")
    return sources


def comment_out_source(url: str, reason: str, sources_file: Optional[str] = None) -> None:
    """Comment out a source URL in the sources.txt file.

    Args:
        url: The URL to comment out.
        reason: The reason for commenting out.
        sources_file: Path to the sources file (defaults to SOURCES_FILE if None).
    """
    if sources_file is None:
        # Import at runtime to allow patching of scraper.scraper.SOURCES_FILE
        try:
            import scraper.scraper as scraper_module

            sources_file = getattr(scraper_module, "SOURCES_FILE", SOURCES_FILE)
        except (ImportError, AttributeError):
            sources_file = SOURCES_FILE

    try:
        with open(sources_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(sources_file, "w", encoding="utf-8") as f:
            for line in lines:
                line_stripped = line.strip()
                if line_stripped == url:
                    f.write(f"# [{reason}] {url}\n")
                else:
                    f.write(line)
            f.flush()
    except Exception as e:
        logging.error(f"Failed to comment out source {url}: {e}")


def validate_sources(sources: List[str]) -> List[str]:
    """Validate and filter source URLs.

    Args:
        sources: List of source URLs.

    Returns:
        List of valid URLs.
    """
    valid_sources: List[str] = []

    for source in sources:
        try:
            result = urlparse(source)
            if all([result.scheme, result.netloc]):
                valid_sources.append(source)
            else:
                logging.warning(f"Invalid URL: {source}")
        except Exception as e:
            logging.warning(f"Error parsing URL {source}: {e}")

    return valid_sources


def get_scraped_sources(csv_path: str = DEFAULT_OUTPUT_CSV, db_path: str = DEFAULT_OUTPUT_DB) -> set[str]:
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
