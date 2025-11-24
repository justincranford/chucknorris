"""Make scraper a package and re-export commonly used functions."""

# Re-export functions for backward compatibility
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
from scraper.validator import is_chuck_norris_source, is_valid_url, normalize_url, validate_http_url

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
    "is_valid_url",
    "is_chuck_norris_source",
    "normalize_url",
    "validate_http_url",
]
