# Chuck Norris Quotes Project

A Python-based project to scrape Chuck Norris quotes from various online databases and generate random quotes based on the scraped data.

## Features

- 🔍 **Quote Scraper**: ETL pipeline to scrape Chuck Norris quotes from multiple online sources
- 🎲 **Quote Generator**: Generate up to 10,000,000 unique random Chuck Norris quotes
- 💾 **Efficient Storage**: SQLite database optimized for quick access
- 🧪 **Fully Tested**: 95%+ code coverage with comprehensive unit tests
- 🎯 **Type-Safe**: Full type hints and mypy validation
- 🔧 **CLI Interface**: User-friendly command-line interface with extensive options

## Requirements

- Python 3.14 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd chucknorris
   ```

1. Create a virtual environment (recommended):

   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

1. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

## Quick Start

### 1. Scrape Chuck Norris Quotes

```bash
python scraper/scraper.py -v
```

This will download quotes from the Chuck Norris API and store them in `scraper/quotes.db`.

### 2. Generate Random Quotes

```bash
# Generate a single quote
python quotes/generator.py

# Generate 10 quotes
python quotes/generator.py --count 10

# Generate JSON output
python quotes/generator.py --count 5 --format json
```

### 3. Run Tests

```bash
# Run all tests with coverage
pytest --cov=scraper --cov=quotes

# Run specific test file
pytest tests/test_scraper.py -v

# Run tests with coverage report
pytest --cov=scraper --cov=quotes --cov-report=html
```

### Example Outputs

#### Text Format (default)

```text
Chuck Norris can divide by zero.
Chuck Norris counted to infinity. Twice.
```

#### JSON Format

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

#### CSV Format

```csv
id,quote,source,created_at
1,"Chuck Norris can divide by zero.","https://api.chucknorris.io/jokes/random","2025-11-14 12:00:00"
```

### Advanced Usage

#### Scraper Options

```bash
# Custom output location
python scraper/scraper.py --output ./data/quotes.db

# Scrape from custom sources
python scraper/scraper.py --sources https://example.com/api/quotes

# Enable verbose logging
python scraper/scraper.py -v
```

#### More Generator Options

```bash
# Generate with specific seed for reproducibility
python quotes/generator.py --count 100 --seed 42

# Save to file
python quotes/generator.py --count 1000 --output quotes.txt

# Use custom database
python quotes/generator.py --database ./data/quotes.db --count 10
```

### Need Help?

```bash
# Scraper help
python scraper/scraper.py --help

# Generator help
python quotes/generator.py --help
```

## Usage

### Quote Scraper

Scrape Chuck Norris quotes from online sources and store them in a database:

```bash
python scraper/scraper.py
```

#### Options

- `-s, --sources`: List of URLs or sources to scrape (space-separated)
- `-o, --output`: Output database file path (default: `scraper/quotes.db`)
- `-f, --format`: Output format (default: `sqlite`)
- `-v, --verbose`: Enable verbose logging
- `-h, --help`: Display help and usage examples

#### Examples

```bash
# Scrape from default sources
python scraper/scraper.py

# Specify custom output location
python scraper/scraper.py --output ./my_quotes.db

# Enable verbose logging
python scraper/scraper.py --verbose

# Scrape from specific sources
python scraper/scraper.py --sources https://api.chucknorris.io/jokes/random
```

### Quote Generator

Generate random Chuck Norris quotes from the scraped database:

```bash
python quotes/generator.py
```

#### Generator Options

- `-c, --count`: Number of quotes to generate (default: 1, max: 10,000,000)
- `-s, --seed`: Random seed for reproducible output (default: None for truly random)
- `-o, --output`: Output file path (default: stdout)
- `-f, --format`: Output format - `text`, `json`, or `csv` (default: `text`)
- `-d, --database`: Path to the quotes database (default: `scraper/quotes.db`)
- `-v, --verbose`: Enable verbose logging
- `-h, --help`: Display help and usage examples

#### Generator Examples

```bash
# Generate a single random quote
python quotes/generator.py

# Generate 10 random quotes
python quotes/generator.py --count 10

# Generate quotes with a specific seed for reproducibility
python quotes/generator.py --count 5 --seed 42

# Output to a file in JSON format
python quotes/generator.py --count 100 --format json --output quotes.json

# Generate CSV format
python quotes/generator.py --count 50 --format csv --output quotes.csv

# Use a custom database
python quotes/generator.py --database ./my_quotes.db --count 5
```

## Testing

Run the test suite:

```bash
pytest
```

Run tests with coverage report:

```bash
pytest --cov=scraper --cov=quotes --cov-report=html
```

View coverage report:

```bash
# The HTML report will be in htmlcov/index.html
```

## Development

### Code Quality Tools

This project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pre-commit**: Git hooks for automated checks

Run all checks manually:

```bash
pre-commit run --all-files
```

### Project Structure

```text
chucknorris/
├── .github/
│   ├── workflows/          # CI/CD pipelines
│   └── copilot-instructions.md
├── scraper/
│   ├── scraper.py          # Quote scraping script
│   ├── quotes.db           # Scraped quotes database
│   ├── quotes.csv          # Scraped quotes CSV
│   └── sources.txt         # List of sources to scrape
├── quotes/
│   └── generator.py        # Quote generation script
├── scripts/                # Utility scripts
├── tests/                  # Unit tests
│   ├── test_scraper.py
│   └── test_generator.py
├── .pre-commit-config.yaml
├── .gitignore
├── pyproject.toml          # Project configuration
├── requirements.txt        # Python dependencies
└── README.md
```

## API Documentation

### Scraper Module (`scraper/scraper.py`)

The scraper module provides functionality to extract, transform, and load Chuck Norris quotes from various online sources.

**Key Functions:**

- `scrape_quotes(sources, output_db)`: Main ETL pipeline
- `fetch_from_api(url)`: Fetch quotes from JSON APIs
- `parse_html(content)`: Parse quotes from HTML pages
- `save_to_database(quotes, db_path)`: Store quotes in SQLite database

### Generator Module (`quotes/generator.py`)

The generator module provides functionality to generate random Chuck Norris quotes from the database.

**Key Functions:**

- `generate_quotes(count, seed, database)`: Generate random quotes
- `export_quotes(quotes, format, output)`: Export quotes in various formats

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Chuck Norris for being awesome
- Various Chuck Norris quote databases and APIs
