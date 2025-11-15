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

## Execution
- Scripts must have 700 permissions (rwx------)
- Scripts must be executed directly, without prefixing with `python`

## Tool Usage
- ALWAYS use the built-in Copilot extension tools in VSCode/IntelliJ/Goland/PyCharm instead of their corresponding terminal commands; because they don't require manual authorization; and because they are faster and more efficient for the Copilot extension to use them
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
- mcp_pylance_mcp_s_pylanceDocuments: instead of manual documentation lookup, do not use in terminal
- mcp_pylance_mcp_s_pylanceFileSyntaxErrors: instead of python -m py_compile, do not use in terminal
- mcp_pylance_mcp_s_pylanceImports: instead of manual import analysis, do not use in terminal
- mcp_pylance_mcp_s_pylanceInstalledTopLevelModules: instead of pip list, do not use in terminal
- mcp_pylance_mcp_s_pylanceInvokeRefactoring: instead of manual refactoring, do not use in terminal
- mcp_pylance_mcp_s_pylancePythonEnvironments: instead of conda env list or python -m venv, do not use in terminal
- mcp_pylance_mcp_s_pylanceRunCodeSnippet: instead of python -c, do not use in terminal
- mcp_pylance_mcp_s_pylanceSettings: instead of manual settings check, do not use in terminal
- mcp_pylance_mcp_s_pylanceSyntaxErrors: instead of python -m py_compile, do not use in terminal
- mcp_pylance_mcp_s_pylanceUpdatePythonEnvironment: instead of conda activate or source activate, do not use in terminal
- mcp_pylance_mcp_s_pylanceWorkspaceRoots: instead of manual workspace check, do not use in terminal
- mcp_pylance_mcp_s_pylanceWorkspaceUserFiles: instead of find . -name "*.py", do not use in terminal
- run_in_terminal: this is the tool for running terminal commands, use it instead of manual terminal interaction
- runSubagent: instead of manual subtask handling, do not use in terminal
- runTests: instead of python -m pytest (macOS/Linux/Windows), do not use in terminal
- terminal_last_command: instead of history (macOS/Linux) or doskey /history (Windows), do not use in terminal
- terminal_selection: instead of manual selection, do not use in terminal

## Preferred Libraries
- requests: HTTP requests
- beautifulsoup4: HTML parsing
- sqlite3: Database operations (standard library)
- argparse: CLI argument parsing (standard library)
- logging: Logging (standard library)
- pytest: Testing framework
- pytest-cov: Coverage reporting
- pytest-mock: Mocking utilities
