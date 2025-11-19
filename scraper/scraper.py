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
from typing import List, Optional

# Import from refactored modules
from scraper.fetcher import fetch_url
from scraper.parser import extract_quotes
from scraper.storage import create_database, get_scraped_sources, save_quotes_to_csv, save_quotes_to_db
from scraper.validator import load_sources, validate_sources

# Constants
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
        scraped_sources = get_scraped_sources(DEFAULT_OUTPUT_CSV, DEFAULT_OUTPUT_DB)
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
