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

## Preferred Libraries
- requests>=2.32.3: HTTP requests
- beautifulsoup4>=4.12.3: HTML parsing
- lxml>=5.3.0: XML/HTML parser
- sqlite3: Database operations (standard library)
- argparse: CLI argument parsing (standard library)
- logging: Logging (standard library)
- pytest>=8.3.3: Testing framework
- pytest-cov>=5.0.0: Coverage reporting
- pytest-mock>=3.14.0: Mocking utilities
- black>=24.10.0: Code formatting
- isort>=5.13.2: Import sorting
- mypy>=1.13.0: Type checking
- flake8>=7.1.0: Linting
- pre-commit>=4.0.1: Git hooks

### Testing Requirements
- Write parameterized tests for both happy and sad paths
- Maintain minimum 95% code coverage
- Use pytest fixtures for reusable test components
- Mock external dependencies (network calls, file I/O)
- Test edge cases and error conditions
- **Systematically identify and test missing branches**: Use coverage analysis to find uncovered conditional paths and exception handlers
- **Test exception handling thoroughly**: Ensure all try/catch blocks have corresponding test cases for both expected and unexpected exceptions
- **Validate boundary conditions**: Test edge cases like empty inputs, maximum values, and boundary conditions (e.g., string lengths, numeric limits)
- **Test CLI argument combinations**: Verify all format options, threading configurations, and parameter interactions

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

## Data Integrity Requirements
- THERE MUST NOT be any duplicates in sources.txt
- THERE MUST NOT be any duplicates in quotes.db
- THERE MUST NOT be any duplicates in quotes.csv
- Deduplication must be enforced at all levels (source loading, quote extraction, database insertion, CSV export)
- Sources must be validated for uniqueness before processing
- Quotes must be checked for uniqueness before storage

### Scraper CLI Parameters
- `-s, --sources`: List of URLs or sources to scrape (space-separated)
- `-o, --output`: Output file path base (default: scraper/quotes.db)
- `-f, --format`: Output format - sqlite, csv, or both (default: both)
- `-v, --verbose`: Enable verbose logging
- `-d, --dry-run, --dryrun`: Validate sources and simulate scraping without network calls
- `-t, --threads, --thread`: Number of concurrent threads for parallel processing (default: 4)

### Generator CLI Parameters
- `-c, --count`: Number of quotes to generate (default: 1, max: 10,000,000)
- `-s, --seed`: Random seed for reproducible output (default: None for truly random)
- `-o, --output`: Output file path (default: stdout)
- `-f, --format`: Output format - text, json, or csv (default: text)
- `-d, --database`: Path to the quotes database (default: scraper/quotes.db)
- `-v, --verbose`: Enable verbose logging

## When Making Changes
1. Ensure all existing tests still pass
2. Add tests for new functionality
3. Update documentation if APIs change
4. Run pre-commit hooks before committing
5. Verify code coverage remains above 95%

### Commit Message Standards
- Use conventional commit format: `type: Brief description`
- Provide detailed explanations in the body with bullet points

## Execution
- Scripts must have 700 permissions (rwx------) on Unix-like systems
- Scripts must be executed directly, without prefixing with `python`
- On Unix-like systems (Linux/macOS): Use `./script.py` after setting execute permissions
- On Windows: Use `py script.py` (Python launcher) or ensure .py files are associated with Python
- IMPORTANT: On Windows, do NOT use `python`, `python3`, or any other Python command variants; always use `py` to run Python scripts
- IMPORTANT: Do NOT prefix Terminal commands with `cd` as it is unnecessary

