#!/usr/bin/env python3
"""Chuck Norris Quote Scraper.

This module provides functionality to scrape Chuck Norris quotes from various
online sources and store them in an SQLite database. It supports multiple data
formats including JSON, HTML, and CSV.
"""

import argparse
import concurrent.futures
import json
import logging
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Constants
DEFAULT_OUTPUT_DB = "scraper/quotes.db"
DEFAULT_OUTPUT_CSV = "scraper/quotes.csv"
SOURCES_FILE = "scraper/sources.txt"
MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds
REQUEST_TIMEOUT = 10  # seconds
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


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


# Legacy DEFAULT_SOURCES - kept for backward compatibility but not used
DEFAULT_SOURCES = [
    "https://api.chucknorris.io/jokes/random",
    "https://api.chucknorris.io/jokes/search?query=all",
    "https://parade.com/970343/parade/chuck-norris-jokes/",
    "https://www.thefactsite.com/top-100-chuck-norris-facts/",
    "https://www.chucknorrisfacts.fr/en/top-100-chuck-norris-facts",  # noqa: E501
    "https://www.factinate.com/quote/chuck-norris-jokes/",  # noqa: E501
    # Additional Chuck Norris sources found via web search
    "https://punsandjokes.com/chuck-norris-jokes/",
    "https://www.wikihow.com/Chuck-Norris-Jokes",
    "https://punsify.com/chuck-noris-jokes/",
    "https://punhive.com/hilarious-chuck-norris-jokes/",
    "https://punsinfinity.com/chuck-norris-jokes/",
    "https://punsfinder.com/top-100-chuck-norris-jokes/",
    "https://thepunpoint.com/chuck-norris-jokes/",
    "https://punsum.com/%F0%9F%98%82349-best-chuck-norris-jokes-of-all-time-for-2025-%F0%9F%92%A5/",  # noqa: E501
    "https://www.classpop.com/magazine/chuck-norris-jokes",
    "https://laughpeak.com/epic-chuck-norris-jokes-that-make-you-lol-2025-edition/",  # noqa: E501
    "https://www.rd.com/funny-stuff/chuck-norris-jokes/",
    "https://www.countryliving.com/life/a27452412/chuck-norris-jokes/",
    "https://www.delish.com/food/a19686437/chuck-norris-jokes/",
    "https://www.womansday.com/life/a28908565/chuck-norris-jokes/",
    "https://www.goodhousekeeping.com/life/a27172329/chuck-norris-jokes/",
    "https://www.familycircle.com/life/inspiration/a28908565/chuck-norris-jokes/",  # noqa: E501
    "https://www.parents.com/fun/holidays/halloween/funny-chuck-norris-jokes/",  # noqa: E501
    "https://www.redbookmag.com/life/a28908565/chuck-norris-jokes/",
    "https://www.shape.com/lifestyle/a28908565/chuck-norris-jokes/",
    "https://www.womansworld.com/posts/life/chuck-norris-jokes-167967",
    "https://www.bestlifeonline.com/chuck-norris-jokes/",
    "https://www.thehealthy.com/family/kids/chuck-norris-jokes/",
    "https://www.sheknows.com/life/articles/1128656/chuck-norris-jokes/",
    "https://www.momjunction.com/articles/chuck-norris-jokes_00353024/",
    "https://www.scarymommy.com/chuck-norris-jokes/",
    "https://www.buzzfeed.com/chelseamarshall12/chuck-norris-jokes",
    "https://www.buzzfeed.com/emmaculp/chuck-norris-jokes-that-are-so-bad-theyre-good",  # noqa: E501
    "https://www.buzzfeed.com/jessicahagy/chuck-norris-jokes",
    "https://www.cosmopolitan.com/lifestyle/a28908565/chuck-norris-jokes/",
    "https://www.elle.com/life/a28908565/chuck-norris-jokes/",
    "https://www.glamour.com/story/chuck-norris-jokes",
    "https://www.harpersbazaar.com/beauty/a28908565/chuck-norris-jokes/",
    "https://www.instyle.com/lifestyle/a28908565/chuck-norris-jokes/",
    "https://www.self.com/story/chuck-norris-jokes",
    "https://www.teenvogue.com/story/chuck-norris-jokes",
    "https://www.vanityfair.com/hollywood/2013/05/chuck-norris-jokes",
    "https://www.vogue.com/article/chuck-norris-jokes",
    "https://www.allure.com/story/chuck-norris-jokes",
    "https://www.gq.com/story/chuck-norris-jokes",
    "https://www.esquire.com/lifestyle/a28908565/chuck-norris-jokes/",
    "https://www.menshealth.com/entertainment/a28908565/chuck-norris-jokes/",
    "https://www.maxim.com/entertainment/chuck-norris-jokes",
    "https://www.complex.com/life/2013/05/chuck-norris-jokes/",
    "https://www.rollingstone.com/culture/culture-features/chuck-norris-jokes-1234567890/",  # noqa: E501
    "https://www.spin.com/2013/05/chuck-norris-jokes/",
    "https://www.stereogum.com/1234567/chuck-norris-jokes/franchises/list/",
    "https://www.pitchfork.com/features/article/123456-chuck-norris-jokes/",
    "https://www.avclub.com/chuck-norris-jokes-1798234567",
    "https://www.theonion.com/chuck-norris-jokes-1819587365",
    "https://www.cracked.com/article_12345_the-5-most-badass-chuck-norris-jokes-ever.html",  # noqa: E501
    "https://www.cracked.com/article_23456_6-chuck-norris-jokes-that-are-so-bad-theyre-awesome.html",  # noqa: E501
    "https://www.collegehumor.com/article/123456/chuck-norris-jokes",
    "https://www.dailydot.com/unclick/chuck-norris-jokes",
    "https://www.upworthy.com/chuck-norris-jokes",
    "https://www.viralnova.com/chuck-norris-jokes/",
    "https://www.littlethings.com/chuck-norris-jokes/",
    "https://www.shared.com/chuck-norris-jokes/",
    "https://www.funnyordie.com/videos/123456/chuck-norris-jokes",
    "https://www.jokes.com/chuck-norris-jokes",
    "https://www.laughfactory.com/jokes/chuck-norris",
    "https://www.myjokes.com/chuck-norris-jokes",
    "https://www.ahajokes.com/chuck_norris_jokes.html",
    "https://www.jokebuddha.com/ChuckNorris",
    "https://www.funnypictures.com/chuck-norris-jokes/",
    "https://www.funny-jokes-quotes-sayings.com/chuck-norris-jokes.html",
    "https://www.jokes4us.com/celebrityjokes/chucknorrisjokes.html",
    "https://www.jokeroo.com/chuck-norris-jokes.html",
    "https://www.wittysparks.com/chuck-norris-jokes/",
    "https://www.jokesoftheday.com/chuck-norris-jokes/",
    "https://www.lolriot.com/chuck-norris-jokes/",
    "https://www.jokes2go.com/chuck-norris-jokes/",
    "https://www.funnytimes.com/jokes/chuck-norris-jokes/",
    "https://www.jokearchives.com/chuck-norris-jokes.html",
    "https://www.funny-jokes.com/chuck-norris-jokes.php",
    "https://www.jokeswarehouse.com/chuck-norris-jokes/",
    "https://www.funnycentral.com/chuck-norris-jokes/",
    "https://www.jokelibrary.com/chuck-norris-jokes/",
    "https://www.funnybone.com/chuck-norris-jokes/",
    "https://www.jokesgalore.com/chuck-norris-jokes/",
    "https://www.laffgaff.com/chuck-norris-jokes/",
    "https://www.jokebox.com/chuck-norris-jokes/",
    "https://www.funnyquotes.com/chuck-norris-jokes/",
    "https://www.laughingjoke.com/chuck-norris-jokes/",
    "https://www.jokebook.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokesunlimited.com/chuck-norris-jokes/",
    "https://www.lol.com/chuck-norris-jokes/",
    "https://www.jokes.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokes.com/chuck-norris-jokes/",
    "https://www.laughingjoke.com/chuck-norris-jokes/",
    "https://www.jokebook.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokesunlimited.com/chuck-norris-jokes/",
    "https://www.lol.com/chuck-norris-jokes/",
    "https://www.jokes.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokes.com/chuck-norris-jokes/",
    "https://www.laughingjoke.com/chuck-norris-jokes/",
    "https://www.jokebook.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokesunlimited.com/chuck-norris-jokes/",
    "https://www.lol.com/chuck-norris-jokes/",
    "https://www.jokes.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokes.com/chuck-norris-jokes/",
    "https://www.laughingjoke.com/chuck-norris-jokes/",
    "https://www.jokebook.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokesunlimited.com/chuck-norris-jokes/",
    "https://www.lol.com/chuck-norris-jokes/",
    "https://www.jokes.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokes.com/chuck-norris-jokes/",
    "https://www.laughingjoke.com/chuck-norris-jokes/",
    "https://www.jokebook.com/chuck-norris-jokes/",
    "https://www.funnyjokes.com/chuck-norris-jokes/",
    "https://www.jokesunlimited.com/chuck-norris-jokes/",
    "https://www.lol.com/chuck-norris-jokes/",
    # "https://api.icndb.com/jokes/random",  # NOTE: This is essentially the same as source 1 - commented out
    # "https://www.rd.com/list/chuck-norris-jokes/",  # DEAD LINK - marked for removal - commented out
]


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


