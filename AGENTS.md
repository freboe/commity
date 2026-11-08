# Repository Guidelines

## Project Structure

Commity is a Python 3.12+ CLI that generates commit messages from staged Git changes. `commity/cli.py` is the entry point. `commity/core.py` handles Git diffs and prompt generation, `commity/config.py` resolves settings, and `commity/llm/` contains provider clients and their factory. Shared helpers live in `commity/utils/`. Unit tests live in `tests/`, and integration and end-to-end tests live in `tests/integration/`. GitHub Actions workflows live in `.github/workflows/`.

## Build, Test, and Development Commands

- `uv sync --group dev` installs the project and development dependencies.
- `uv run commity --help` checks the local CLI entry point. Stage changes in a test Git repository before trying message generation.
- `make test` runs pytest. `make build` cleans and builds distributions in `dist/` with Hatch.
- `make format` formats Python files. `make check` checks lint and formatting with Ruff, and `make typecheck` runs mypy.

## Coding Style and Naming

Use four-space indentation, double quotes, and Ruff’s 100-character formatting width. Use `snake_case` for modules, functions, and variables, and `PascalCase` for classes. Keep provider-specific behavior in `commity/llm/` and reuse shared client logic.

## Testing

Use pytest and name test files and functions `test_*`. Reuse fixtures from `tests/conftest.py` and mock provider requests in unit tests. Run `uv run pytest --ignore=tests/integration` for the unit suite or `uv run pytest -m integration` for integration tests. Integration tests use Git or a local Ollama instance, depending on the test. Pytest reports branch coverage in the terminal and `htmlcov/`. Cover changed behavior with focused regression tests.

## Commits and Pull Requests

Follow the Conventional Commits style used in recent history, such as `feat(config): add provider setting` or `fix(cli): handle empty diffs`. Keep subjects short and use an imperative verb. In PRs, summarize the behavior change, list checks run, and link related issues when applicable. Include sample terminal output for visible CLI changes.

## Code Discovery

Prefer codebase-memory MCP tools for locating symbols and tracing callers. If `.codegraph/` exists, use CodeGraph before falling back to text search for code discovery.
