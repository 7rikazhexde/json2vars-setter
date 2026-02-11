# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

json2vars-setter is a **GitHub Action** (composite action) that parses JSON files and sets their values as GitHub Actions output variables. It supports dynamic version management and caching for Python, Node.js, Ruby, Go, and Rust. The action reads a matrix JSON file (default: `.github/json2vars-setter/matrix.json`) and exposes OS lists, language versions, and other config as workflow outputs.

## Common Commands

```bash
# Install dependencies
poetry install

# Run tests with coverage
poetry run task testcoverage

# Run tests verbose
poetry run task testcoverageverbose

# Run a single test file
poetry run pytest tests/test_json_to_github_output.py

# Run a single test by name
poetry run pytest tests/test_cache_version_info.py -k "test_function_name"

# Lint (ruff)
poetry run ruff check json2vars_setter
poetry run ruff format --check json2vars_setter

# Type check (mypy)
poetry run mypy --config-file=pyproject.toml

# Pre-commit hooks (runs all checks)
poetry run pre-commit run --all-files

# CLI usage help
poetry run json2vars --help
```

## Architecture

### Three Core Modules

The action has three processing stages with a priority chain: **dynamic update > cache version > JSON parse**.

1. **`json_to_github_output.py`** — Always runs. Recursively flattens a JSON file into `GITHUB_OUTPUT` key-value pairs. Nested keys are joined with underscores and uppercased (e.g., `versions.python` → `VERSIONS_PYTHON`). Lists are serialized as JSON strings.

2. **`update_matrix_dynamic.py`** — Optionally runs (highest priority). Fetches latest/stable language versions from GitHub APIs and updates the matrix JSON in-place before parsing. Uses `VersionStrategy` (STABLE, LATEST, BOTH) per language.

3. **`cache_version_info.py`** — Optionally runs (medium priority, only if dynamic update is off). Manages a TTL-based version cache file, supports incremental updates, and generates matrix templates from cached data.

### Version Fetcher System (`json2vars_setter/version/`)

A pluggable architecture for fetching language versions from GitHub:

- **`version/core/base.py`** — `BaseVersionFetcher` abstract class handles GitHub API pagination, authentication (via `GITHUB_TOKEN`), and defines the interface (`_is_stable_tag()`, `_parse_version_from_tag()`)
- **`version/core/exceptions.py`** — Exception hierarchy: `VersionFetchError` → `GitHubAPIError`, `ParseError`, `ValidationError`
- **`version/core/utils.py`** — Shared data classes (`VersionInfo`, `ReleaseInfo`) and helpers
- **`version/fetchers/`** — Language-specific implementations (`python.py`, `nodejs.py`, `ruby.py`, `go.py`, `rust.py`), each parsing tags from the respective GitHub repository

### Entry Points

- **GitHub Action**: `action.yml` defines the composite action with inputs/outputs
- **CLI**: `json2vars_setter/cli.py` — Typer app exposed as `json2vars` via Poetry scripts
- **Direct module execution**: `python -m json2vars_setter.<module>`

## Code Conventions

- **Commit messages**: Follow [gitmoji](https://gitmoji.dev/) conventions
- **Branch naming**: Use prefixes: `feature-`, `bugfix-`, `docs-`, `refactor-`
- **Python version**: 3.10+ (target 3.12 for mypy)
- **Linting**: Ruff with E, F, I rules (E402 and E501 ignored)
- **Type checking**: mypy with strict settings (`disallow_untyped_defs`, `warn_return_any`)
- **Test coverage**: Minimum 95%, goal 100%. Branch coverage is disabled in config due to testmon compatibility
- **Testing framework**: pytest with pytest-mock, pytest-cov, pytest-xdist

## Key File Locations

- Matrix JSON: `.github/json2vars-setter/matrix.json`
- Cache file: `.github/json2vars-setter/cache/version_cache.json`
- Test fixtures: `tests/matrix_static.json`, `tests/python_project_matrix.json`
- Docs site: `docs/` (MkDocs Material, deployed to GitHub Pages)
