# Custom Copilot Instructions for Chuck Norris Quotes Project

## Project Context
This is a Python project for scraping and generating Chuck Norris quotes. The project emphasizes code quality, testability, and best practices.

## Coding Standards

### Python Style
- Follow PEP 8 guidelines
- Use Black for code formatting (line length: 88)
- Sort imports with isort (black profile)
- Use type hints for all function signatures
- Write comprehensive docstrings (Google style)

### Testing Requirements
- Maintain minimum 95% code coverage
- Write parameterized tests for both happy and sad paths
- Use pytest fixtures for reusable test components
- Mock external dependencies (network calls, file I/O)
- Test edge cases and error conditions

### Code Organization
- Keep functions small and focused (single responsibility)
- Use descriptive variable and function names
- Avoid magic numbers - use named constants
- Implement proper error handling and logging
- Validate all user inputs

### CLI Development
- Use argparse for command-line interfaces
- Provide comprehensive help text with examples
- Support both short and long option forms
- Validate parameters before processing
- Return appropriate exit codes

## Architecture Patterns

### Scraper Module
- Separate concerns: fetch, parse, transform, load
- Handle multiple data formats (JSON, HTML, CSV)
- Implement retry logic for network failures
- Use appropriate error handling for malformed data
- Log progress and errors appropriately

### Generator Module
- Optimize database queries for performance
- Support multiple output formats
- Implement streaming for large outputs
- Provide reproducible randomness with seeds
- Handle edge cases (empty database, invalid counts)

## When Making Changes
1. Ensure all existing tests still pass
2. Add tests for new functionality
3. Update documentation if APIs change
4. Run pre-commit hooks before committing
5. Verify code coverage remains above 95%

## Preferred Libraries
- requests: HTTP requests
- beautifulsoup4: HTML parsing
- sqlite3: Database operations (standard library)
- argparse: CLI argument parsing (standard library)
- logging: Logging (standard library)
- pytest: Testing framework
- pytest-cov: Coverage reporting
- pytest-mock: Mocking utilities
