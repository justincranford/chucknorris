# Quick Start Guide

## Get Started in 3 Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Scrape Chuck Norris Quotes
```bash
python download/scraper.py -v
```
This will download quotes from the Chuck Norris API and store them in `download/quotes.db`.

### 3. Generate Random Quotes
```bash
# Generate a single quote
python quotes/generator.py

# Generate 10 quotes
python quotes/generator.py --count 10

# Generate JSON output
python quotes/generator.py --count 5 --format json
```

## Running Tests
```bash
# Run all tests with coverage
pytest --cov=download --cov=quotes

# Run specific test file
pytest tests/test_scraper.py -v

# Run tests with coverage report
pytest --cov=download --cov=quotes --cov-report=html
```

## Development Workflow

### 1. Install pre-commit hooks
```bash
pre-commit install
```

### 2. Run code quality checks
```bash
# Format code with Black
black download quotes tests

# Sort imports
isort download quotes tests

# Run linter
flake8 download quotes

# Type checking
mypy download quotes
```

### 3. Run all pre-commit hooks
```bash
pre-commit run --all-files
```

## Example Outputs

### Text Format (default)
```
Chuck Norris can divide by zero.
Chuck Norris counted to infinity. Twice.
```

### JSON Format
```json
[
  {
    "id": 1,
    "quote": "Chuck Norris can divide by zero.",
    "source": "https://api.chucknorris.io/jokes/random",
    "created_at": "2025-11-14 12:00:00"
  }
]
```

### CSV Format
```csv
id,quote,source,created_at
1,"Chuck Norris can divide by zero.","https://api.chucknorris.io/jokes/random","2025-11-14 12:00:00"
```

## Advanced Usage

### Scraper Options
```bash
# Custom output location
python download/scraper.py --output ./data/quotes.db

# Scrape from custom sources
python download/scraper.py --sources https://example.com/api/quotes

# Enable verbose logging
python download/scraper.py -v
```

### Generator Options
```bash
# Generate with specific seed for reproducibility
python quotes/generator.py --count 100 --seed 42

# Save to file
python quotes/generator.py --count 1000 --output quotes.txt

# Use custom database
python quotes/generator.py --database ./data/quotes.db --count 10
```

## Need Help?

```bash
# Scraper help
python download/scraper.py --help

# Generator help
python quotes/generator.py --help
```

For full documentation, see [README.md](README.md).
