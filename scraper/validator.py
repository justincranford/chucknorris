#!/usr/bin/env python3
"""URL and source validation for Chuck Norris Quote Scraper."""

import logging
from pathlib import Path
from typing import List
from urllib.parse import urlparse

# Constants
SOURCES_FILE = "scraper/sources.txt"


def load_sources() -> List[str]:
    """Load sources from the sources.txt file.

    Returns:
        List of source URLs (excluding commented lines).
    """
    sources: List[str] = []
    try:
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    sources.append(line)
    except FileNotFoundError:
        logging.warning(f"Sources file {SOURCES_FILE} not found, using empty list")
    return sources


def comment_out_source(url: str, reason: str) -> None:
    """Comment out a source URL in the sources.txt file.

    Args:
        url: The URL to comment out.
        reason: The reason for commenting out.
    """
    try:
        with open(SOURCES_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(SOURCES_FILE, "w", encoding="utf-8") as f:
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