## Tool Usage
- ALWAYS use the built-in Copilot extension tools in VSCode/IntelliJ/Goland/PyCharm instead of their corresponding terminal commands; because they don't require manual authorization; and because they are faster and more efficient for the Copilot extension to use them
- IMPORTANT: Terminal commands executed via run_in_terminal are run from the workspace root directory; do NOT prefix commands with `cd` as it is unnecessary and will be simplified away by the tool
- create_directory: instead of mkdir (macOS/Linux/Windows), do not use in terminal
- create_file: instead of touch (macOS/Linux) or echo > (macOS/Linux/Windows) or New-Item (Windows PowerShell), do not use in terminal
- create_new_jupyter_notebook: instead of jupyter notebook (macOS/Linux/Windows), do not use in terminal
- create_new_workspace: instead of manual project setup commands, do not use in terminal
- edit_notebook_file: instead of jupyter nbconvert or manual editing, do not use in terminal
- fetch_webpage: instead of curl (macOS/Linux) or wget (macOS/Linux) or Invoke-WebRequest (Windows), do not use in terminal
- file_search: instead of find (macOS/Linux) or dir /s (Windows), do not use in terminal
- grep_search: instead of grep (macOS/Linux) or findstr (Windows), do not use in terminal
- get_changed_files: instead of git diff (macOS/Linux/Windows), do not use in terminal
- get_errors: instead of manual error checking, do not use in terminal
- copilot_getNotebookSummary: instead of jupyter nbconvert --to script, do not use in terminal
- get_project_setup_info: instead of manual setup, do not use in terminal
- get_search_view_results: instead of manual search, do not use in terminal
- get_vscode_api: instead of manual API lookup, do not use in terminal
- github_repo: instead of git clone (macOS/Linux/Windows), do not use in terminal
- install_extension: instead of code --install-extension (macOS/Linux/Windows), do not use in terminal
- list_code_usages: instead of grep -r or manual search, do not use in terminal
- list_dir: instead of ls (macOS/Linux) or dir (Windows), do not use in terminal
- open_simple_browser: instead of open (macOS) or xdg-open (Linux) or start (Windows), do not use in terminal
- read_file: instead of cat (macOS/Linux) or type (Windows), do not use in terminal
- replace_string_in_file: instead of sed (macOS/Linux) or manual editing, do not use in terminal
- run_notebook_cell: instead of jupyter run, do not use in terminal
- run_vscode_command: instead of manual command execution, do not use in terminal
- semantic_search: instead of manual search, do not use in terminal
- test_failure: instead of manual test running, do not use in terminal
- vscode_searchExtensions_internal: instead of manual extension search, do not use in terminal
- configure_python_environment: instead of python -m venv or conda create, do not use in terminal
- create_and_run_task: instead of manual task creation, do not use in terminal
- get_python_environment_details: instead of python --version or conda info, do not use in terminal
- get_python_executable_details: instead of which python or where python, do not use in terminal
- get_terminal_output: instead of manual terminal interaction, do not use in terminal
- install_python_packages: instead of pip install (macOS/Linux/Windows), do not use in terminal
- mcp_copilot_conta_act_container: instead of docker start/stop/restart/rm, do not use in terminal
- mcp_copilot_conta_act_image: instead of docker pull/rmi, do not use in terminal
- mcp_copilot_conta_inspect_container: instead of docker inspect, do not use in terminal
- mcp_copilot_conta_inspect_image: instead of docker inspect, do not use in terminal
- mcp_copilot_conta_list_containers: instead of docker ps, do not use in terminal
- mcp_copilot_conta_list_images: instead of docker images, do not use in terminal
- mcp_copilot_conta_list_networks: instead of docker network ls, do not use in terminal
- mcp_copilot_conta_list_volumes: instead of docker volume ls, do not use in terminal
- mcp_copilot_conta_logs_for_container: instead of docker logs, do not use in terminal
- mcp_copilot_conta_prune: instead of docker system prune, do not use in terminal
- mcp_copilot_conta_run_container: instead of docker run, do not use in terminal
- mcp_copilot_conta_tag_image: instead of docker tag, do not use in terminal

## Validation and Quality Assurance

### After Substantive Changes
- **Always run tests**: Execute the full test suite after any code modifications
- **Check coverage**: Ensure coverage remains above 95% using `pytest --cov --cov-fail-under=95`
- **Validate functionality**: Test both happy path and edge cases manually if needed
- **Review error handling**: Verify that exceptions are properly caught and logged
- **Check CLI interfaces**: Test command-line arguments and help text

### Coverage Analysis Approach
- Use `pytest --cov-report=term-missing` to identify uncovered lines
- Focus on conditional branches (`if/elif/else`) that may not be exercised
- Target exception handlers and error paths
- Prioritize functions with complex logic or multiple code paths
- Create targeted test cases for specific missing branches rather than broad tests

### Testing Patterns by Functionality Type

#### Exception Handling Tests
- Test both expected and unexpected exceptions
- Verify proper logging occurs in exception paths
- Ensure resources are cleaned up appropriately
- Test retry logic and failure thresholds

#### CLI Argument Tests
- Test all valid argument combinations
- Verify default values are applied correctly
- Test argument validation and error messages
- Check that mutually exclusive options work properly

#### Data Processing Tests
- Test boundary conditions (empty inputs, maximum sizes)
- Verify data transformation logic
- Test format detection and parsing
- Ensure deduplication works at all levels

#### Concurrent/Multi-threaded Tests
- Test both single-threaded and multi-threaded execution
- Verify exception handling in threaded contexts
- Ensure thread safety and proper synchronization
- Test thread pool management and cleanup