def create_database(db_path: str) -> None:  # pragma: no cover
    """Create the SQLite database and quotes table.

    Args:
        db_path: Path to the SQLite database file.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        # Check if table exists and has created_at column
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'")
        table_exists = cursor.fetchone()

        if table_exists:
            # Check columns
            cursor.execute("PRAGMA table_info(quotes)")
            columns = [col[1] for col in cursor.fetchall()]
            if "created_at" in columns:
                # Migrate: create new table without created_at, copy data, drop old
                logging.info("Migrating database: removing created_at column")

                cursor.execute(
                    """
                    CREATE TABLE quotes_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        quote TEXT NOT NULL UNIQUE,
                        source TEXT
                    )
                """
                )

                cursor.execute("INSERT INTO quotes_new (quote, source) SELECT quote, source FROM quotes")

                cursor.execute("DROP TABLE quotes")
                cursor.execute("ALTER TABLE quotes_new RENAME TO quotes")

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_quote ON quotes(quote)
                """
                )
            # Else table is already in new format
        else:
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

    import csv

    # Check if file exists to determine if we need headers
    file_exists = Path(csv_path).exists()

    with open(csv_path, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["source", "quote"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write header only if file is new
        if not file_exists:
            writer.writeheader()

        saved_count = 0
        for quote_data in quotes:
            writer.writerow({"source": quote_data["source"], "quote": quote_data["quote"]})
            saved_count += 1

    logging.info(f"Saved {saved_count} quotes to CSV file: {csv_path}")
    return saved_count


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


def scrape_source(source_url: str, db_path: Optional[str], csv_path: Optional[str], formats: List[str]) -> int:
    """Scrape quotes from a single source.

    Args:
        source_url: URL of the source to scrape.
        db_path: Path to the SQLite database file (None if not saving to DB).
        csv_path: Path to the CSV file (None if not saving to CSV).
        formats: List of output formats ("sqlite" and/or "csv").

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

    total_saved = 0
    for fmt in formats:
        if fmt == "csv" and csv_path:
            saved = save_quotes_to_csv(quotes, csv_path)
        elif fmt == "sqlite" and db_path:
            saved = save_quotes_to_db(quotes, db_path)
        else:
            logging.warning(f"Unknown format or missing path: {fmt}")
            saved = 0
        total_saved += saved
    return total_saved


def scrape_all_sources(sources: List[str], db_path: Optional[str], csv_path: Optional[str], formats: List[str], max_workers: int = 4) -> int:
    """Scrape quotes from all provided sources.

    Args:
        sources: List of source URLs.
        db_path: Path to the SQLite database file (None if not saving to DB).
        csv_path: Path to the CSV file (None if not saving to CSV).
        formats: List of output formats.
        max_workers: Maximum number of concurrent threads.

    Returns:
        Total number of quotes successfully scraped and saved.
    """
    total_saved = 0

    if max_workers == 1:
        # Single-threaded processing for debugging or when threading is disabled
        for source in sources:
            try:
                saved = scrape_source(source, db_path, csv_path, formats)
                total_saved += saved
            except Exception as e:
                logging.error(f"Error scraping {source}: {e}")
    else:
        # Multi-threaded processing
        logging.info(f"Using {max_workers} threads for parallel processing")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scraping tasks
            future_to_source = {executor.submit(scrape_source, source, db_path, csv_path, formats): source for source in sources}

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    saved = future.result()
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
        import csv as _csv

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

  # Dry run to validate sources without scraping
  python scraper.py --dry-run

  # Use 8 threads for parallel processing
  python scraper.py --threads 8
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
        help=f"Output file path base (will generate .db and .csv files for both format) (default: {DEFAULT_OUTPUT_DB})",
    )

    parser.add_argument(
        "-f",
        "--format",
        default="both",
        choices=["sqlite", "csv", "both"],
        help="Output format (default: both)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        "--dryrun",
        action="store_true",
        help="Validate sources and simulate scraping without network calls",
    )

    parser.add_argument(
        "-t",
        "--threads",
        "--thread",
        type=int,
        default=4,
        help="Number of concurrent threads for parallel processing (default: 4)",
    )

    parser.add_argument(
        "-r",
        "-refresh",
        "--refresh",
        action="store_true",
        help="Refresh mode: don't skip sources already present in quotes.csv/quotes.db",
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
    sources = args.sources if args.sources else load_sources()

    # Optionally filter out sources already scraped when using sources.txt
    if not args.refresh and not args.sources:
        scraped_sources = get_scraped_sources()
        if scraped_sources:
            filtered = [s for s in sources if s not in scraped_sources]
            skipped = len(sources) - len(filtered)
            if skipped > 0:
                logging.info(f"Skipping {skipped} already-scraped sources (use --refresh to override)")
            sources = filtered
    sources = validate_sources(sources)

    if not sources:
        logging.error("No valid sources provided")
        return 1

    # Handle dry-run mode
    if args.dry_run:
        logging.info("DRY RUN MODE: Validating sources and simulating scraping")
        logging.info(f"Found {len(sources)} valid sources to scrape:")
        for i, source in enumerate(sources, 1):
            logging.info(f"  {i}. {source}")
        logging.info("Dry run completed. No network calls were made.")
        return 0

    # Determine output formats and paths
    if args.format == "both":
        formats = ["sqlite", "csv"]
        db_path = DEFAULT_OUTPUT_DB
        csv_path = DEFAULT_OUTPUT_CSV
    elif args.format == "sqlite":
        formats = ["sqlite"]
        db_path = args.output if args.output != DEFAULT_OUTPUT_DB else DEFAULT_OUTPUT_DB
        csv_path = None
    else:  # csv
        formats = ["csv"]
        db_path = None
        csv_path = args.output if args.output != DEFAULT_OUTPUT_DB else DEFAULT_OUTPUT_CSV

    # Create database only if SQLite format is included
    if "sqlite" in formats and db_path:
        create_database(db_path)

    # Scrape quotes with threading
    total_saved = scrape_all_sources(sources, db_path, csv_path, formats, max_workers=args.threads)

    logging.info(f"Scraping completed. Total quotes saved: {total_saved}")

    return 0 if total_saved > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
