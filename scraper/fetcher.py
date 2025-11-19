#!/usr/bin/env python3
"""HTTP fetching module for Chuck Norris Quote Scraper.

This module handles fetching content from URLs with retry logic and error handling.
"""

import logging
import time
from typing import Optional

import requests

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


def fetch_url(url: str, retries: int = MAX_RETRIES) -> Optional[str]:
    """Fetch content from a URL with retry logic.

    Args:
        url: The URL to fetch.
        retries: Number of retry attempts on failure.

    Returns:
        The response text if successful, None otherwise.
    """
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(retries):
        try:
            logging.debug(f"Fetching {url} (attempt {attempt + 1}/{retries})")
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            if "404" in str(e):
                # Import here to avoid circular dependency and allow patching
                from scraper.scraper import comment_out_source

                comment_out_source(url, "HTTP 404")
            logging.warning(f"Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts")
                return None
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts")
                return None

    return None
