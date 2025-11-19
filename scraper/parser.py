#!/usr/bin/env python3
"""Parsing module for Chuck Norris Quote Scraper.

This module handles extracting quotes from various content formats (JSON, HTML).
"""

import json
import logging
import re
from typing import Dict, List


def _get_beautifulsoup() -> type:
    """Get BeautifulSoup class, allowing for test patching from scraper.scraper."""
    try:
        import scraper.scraper as scraper_module

        return getattr(scraper_module, "BeautifulSoup")
    except (ImportError, AttributeError):
        from bs4 import BeautifulSoup

        return BeautifulSoup


def extract_quotes_from_json(content: str, source: str) -> List[Dict[str, str]]:
    """Extract quotes from JSON content.

    Args:
        content: JSON string content.
        source: Source URL for attribution.

    Returns:
        List of quote dictionaries with 'quote' and 'source' keys.
    """
    quotes: List[Dict[str, str]] = []
    try:
        data = json.loads(content)

        # Handle different JSON structures
        if isinstance(data, dict):
            # Single quote (e.g., from api.chucknorris.io/jokes/random)
            if "value" in data:
                quotes.append({"quote": data["value"], "source": source})
            elif "joke" in data:
                quotes.append({"quote": data["joke"], "source": source})
            elif "result" in data and isinstance(data["result"], list):
                # Search results - handle list of dicts or strings
                for item in data["result"]:  # type: ignore
                    if isinstance(item, dict):
                        if "value" in item:
                            quotes.append({"quote": item["value"], "source": source})  # type: ignore
                        elif "joke" in item:
                            quotes.append({"quote": item["joke"], "source": source})  # type: ignore
                    elif isinstance(item, str):
                        quotes.append({"quote": item, "source": source})  # type: ignore
        elif isinstance(data, list):
            # List of quotes
            for item in data:  # type: ignore
                if isinstance(item, dict):
                    if "value" in item:
                        quotes.append({"quote": item["value"], "source": source})  # type: ignore
                    elif "joke" in item:
                        quotes.append({"quote": item["joke"], "source": source})  # type: ignore
                elif isinstance(item, str):
                    quotes.append({"quote": item, "source": source})

        logging.debug(f"Extracted {len(quotes)} quotes from JSON")
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON: {e}")

    return quotes


def extract_quotes_from_html(content: str, source: str) -> List[Dict[str, str]]:
    """Extract quotes from HTML content.

    Args:
        content: HTML string content.
        source: Source URL for attribution.

    Returns:
        List of quote dictionaries with 'quote' and 'source' keys.
    """
    quotes: List[Dict[str, str]] = []
    try:
        BeautifulSoup = _get_beautifulsoup()
        soup = BeautifulSoup(content, "lxml")

        # Try common HTML patterns for quotes
        # Pattern 1: <blockquote> tags
        for blockquote in soup.find_all("blockquote"):
            quote_text = blockquote.get_text(strip=True)
            if quote_text:
                quotes.append({"quote": quote_text, "source": source})

        # Pattern 2: Elements with class containing 'quote'
        for elem in soup.select('[class*="quote"]'):
            quote_text = elem.get_text(strip=True)
            if quote_text and len(quote_text) > 10:  # Filter out short snippets
                quotes.append({"quote": quote_text, "source": source})

        # Pattern 3: <p> tags (if no other patterns found)
        if not quotes:
            for p in soup.find_all("p"):
                quote_text = p.get_text(strip=True)
                # Heuristic: Chuck Norris quotes often contain "Chuck Norris"
                if "chuck norris" in quote_text.lower() and len(quote_text) > 20:
                    quotes.append({"quote": quote_text, "source": source})

        logging.debug(f"Extracted {len(quotes)} quotes from HTML")
    except Exception as e:
        logging.error(f"Failed to parse HTML: {e}")

    return quotes


