#!/usr/bin/env python3
"""Utility module for Chuck Norris Quote Scraper.

This module provides utility functions for logging, validation, and source management.
"""

import csv as _csv
import logging
import sqlite3
from pathlib import Path
from typing import List, Optional

from scraper.config import get_config
from scraper.validator import validate_sources as validator_validate_sources


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
        sources_file: Path to the sources file (defaults to config if None).

    Returns:
        List of source URLs (excluding commented lines).
    """
    if sources_file is None:
        # Try to get from scraper.scraper for test patching
        try:
            import scraper.scraper as scraper_module

            sources_file = getattr(scraper_module, "SOURCES_FILE", None)
        except (ImportError, AttributeError):  # pragma: no cover
            sources_file = None

        # Fall back to config
        if sources_file is None:
            config = get_config()
            sources_file = config.get("sources_file", "scraper/sources.txt")

    sources: List[str] = []
    try:
        with open(sources_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    sources.append(line)
    except FileNotFoundError:  # pragma: no cover
        logging.warning(f"Sources file {sources_file} not found, using empty list")
    return sources


def comment_out_source(url: str, reason: str, sources_file: Optional[str] = None) -> None:
    """Comment out a source URL in the sources.txt file.

    Args:
        url: The URL to comment out.
        reason: The reason for commenting out.
        sources_file: Path to the sources file (defaults to config if None).
    """
    if sources_file is None:
        # Try to get from scraper.scraper for test patching
        try:
            import scraper.scraper as scraper_module

            sources_file = getattr(scraper_module, "SOURCES_FILE", None)
        except (ImportError, AttributeError):  # pragma: no cover
            sources_file = None

        # Fall back to config
        if sources_file is None:
            config = get_config()
            sources_file = config.get("sources_file", "scraper/sources.txt")

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
    except Exception as e:  # pragma: no cover
        logging.error(f"Failed to comment out source {url}: {e}")


def validate_sources(sources: List[str]) -> List[str]:
    """Validate and filter source URLs.

    Args:
        sources: List of source URLs.

    Returns:
        List of valid URLs.
    """
    return validator_validate_sources(sources)


def get_scraped_sources(csv_path: Optional[str] = None, db_path: Optional[str] = None) -> set[str]:
    """Return a set of unique source URLs that have already been scraped.

    Args:
        csv_path: Path to the CSV file (defaults to config if None).
        db_path: Path to the SQLite database (defaults to config if None).

    Returns:
        A set of source URLs (strings).
    """
    config = get_config()
    if csv_path is None:
        csv_path = config.get("output_csv", "scraper/quotes.csv")
    if db_path is None:
        db_path = config.get("output_db", "scraper/quotes.db")

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
    except Exception:  # pragma: no cover
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
    except Exception:  # pragma: no cover
        logging.debug("Failed to read DB for scraped sources; continuing")

    return scraped
