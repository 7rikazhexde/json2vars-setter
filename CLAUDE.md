# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

json2vars-setter is a **GitHub Action** (composite action) that parses JSON files and sets their values as GitHub Actions output variables. It supports dynamic version management and caching for Python, Node.js, Ruby, Go, Rust, and PHP. The action reads a matrix JSON file (default: `.github/json2vars-setter/matrix.json`) and exposes OS lists, language versions, and other config as workflow outputs.

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
- **`version/fetchers/`** — Language-specific implementations (`python.py`, `nodejs.py`, `ruby.py`, `go.py`, `rust.py`, `php.py`), each parsing tags from the respective GitHub repository

### Entry Points

- **GitHub Action**: `action.yml` defines the composite action with inputs/outputs; its steps invoke `python -m json2vars_setter.features.<module>`
- **CLI**: `json2vars_setter/cli.py` — Typer app exposed as `json2vars` via `[project.scripts]`; commands call each feature's `main()` **in-process** (no subprocess)
- **Direct module execution**: `python -m json2vars_setter.features.<module>`

## Adding a New Language (complete checklist)

Adding a supported language touches **code, the action contract, tests, an example
project, a CI workflow, status badges, and docs**. All of the following must be done
or the addition is incomplete:

1. **Fetcher** — `json2vars_setter/version/fetchers/<lang>.py`: a `BaseVersionFetcher`
   subclass implementing `_is_stable_tag` / `_parse_version_from_tag` (and usually
   `_get_stability_criteria`) plus a `<lang>_filter_func` and the `__main__` block,
   modeled on the closest existing fetcher (e.g. `ruby.py` / `go.py`).
2. **Registry** — register the fetcher in `json2vars_setter/version/registry.py`
   (`LANGUAGE_FETCHERS`).
3. **Matrix update CLI** — `json2vars_setter/features/matrix_update.py`: add the
   `--<lang>` argument, the `args.<lang> = args.all` line in the `--all` block, and
   the `if args.<lang>: language_strategies["<lang>"] = ...` wiring.
4. **Action contract** — `action.yml`: add the `<lang>-strategy` input, the
   `versions_<lang>` output, the strategy-arg building block, and the summary `echo`.
5. **Tests (keep 100% coverage)** — `tests/version/fetchers/test_<lang>.py`, plus add
   the language to `tests/version/test_registry.py` and the `--all` / individual-flag
   assertions in `tests/features/test_matrix_update.py`.
6. **Example project** — `examples/<lang>/`: a small JSON-parser project with source,
   tests, `<lang>_project_matrix.json`, build config, and `README.md` (mirror
   `examples/ruby/`). The matrix versions must be in the format the language's
   `setup-*` action accepts.
7. **Example CI workflow** — `.github/workflows/<lang>_test.yml` (mirror
   `ruby_test.yml`): `set_variables` → `run_tests` (matrix) → `update_badge`. The
   `update_badge` job needs a **dedicated gist** (`<lang>-test-badge.json`, written via
   `GIST_TOKEN`) — its `gistID` must be created by the repo owner and cannot be
   generated programmatically.
8. **Status badges** — add a row to the language table in `README.md` **and** the
   matching badge in `docs/index.md`, pointing at the new gist
   (`gist.githubusercontent.com/7rikazhexde/<GIST_ID>/raw/<lang>-test-badge.json`) and
   the new workflow. Also update any "supported languages" prose (README intro,
   `docs/features/dynamic-update.md`, `docs/reference/options.md`, this file's
   Project Overview + fetcher list).
9. **Release ordering (two-phase action reference)** — a new language's
   `versions_<lang>` output does not exist in the published tag until the release that
   adds it, so a tag ref (`@vX.Y.Z`) in `<lang>_test.yml` would fail on the introducing
   PR. Handle this in two phases:
   - **In the introducing PR:** point `<lang>_test.yml` at the in-repo action with
     `uses: ./` so the workflow tests the PR's own code and is green from the start.
   - **After the release that adds the language:** switch it to the pinned tag
     `uses: 7rikazhexde/json2vars-setter@vX.Y.Z` to match every other `*_test.yml` and
     the Versioning Rule. From then on `sync-version-refs.sh` keeps it pinned to the
     latest release. **This swap is a required follow-up** — track it so the example
     workflow does not stay on `./`.

## Code Conventions

- **Commit messages**: Follow [gitmoji](https://gitmoji.dev/) conventions. Releases are automated by **semantic-release-gitmoji**, which reads the gitmoji to pick the next version: `:boom:` → major, `:sparkles:` → minor, and fixes/maintenance (`:bug:`, `:lock:`, `:ambulance:`, `:zap:`, `:wrench:`, `:recycle:`, `:arrow_up:`, …) → patch. Other gitmoji (e.g. `:memo:`, `:art:`, `:white_check_mark:`) don't trigger a release. The full mapping is the `releaseRules` in `.releaserc.json`.
- **Branch naming**: Use prefixes: `feature-`, `bugfix-`, `docs-`, `refactor-`
- **Python version**: 3.10+ (target 3.12 for mypy)
- **Linting**: Ruff with E, F, I rules (E402 and E501 ignored)
- **Type checking**: mypy with strict settings (`disallow_untyped_defs`, `warn_return_any`)
- **Test coverage**: Minimum 95%, goal 100%. Branch coverage is disabled in config due to testmon compatibility
- **Testing framework**: pytest with pytest-mock, pytest-cov, pytest-xdist

## Versioning Rule

When the action version is bumped, **all usage examples must be pinned to the new version**. Every `uses: 7rikazhexde/json2vars-setter@vX.Y.Z` reference across `README.md`, `docs/**`, and the example workflows in `.github/workflows/**` must point to the version being released — usage examples must never lag behind the latest tag. Releases are automated by **semantic-release** (`.github/workflows/semantic-release.yml`): its `@semantic-release/exec` step runs `.github/scripts/sync-version-refs.sh <new-version>` (and `uv version` / `uv lock`), then `@semantic-release/git` commits the synced references back to `main` as part of the release. Keep that script in sync if reference locations change, and apply the same rule for any manual version bump.

### Releasing (semantic-release-gitmoji)

Releases are **manually triggered** (`workflow_dispatch` on `semantic-release.yml`) but otherwise automatic: semantic-release-gitmoji derives the next version from the gitmoji of commits since the last tag, bumps `pyproject.toml` + `uv.lock`, syncs usage-example references, updates `CHANGELOG.md`, commits these to `main`, and creates the `vX.Y.Z` tag + GitHub Release. It uses `PAT_FOR_PUSHES` so the new tag can trigger downstream workflows. (Switch the trigger to `push: branches: [main]` for fully continuous releases.)

## Key File Locations

- Matrix JSON: `.github/json2vars-setter/matrix.json`
- Cache file: `.github/json2vars-setter/cache/version_cache.json`
- Test fixtures: `tests/matrix_static.json`, `tests/python_project_matrix.json`
- Docs site: `docs/` (MkDocs Material, deployed to GitHub Pages)