def extract_quotes_from_parade(content: str, source: str) -> List[Dict[str, str]]:
    """Extract quotes from Parade.com Chuck Norris jokes page.

    Args:
        content: HTML content from Parade.com.
        source: Source URL for attribution.

    Returns:
        List of quote dictionaries.
    """
    quotes: List[Dict[str, str]] = []
    try:
        BeautifulSoup = _get_beautifulsoup()
        soup = BeautifulSoup(content, "lxml")

        # Parade.com uses various containers for jokes
        # Try different selectors
        selectors = [
            "div.article-body p",  # Article paragraphs
            "p",  # All paragraphs
            "li",  # List items
            "[class*='joke']",  # Elements with joke in class
            "[class*='fact']",  # Elements with fact in class
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 20 and len(text) < 500 and "chuck norris" in text.lower():
                    quotes.append({"quote": text, "source": source})

        # Remove duplicates
        seen: set[str] = set()
        unique_quotes: List[Dict[str, str]] = []
        for quote in quotes:
            if quote["quote"] not in seen:
                unique_quotes.append(quote)
                seen.add(quote["quote"])

        logging.debug(f"Extracted {len(unique_quotes)} quotes from Parade.com")
        return unique_quotes

    except Exception as e:
        logging.error(f"Failed to parse Parade.com: {e}")
        return []


def extract_quotes_from_thefactsite(content: str, source: str) -> List[Dict[str, str]]:
    """Extract quotes from Thefactsite.com top 100 Chuck Norris facts.

    Args:
        content: HTML content from Thefactsite.com.
        source: Source URL for attribution.

    Returns:
        List of quote dictionaries.
    """
    quotes: List[Dict[str, str]] = []
    try:
        # Use regex to find list items
        li_pattern = re.compile(r"<li[^>]*>(.*?)</li>", re.IGNORECASE | re.DOTALL)
        matches = li_pattern.findall(content)

        for match in matches:
            text = re.sub(r"<[^>]+>", "", match).strip()  # Remove any nested tags
            text = re.sub(r"^\d+\.\s*", "", text)  # Remove leading numbering like "1. "
            if text and len(text) > 20 and len(text) < 500 and "chuck norris" in text.lower():
                quotes.append({"quote": text, "source": source})

        logging.debug(f"Extracted {len(quotes)} quotes from Thefactsite.com")
        return quotes

    except Exception as e:
        logging.error(f"Failed to parse Thefactsite.com: {e}")
        return []


def extract_quotes_from_chucknorrisfacts_fr(content: str, source: str) -> List[Dict[str, str]]:
    """Extract quotes from Chucknorrisfacts.fr.

    Args:
        content: HTML content from Chucknorrisfacts.fr.
        source: Source URL for attribution.

    Returns:
        List of quote dictionaries.
    """
    quotes: List[Dict[str, str]] = []
    try:
        BeautifulSoup = _get_beautifulsoup()
        soup = BeautifulSoup(content, "lxml")

        # French site structure
        selectors = [
            "div.fact",  # Fact divs
            "p",  # Paragraphs
            "li",  # List items
            "[class*='fact']",  # Fact containers
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                # Handle French numbering/removal
                text = re.sub(r"^\d+\.?\s*", "", text)
                if text and len(text) > 20 and len(text) < 500 and "chuck norris" in text.lower():
                    quotes.append({"quote": text, "source": source})

        logging.debug(f"Extracted {len(quotes)} quotes from Chucknorrisfacts.fr")
        return quotes

    except Exception as e:
        logging.error(f"Failed to parse Chucknorrisfacts.fr: {e}")
        return []


def extract_quotes_from_factinate(content: str, source: str) -> List[Dict[str, str]]:
    """Extract quotes from Factinate.com Chuck Norris jokes.

    Args:
        content: HTML content from Factinate.com.
        source: Source URL for attribution.

    Returns:
        List of quote dictionaries.
    """
    quotes: List[Dict[str, str]] = []
    try:
        BeautifulSoup = _get_beautifulsoup()
        soup = BeautifulSoup(content, "lxml")

        # Factinate uses various quote containers
        selectors = [
            "blockquote",  # Blockquotes
            "div.quote",  # Quote divs
            "p",  # Paragraphs
            "[class*='quote']",  # Quote elements
            "[class*='joke']",  # Joke elements
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 20 and len(text) < 500 and "chuck norris" in text.lower():
                    quotes.append({"quote": text, "source": source})

        logging.debug(f"Extracted {len(quotes)} quotes from Factinate.com")
        return quotes

    except Exception as e:
        logging.error(f"Failed to parse Factinate.com: {e}")
        return []


def extract_quotes(content: str, source: str, content_type: str = "auto") -> List[Dict[str, str]]:
    """Extract quotes from content based on type detection and source routing.

    Args:
        content: The content to parse.
        source: Source URL for attribution.
        content_type: Type of content ('json', 'html', or 'auto' for detection).

    Returns:
        List of quote dictionaries with 'quote' and 'source' keys.
    """
    if content_type == "auto":
        # Try JSON first
        try:
            json.loads(content)
            content_type = "json"
        except json.JSONDecodeError:
            content_type = "html"

    if content_type == "json":
        return extract_quotes_from_json(content, source)
    else:
        # Route HTML content to site-specific extractors
        if "parade.com" in source:
            return extract_quotes_from_parade(content, source)
        elif "thefactsite.com" in source:
            return extract_quotes_from_thefactsite(content, source)
        elif "chucknorrisfacts.fr" in source:
            return extract_quotes_from_chucknorrisfacts_fr(content, source)
        elif "factinate.com" in source:
            return extract_quotes_from_factinate(content, source)
        else:
            # Fallback to generic HTML extraction
            return extract_quotes_from_html(content, source)
