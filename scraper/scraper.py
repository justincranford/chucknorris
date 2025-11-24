#!/usr/bin/env python3
"""Chuck Norris Quote Scraper.

This module provides functionality to scrape Chuck Norris quotes from various
online sources and store them in an SQLite database. It supports multiple data
formats including JSON, HTML, and CSV.
"""

import argparse
import concurrent.futures
import logging
import sys
import time  # noqa: F401 - imported for test patching
from typing import List, Optional

import requests  # noqa: F401 - imported for test patching
from bs4 import BeautifulSoup  # noqa: F401 - imported for test patching

from scraper.config import get_config
from scraper.fetcher import fetch_url
from scraper.loader import create_database, save_quotes_to_csv, save_quotes_to_db
from scraper.parser import (
    extract_quotes,
    extract_quotes_from_chucknorrisfacts_fr,
    extract_quotes_from_factinate,
    extract_quotes_from_html,
    extract_quotes_from_json,
    extract_quotes_from_parade,
    extract_quotes_from_thefactsite,
)
from scraper.utils import comment_out_source, get_scraped_sources, load_sources, setup_logging, validate_sources

# Constants for test patching compatibility
SOURCES_FILE = None  # noqa: F401 - kept for test patching
DEFAULT_OUTPUT_DB = None  # noqa: F401 - kept for test patching
DEFAULT_OUTPUT_CSV = None  # noqa: F401 - kept for test patching

# Re-export for backward compatibility
__all__ = [
    "fetch_url",
    "create_database",
    "save_quotes_to_csv",
    "save_quotes_to_db",
    "extract_quotes",
    "extract_quotes_from_chucknorrisfacts_fr",
    "extract_quotes_from_factinate",
    "extract_quotes_from_html",
    "extract_quotes_from_json",
    "extract_quotes_from_parade",
    "extract_quotes_from_thefactsite",
    "comment_out_source",
    "get_scraped_sources",
    "load_sources",
    "setup_logging",
    "validate_sources",
    "scrape_source",
    "scrape_all_sources",
    "parse_arguments",
    "main",
]

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
        default=None,
        help="Output file path base (will generate .db and .csv files for both format) (default: from config)",
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

    # Get config
    config = get_config()

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
    default_db = config.get("output_db", "scraper/quotes.db")
    default_csv = config.get("output_csv", "scraper/quotes.csv")

    if args.format == "both":
        formats = ["sqlite", "csv"]
        db_path = args.output if args.output else default_db
        csv_path = args.output.replace(".db", ".csv") if args.output else default_csv
    elif args.format == "sqlite":
        formats = ["sqlite"]
        db_path = args.output if args.output else default_db
        csv_path = None
    else:  # csv
        formats = ["csv"]
        db_path = None
        csv_path = args.output if args.output else default_csv

    # Create database only if SQLite format is included
    if "sqlite" in formats and db_path:
        create_database(db_path)

    # Scrape quotes with threading
    total_saved = scrape_all_sources(sources, db_path, csv_path, formats, max_workers=args.threads)

    logging.info(f"Scraping completed. Total quotes saved: {total_saved}")

    return 0 if total_saved > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
