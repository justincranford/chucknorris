# Migration Guide

This guide helps you migrate to the refactored modular structure of the Chuck Norris quotes scraper.

## Overview

The scraper has been refactored from a monolithic `scraper.py` file into focused modules for better maintainability and scalability.

## What Changed

### File Structure

**Before:**
```
scraper/
├── __init__.py
├── scraper.py (959 lines, all functionality)
└── sources.txt
```

**After:**
```
scraper/
├── __init__.py (re-exports for backward compatibility)
├── scraper.py (orchestration, 104 lines)
├── fetcher.py (HTTP operations, 32 lines)
├── parser.py (quote extraction, 155 lines)
├── loader.py (data persistence, 20 lines)
├── utils.py (utilities, 83 lines)
└── sources.txt
```

## Backward Compatibility

### ✅ No Changes Required

All existing imports continue to work without modification:

```python
# These imports still work exactly as before
from scraper.scraper import (
    fetch_url,
    extract_quotes,
    save_quotes_to_db,
    save_quotes_to_csv,
    create_database,
    scrape_source,
    scrape_all_sources,
    setup_logging,
    load_sources,
    validate_sources,
    comment_out_source,
    get_scraped_sources,
)
```

### Alternative: Import from New Modules

You can now also import directly from specific modules if you prefer:

```python
# New modular imports (optional)
from scraper.fetcher import fetch_url
from scraper.parser import extract_quotes, extract_quotes_from_json, extract_quotes_from_html
from scraper.loader import save_quotes_to_db, save_quotes_to_csv, create_database
from scraper.utils import setup_logging, load_sources, validate_sources
```

## What to Update (Optional)

While not required, you may want to update your code to use the new modular structure for better clarity:

### 1. Specific Module Imports

**Before:**
```python
from scraper.scraper import fetch_url, extract_quotes, save_quotes_to_db
```

**After (optional):**
```python
from scraper.fetcher import fetch_url
from scraper.parser import extract_quotes
from scraper.loader import save_quotes_to_db
```

**Benefits:**
- Clearer where functionality comes from
- Easier to mock in tests
- Better IDE autocomplete

### 2. Test Mocking Paths

If you have custom tests that mock scraper functions, you may want to update mock paths:

**Before:**
```python
@patch('scraper.scraper.requests.get')
@patch('scraper.scraper.BeautifulSoup')
```

**After (more precise):**
```python
@patch('scraper.fetcher.requests.get')
@patch('scraper.parser.BeautifulSoup')
```

**Note:** Both approaches still work due to re-exports, but the new paths are more precise.

## Module Responsibilities

### scraper.fetcher
- HTTP requests with retry logic
- Network error handling
- 404 detection and source commenting

**Functions:**
- `fetch_url(url, retries)` - Fetch content from URL

### scraper.parser
- JSON and HTML quote extraction
- Site-specific parsers (Parade, Thefactsite, etc.)
- Content type auto-detection

**Functions:**
- `extract_quotes(content, source, content_type)` - Main extraction router
- `extract_quotes_from_json(content, source)` - JSON parsing
- `extract_quotes_from_html(content, source)` - Generic HTML parsing
- `extract_quotes_from_parade(content, source)` - Parade.com specific
- `extract_quotes_from_thefactsite(content, source)` - Thefactsite.com specific
- `extract_quotes_from_chucknorrisfacts_fr(content, source)` - French site specific
- `extract_quotes_from_factinate(content, source)` - Factinate.com specific

### scraper.loader
- Database operations (SQLite)
- CSV export functionality
- Duplicate detection

**Functions:**
- `create_database(db_path)` - Initialize SQLite database
- `save_quotes_to_db(quotes, db_path)` - Save to database
- `save_quotes_to_csv(quotes, csv_path)` - Save to CSV

### scraper.utils
- Logging configuration
- URL validation
- Source file management
- Helper utilities

