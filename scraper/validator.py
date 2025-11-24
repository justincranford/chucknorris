#!/usr/bin/env python3
"""URL validation module for Chuck Norris Quote Scraper.

This module provides URL validation and verification functionality.
"""

import logging
from typing import List
from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """Check if a URL is valid and well-formed.

    Args:
        url: The URL to validate.

    Returns:
        True if URL is valid, False otherwise.
    """
    try:
        result = urlparse(url)
        # Check for scheme and netloc (domain)
        return bool(result.scheme and result.netloc)
    except Exception as e:  # pragma: no cover
        logging.debug(f"Error parsing URL {url}: {e}")
        return False


def validate_sources(sources: List[str]) -> List[str]:
    """Validate and filter source URLs.

    Args:
        sources: List of source URLs.

    Returns:
        List of valid URLs.
    """
    valid_sources: List[str] = []

    for source in sources:
        if is_valid_url(source):
            valid_sources.append(source)
        else:
            logging.warning(f"Invalid URL: {source}")

    return valid_sources


def validate_http_url(url: str) -> bool:
    """Check if a URL uses HTTP or HTTPS scheme.

    Args:
        url: The URL to validate.

    Returns:
        True if URL uses http or https, False otherwise.
    """
    try:
        result = urlparse(url)
        return result.scheme in ('http', 'https')
    except Exception:  # pragma: no cover
        return False


def normalize_url(url: str) -> str:
    """Normalize a URL by removing trailing slashes and fragments.

    Args:
        url: The URL to normalize.

    Returns:
        Normalized URL.
    """
    try:
        result = urlparse(url)
        # If no scheme or netloc, return as-is (malformed)
        if not result.scheme or not result.netloc:
            return url
        # Reconstruct without fragment and with normalized path
        path = result.path.rstrip('/') if result.path != '/' else result.path
        normalized = f"{result.scheme}://{result.netloc}{path}"
        if result.query:
            normalized += f"?{result.query}"
        return normalized
    except Exception:  # pragma: no cover
        return url


def is_chuck_norris_source(url: str, content: str = "") -> bool:
    """Check if a URL/content is likely a Chuck Norris quote source.

    Args:
        url: The URL to check.
        content: Optional content to check for Chuck Norris mentions.

    Returns:
        True if likely a Chuck Norris source, False otherwise.
    """
    url_lower = url.lower()
    
    # Check URL for Chuck Norris indicators
    cn_indicators = ['chucknorris', 'chuck-norris', 'chuck_norris', 'cn-facts', 'norris']
    if any(indicator in url_lower for indicator in cn_indicators):
        return True
    
    # Check content if provided
    if content and 'chuck norris' in content.lower():
        return True
    
    return False
