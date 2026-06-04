# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

json2vars-setter is a **GitHub Action** (composite action) that parses JSON files and sets their values as GitHub Actions output variables. It supports dynamic version management and caching for Python, Node.js, Ruby, Go, and Rust. The action reads a matrix JSON file (default: `.github/json2vars-setter/matrix.json`) and exposes OS lists, language versions, and other config as workflow outputs.

## Common Commands

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and
[just](https://github.com/casey/just) as the task runner (see `justfile`).

```bash
# Install dependencies (creates .venv from uv.lock)
uv sync

# Run tests with coverage (just recipe)
just test-cov

# Run tests verbose
just test-cov-verbose

# List all available just recipes
just

# Run a single test file
uv run pytest tests/features/test_github_output.py

# Run a single test by name
uv run pytest tests/features/test_version_cache.py -k "test_function_name"

# Lint (ruff)
uv run ruff check json2vars_setter
uv run ruff format --check json2vars_setter

# Type check (mypy)
uv run mypy --config-file=pyproject.toml

# Pre-commit hooks (runs all checks)
uv run pre-commit run --all-files

# Validate pyproject.toml schema / spell check (also run by pre-commit)
uvx validate-pyproject pyproject.toml
uvx typos            # config in [tool.typos] (excludes via files.extend-exclude)

# CLI usage help
uv run json2vars --help
```

### Modern quality preview (`.github/workflows/modern-quality.yml`)

A non-blocking CI suite (every analysis job is `continue-on-error`, results land
in the run summary): `validate-pyproject`, `typos`, `zizmor` (Actions security
audit), `ty` (Astral type checker — mypy stays canonical), `pip-audit` (dependency
CVEs), and `gitleaks` (secret scan, CI-only — no `GITLEAKS_LICENSE` needed for this
personal-account repo). pre-commit + the test workflows remain the required checks.
All `uses:` actions in `.github/workflows/**` and `action.yml` are pinned to commit
SHAs (with the version tag as a trailing comment) — except the self-reference
`uses: 7rikazhexde/json2vars-setter@vX.Y.Z`, which the Versioning Rule keeps as a tag.

## Architecture

### Three Feature Modules (`json2vars_setter/features/`)

The action has three processing stages with a priority chain: **dynamic update > cache version > JSON parse**. Each stage is a module under `json2vars_setter/features/` exposing a `build_parser()` + `main(argv=None)` pair (so it runs both via `python -m` and in-process from the CLI):

1. **`features/github_output.py`** — Always runs. Recursively flattens a JSON file into `GITHUB_OUTPUT` key-value pairs. Nested keys are joined with underscores and uppercased (e.g., `versions.python` → `VERSIONS_PYTHON`). Lists are serialized as JSON strings.

2. **`features/matrix_update.py`** — Optionally runs (highest priority). Fetches latest/stable language versions from GitHub APIs and updates the matrix JSON in-place before parsing. Uses `VersionStrategy` (STABLE, LATEST, BOTH) per language.

3. **`features/version_cache.py`** — Optionally runs (medium priority, only if dynamic update is off). Manages a TTL-based version cache file, supports incremental updates, and generates matrix templates from cached data.

### Version Fetcher System (`json2vars_setter/version/`)

A pluggable architecture for fetching language versions from GitHub:

- **`version/registry.py`** — `get_version_fetcher(language)` and the `LANGUAGE_FETCHERS` map: the single source of truth pairing each language with its fetcher (shared by the matrix-update and version-cache features)
- **`version/core/base.py`** — `BaseVersionFetcher` abstract class handles GitHub API pagination, authentication (via `GITHUB_TOKEN`), and defines the interface (`_is_stable_tag()`, `_parse_version_from_tag()`)
- **`version/core/exceptions.py`** — Exception hierarchy: `VersionFetchError` → `GitHubAPIError`, `ParseError`, `ValidationError`
- **`version/core/utils.py`** — Shared data classes (`VersionInfo`, `ReleaseInfo`) and helpers
- **`version/fetchers/`** — Language-specific implementations (`python.py`, `nodejs.py`, `ruby.py`, `go.py`, `rust.py`), each parsing tags from the respective GitHub repository

### Entry Points

- **GitHub Action**: `action.yml` defines the composite action with inputs/outputs; its steps invoke `python -m json2vars_setter.features.<module>`
- **CLI**: `json2vars_setter/cli.py` — Typer app exposed as `json2vars` via `[project.scripts]`; commands call each feature's `main()` **in-process** (no subprocess)
- **Direct module execution**: `python -m json2vars_setter.features.<module>`

## Code Conventions

- **Commit messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `test:`, …; use `feat!:` or a `BREAKING CHANGE:` footer for breaking changes). release-please parses these to compute the next version and the changelog, so the type prefix matters. A gitmoji may optionally follow the type (e.g. `feat: :sparkles: add X`).
- **Branch naming**: Use prefixes: `feature-`, `bugfix-`, `docs-`, `refactor-`
- **Python version**: 3.10+ (target 3.12 for mypy)
- **Linting**: Ruff with E, F, I rules (E402 and E501 ignored)
- **Type checking**: mypy with strict settings (`disallow_untyped_defs`, `warn_return_any`)
- **Test coverage**: Minimum 95%, goal 100%. Branch coverage is disabled in config due to testmon compatibility
- **Testing framework**: pytest with pytest-mock, pytest-cov, pytest-xdist

## Versioning Rule

When the action version is bumped, **all usage examples must be pinned to the new version**. Every `uses: 7rikazhexde/json2vars-setter@vX.Y.Z` reference across `README.md`, `docs/**`, and the example workflows in `.github/workflows/**` must point to the version being released — usage examples must never lag behind the latest tag. Releases are automated by **release-please** (`.github/workflows/release-please.yml`): its "Sync action version references into the release PR" step commits the matching `uses:` updates (and the regenerated `uv.lock`) **into the release PR**, so the references are correct at tag time. Keep that step in sync if reference locations change, and apply the same rule for any manual version bump.

### Releasing (release-please)

Merge Conventional Commits into `main`; release-please maintains a **release PR** that bumps `pyproject.toml`, updates `CHANGELOG.md`, and (via the sync step) `uv.lock` + usage examples. **Merging that release PR** (manually) creates the `vX.Y.Z` tag and the GitHub Release. The workflow uses `PAT_FOR_PUSHES` so the new tag can trigger downstream workflows.

## Key File Locations

- Matrix JSON: `.github/json2vars-setter/matrix.json`
- Cache file: `.github/json2vars-setter/cache/version_cache.json`
- Test fixtures: `tests/matrix_static.json`, `tests/python_project_matrix.json`
- Docs site: `docs/` (MkDocs Material, deployed to GitHub Pages)