**Functions:**
- `setup_logging(verbose)` - Configure logging
- `load_sources(sources_file)` - Load sources from file
- `comment_out_source(url, reason, sources_file)` - Comment out failed source
- `validate_sources(sources)` - Validate URL list
- `get_scraped_sources(csv_path, db_path)` - Get previously scraped sources

### scraper.scraper
- Orchestration of scraping workflow
- CLI argument parsing
- Multi-threaded scraping coordination

**Functions:**
- `scrape_source(source_url, db_path, csv_path, formats)` - Scrape single source
- `scrape_all_sources(sources, db_path, csv_path, formats, max_workers)` - Scrape multiple sources
- `parse_arguments()` - CLI argument parsing
- `main()` - Entry point

## Configuration Changes

### Python Version

The project requires Python 3.14:

```toml
# pyproject.toml
requires-python = ">=3.14"
```

**Note:** If you're using Python 3.12, the code will still work but you may see warnings. Python 3.14 is the official target.

### Coverage Threshold

Coverage threshold has been set to 95%:

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = [
    "--cov-fail-under=95",
]
```

## Breaking Changes

### None

There are no breaking changes. All existing code continues to work without modification.

## Testing

### Running Tests

Tests continue to work without modification:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scraper --cov=quotes

# Run specific module tests
pytest tests/test_scraper.py
```

### Test Count

- Before: 180 tests
- After: 193 tests (added 13 new tests for coverage)
- All tests passing ✅

## Performance

The refactoring maintains identical performance characteristics:

- Threading: Still uses 4 workers by default (configurable)
- Network I/O: Same retry logic and timeouts
- Database: Same SQLite operations
- Parsing: Same BeautifulSoup and JSON parsing

## Example Migration

Here's a complete example showing the migration:

### Before Refactoring

```python
from scraper.scraper import (
    setup_logging,
    load_sources,
    validate_sources,
    scrape_all_sources,
)

# Setup
setup_logging(verbose=True)
sources = load_sources()
valid_sources = validate_sources(sources)

# Scrape
total = scrape_all_sources(
    valid_sources,
    db_path="quotes.db",
    csv_path="quotes.csv",
    formats=["sqlite", "csv"],
    max_workers=4
)

print(f"Scraped {total} quotes")
```

### After Refactoring

```python
# Option 1: Keep existing imports (no changes needed)
from scraper.scraper import (
    setup_logging,
    load_sources,
    validate_sources,
    scrape_all_sources,
)

# Setup
setup_logging(verbose=True)
sources = load_sources()
valid_sources = validate_sources(sources)

# Scrape
total = scrape_all_sources(
    valid_sources,
    db_path="quotes.db",
    csv_path="quotes.csv",
    formats=["sqlite", "csv"],
    max_workers=4
)

print(f"Scraped {total} quotes")

# Option 2: Use new modular imports (optional, clearer)
from scraper.utils import setup_logging, load_sources, validate_sources
from scraper.scraper import scrape_all_sources

# Setup
setup_logging(verbose=True)
sources = load_sources()
valid_sources = validate_sources(sources)

# Scrape
total = scrape_all_sources(
    valid_sources,
    db_path="quotes.db",
    csv_path="quotes.csv",
    formats=["sqlite", "csv"],
    max_workers=4
)

print(f"Scraped {total} quotes")
```

Both approaches work identically!

## Getting Help

If you encounter any issues during migration:

1. Check that all imports use `from scraper.scraper import ...` (the main module re-exports everything)
2. Ensure you're using Python 3.14 or compatible version
3. Run tests to verify everything works: `pytest`
4. Check the [REFACTORING_STEPS.md](REFACTORING_STEPS.md) document for detailed technical information

## Summary

✅ **No code changes required** - Existing code continues to work
✅ **Optional modular imports** - Use new structure for clarity if desired
✅ **All tests passing** - Verified backward compatibility
✅ **Better maintainability** - Clearer code organization
✅ **Same performance** - No performance impact

The refactoring is fully backward compatible. You can migrate at your own pace or not at all!
