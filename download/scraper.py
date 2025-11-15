"""Chuck Norris Quote Scraper.

This module provides functionality to scrape Chuck Norris quotes from various
online sources and store them in an SQLite database. It supports multiple data
formats including JSON, HTML, and CSV.
"""

import argparse
import json
import logging
import re
import sqlite3
import sys
import time
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Constants
DEFAULT_OUTPUT_DB = "download/quotes.db"
DEFAULT_SOURCES = [
    "https://api.chucknorris.io/jokes/random",
    "https://api.chucknorris.io/jokes/search?query=all",
    "https://parade.com/970343/parade/chuck-norris-jokes/",
    "https://www.thefactsite.com/top-100-chuck-norris-facts/",
    "https://www.chucknorrisfacts.fr/en/top-100-chuck-norris-facts",  # noqa: E501
    "https://www.factinate.com/quote/chuck-norris-jokes/",  # noqa: E501
    # "https://api.icndb.com/jokes/random",  # NOTE: This is essentially the same as source 1 - commented out
    # "https://www.rd.com/list/chuck-norris-jokes/",  # DEAD LINK - marked for removal - commented out
]
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "ChuckNorrisQuoteScraper/1.0"


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


def create_database(db_path: str) -> None:
    """Create the SQLite database and quotes table.

    Args:
        db_path: Path to the SQLite database file.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote TEXT NOT NULL UNIQUE,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_quote ON quotes(quote)
        """
        )

        conn.commit()
    logging.info(f"Database created/verified at {db_path}")


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
        except requests.exceptions.RequestException as e:
            logging.warning(f"Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                logging.error(f"Failed to fetch {url} after {retries} attempts")
                return None

    return None


def extract_quotes_from_json(content: str, source: str) -> List[Dict[str, str]]:
    """Extract quotes from JSON content.

    Args:
        content: JSON string content.
        source: Source URL for attribution.

    Returns:
        List of quote dictionaries with 'quote' and 'source' keys.
    """
    quotes = []
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
                # Search results
                for item in data["result"]:
                    if "value" in item:
                        quotes.append({"quote": item["value"], "source": source})
        elif isinstance(data, list):
            # List of quotes
            for item in data:
                if isinstance(item, dict):
                    if "value" in item:
                        quotes.append({"quote": item["value"], "source": source})
                    elif "joke" in item:
                        quotes.append({"quote": item["joke"], "source": source})
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
    quotes = []
    try:
        soup = BeautifulSoup(content, "lxml")

        # Try common HTML patterns for quotes
        # Pattern 1: <blockquote> tags
        for blockquote in soup.find_all("blockquote"):
            quote_text = blockquote.get_text(strip=True)
            if quote_text:
                quotes.append({"quote": quote_text, "source": source})

        # Pattern 2: Elements with class containing 'quote'
        for elem in soup.find_all(class_=lambda x: x and "quote" in x.lower()):
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
    quotes = []
    try:
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
                if (
                    text
                    and len(text) > 20
                    and len(text) < 500
                    and "chuck norris" in text.lower()
                ):
                    quotes.append({"quote": text, "source": source})

        # Remove duplicates
        seen = set()
        unique_quotes = []
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
    quotes = []
    try:
        soup = BeautifulSoup(content, "lxml")

        # Thefactsite uses numbered lists for facts
        selectors = [
            "ol li",  # Ordered list items
            "ul li",  # Unordered list items
            "p",  # Paragraphs
            "[class*='fact']",  # Fact containers
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                # Remove numbering like "1. " or "1) "
                text = re.sub(r"^\d+\.?\s*", "", text)
                if (
                    text
                    and len(text) > 20
                    and len(text) < 500
                    and "chuck norris" in text.lower()
                ):
                    quotes.append({"quote": text, "source": source})

        logging.debug(f"Extracted {len(quotes)} quotes from Thefactsite.com")
        return quotes

    except Exception as e:
        logging.error(f"Failed to parse Thefactsite.com: {e}")
        return []


def extract_quotes_from_chucknorrisfacts_fr(
    content: str, source: str
) -> List[Dict[str, str]]:
    """Extract quotes from Chucknorrisfacts.fr.

    Args:
        content: HTML content from Chucknorrisfacts.fr.
        source: Source URL for attribution.

    Returns:
        List of quote dictionaries.
    """
    quotes = []
    try:
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
                if (
                    text
                    and len(text) > 20
                    and len(text) < 500
                    and "chuck norris" in text.lower()
                ):
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
    quotes = []
    try:
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
                if (
                    text
                    and len(text) > 20
                    and len(text) < 500
                    and "chuck norris" in text.lower()
                ):
                    quotes.append({"quote": text, "source": source})

        logging.debug(f"Extracted {len(quotes)} quotes from Factinate.com")
        return quotes

    except Exception as e:
        logging.error(f"Failed to parse Factinate.com: {e}")
        return []


def extract_quotes(
    content: str, source: str, content_type: str = "auto"
) -> List[Dict[str, str]]:
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


def save_quotes_to_db(quotes: List[Dict[str, str]], db_path: str) -> int:
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

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

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

    logging.info(
        f"Saved {saved_count} new quotes, skipped {duplicate_count} duplicates"
    )
    return saved_count


def scrape_source(source_url: str, db_path: str) -> int:
    """Scrape quotes from a single source.

    Args:
        source_url: URL of the source to scrape.
        db_path: Path to the SQLite database file.

    Returns:
        Number of quotes successfully scraped and saved.
    """
    logging.info(f"Scraping source: {source_url}")

    content = fetch_url(source_url)
    if not content:
        logging.error(f"Failed to fetch content from {source_url}")
        return 0

    quotes = extract_quotes(content, source_url)

    if not quotes:
        logging.warning(f"No quotes found at {source_url}")
        return 0

    saved = save_quotes_to_db(quotes, db_path)
    return saved


def scrape_all_sources(sources: List[str], db_path: str) -> int:
    """Scrape quotes from all provided sources.

    Args:
        sources: List of source URLs.
        db_path: Path to the SQLite database file.

    Returns:
        Total number of quotes successfully scraped and saved.
    """
    total_saved = 0

    for source in sources:
        try:
            saved = scrape_source(source, db_path)
            total_saved += saved
        except Exception as e:
            logging.error(f"Error scraping {source}: {e}")

    return total_saved


def validate_sources(sources: List[str]) -> List[str]:
    """Validate and filter source URLs.

    Args:
        sources: List of source URLs.

    Returns:
        List of valid URLs.
    """
    valid_sources = []

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


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Scrape Chuck Norris quotes from various online sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape from default sources
  python scraper.py

  # Specify custom output location
  python scraper.py --output ./my_quotes.db

  # Enable verbose logging
  python scraper.py --verbose

  # Scrape from specific sources
  python scraper.py --sources https://api.chucknorris.io/jokes/random
        """,
    )

    parser.add_argument(
        "-s",
        "--sources",
        nargs="+",
        help="List of URLs or sources to scrape (space-separated)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_DB,
        help=f"Output database file path (default: {DEFAULT_OUTPUT_DB})",
    )

    parser.add_argument(
        "-f",
        "--format",
        default="sqlite",
        choices=["sqlite"],
        help="Output format (default: sqlite)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point for the scraper.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_arguments()
    setup_logging(args.verbose)

    logging.info("Chuck Norris Quote Scraper started")

    # Use default sources if none provided
    sources = args.sources if args.sources else DEFAULT_SOURCES
    sources = validate_sources(sources)

    if not sources:
        logging.error("No valid sources provided")
        return 1

    # Create database
    create_database(args.output)

    # Scrape quotes
    total_saved = scrape_all_sources(sources, args.output)

    logging.info(f"Scraping completed. Total quotes saved: {total_saved}")

    return 0 if total_saved > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
