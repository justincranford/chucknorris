#!/usr/bin/env python3
"""HTTP fetching module for Chuck Norris Quote Scraper.

This module handles fetching content from URLs with retry logic and error handling.
"""

import logging
import time
from typing import Optional

import requests

from scraper.config import get_config


def fetch_url(url: str, retries: Optional[int] = None) -> Optional[str]:
    """Fetch content from a URL with retry logic.

    Args:
        url: The URL to fetch.
        retries: Number of retry attempts on failure (uses config if None).

    Returns:
        The response text if successful, None otherwise.
    """
    config = get_config()
    if retries is None:
        retries = config.get("max_retries", 3)
    
    retry_delay = config.get("retry_delay", 3)
    timeout = config.get("request_timeout", 10)
    user_agent = config.get("user_agent", "Mozilla/5.0")
    
    headers = {"User-Agent": user_agent}

    for attempt in range(retries):
        try:
            logging.debug(f"Fetching {url} (attempt {attempt + 1}/{retries})")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            if "404" in str(e):
                # Import here to avoid circular dependency and allow patching
                from scraper.scraper import comment_out_source

                comment_out_source(url, "HTTP 404")
            logging.warning(f"Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(retry_delay)
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts")
                return None
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(retry_delay)
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts")
                return None

    return None
