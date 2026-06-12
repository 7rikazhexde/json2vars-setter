# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

json2vars-setter is a **GitHub Action** (composite action) that parses JSON files and sets their values as GitHub Actions output variables. It supports dynamic version management and caching for Python, Node.js, Ruby, Go, Rust, PHP, .NET (C#), Java, Deno, Bun, Zig, Elixir, Dart, Swift, Julia, Crystal, Haskell, OCaml, and Kotlin. The action reads a matrix JSON file (default: `.github/json2vars-setter/matrix.json`) and exposes OS lists, language versions, and other config as workflow outputs.

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

### Dependabot PR safety gate

A passing test run shows the code still works; it does **not** prove a dependency bump
is safe to merge. Four layers decide that, and **merging always stays manual** (repo
auto-merge is disabled):

1. **`cooldown`** (in `.github/dependabot.yml`) delays every bump until the release has
   been public for a few days (longer for major), so a freshly-published / compromised
   version is not pulled the instant it ships.
2. **`dependency-review.yml`** (on every PR to `main`) fails the PR if the dependency diff
   introduces a vulnerability ≥ moderate (GitHub Advisory DB). No-op on PRs with no
   manifest change, so it is cheap to run on everything.
3. **`dependabot-metadata.yml`** (`pull_request_target`, Dependabot PRs only) labels each
   PR by semver bump (`dependency:patch` vs `dependency:major`) so the risk is obvious at a
   glance. It only labels — it never checks out the PR's code, and never merges.
4. **`dependabot-auto-rebase.yml`** only *rebases* open Dependabot PRs so they stay
   mergeable (see [[dependabot-auto-rebase-setup]] in memory); a human still clicks Merge.

`dependency-review` should be a **required** status check in branch protection so the gate
cannot be skipped (branch protection is configured in the repo settings, not in-repo).

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
- **`version/fetchers/`** — Language-specific implementations (`python.py`, `nodejs.py`, `ruby.py`, `go.py`, `rust.py`, `php.py`, `dotnet.py`, `java.py`, `deno.py`, `bun.py`, `zig.py`, `elixir.py`, `dart.py`, `swift.py`, `julia.py`, `crystal.py`, `haskell.py`, `ocaml.py`, `kotlin.py`). Most parse tags from the respective GitHub repository; `java.py`, `dart.py`, and `swift.py` are exceptions — they override `fetch_versions` to query the Adoptium API, the Dart release archive, and the swift.org install API respectively (see `docs/reference/version-sources.md`). `julia.py`, `crystal.py`, `haskell.py`, and `ocaml.py` read GitHub tags but override `_get_github_tags` to sort by semantic version first, because the JuliaLang/julia, crystal-lang/crystal, ghc/ghc, and ocaml/ocaml tag APIs are not reliably newest-first (`crystal.py` also accepts both the `vX.Y.Z` and prefix-less `X.Y.Z` tag forms; `haskell.py` parses `ghc-X.Y.Z-release` tags; `ocaml.py` excludes `-beta`/`-alpha` and ancient `csl-*` tags). `kotlin.py` (JetBrains/kotlin) is a plain GitHub-tags fetcher like `ruby.py`/`go.py` — its tags are already newest-first, so it needs no sort override; stable means a bare `vX.Y.Z` tag (an anchored regex rejects `-RC`/`-Beta`/`-M` pre-releases)

### Entry Points

- **GitHub Action**: `action.yml` defines the composite action with inputs/outputs; its steps invoke `python -m json2vars_setter.features.<module>`
- **CLI**: `json2vars_setter/cli.py` — Typer app exposed as `json2vars` via `[project.scripts]`; commands call each feature's `main()` **in-process** (no subprocess). The three feature commands are **bridged** from each feature's `build_parser()`: `cli.py` generates the matching options dynamically (argparse stays the single source of truth) so shell completion covers the per-command options **and values**, then reconstructs argv and calls `main()`. A new feature option therefore needs **no** cli.py change. **The bridged params must be built as `typer.core.TyperOption` (not plain `click.Option`)**: Typer's completer only resolves an option's *value* when the param is a `TyperOption`, and choice values are supplied via the public `shell_complete=` callback — a plain `click.Option` completes option *names* but silently drops value completion. One consequence: the repeated argparse option `--languages` is completed one value at a time, so via the `json2vars` script you repeat the flag (`--languages python --languages nodejs`); `python -m …` still takes the space-separated list.
- **Shell completion**: bash uses Typer's generated completer as-is (its output is plain values — robust). **PowerShell** ships a hand-written completer at `scripts/json2vars-completion.ps1` (dot-source it from `$PROFILE`; documented in `docs/getting-started.md`) — Typer's generated PowerShell completer splits each `value:::help` line on `:::` and builds a `CompletionResult` whose tooltip must be non-empty, so **long help that wraps across lines throws and a whole command returns zero completions while leaking the completion env vars** (a later `--help` then prints completion noise). The shipped completer keeps only `:::` lines, splits on the first separator, falls back to the value for an empty tooltip, resets env vars in `finally`, and surfaces options at the bare command position. **Command-execution (subprocess) tests** for this live in `tests/test_cli_exec.py`, separate from the in-process `tests/test_cli.py`.
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
   (`LANGUAGE_FETCHERS`). This map is the **single source of truth** for the supported
   language set: the version-cache feature derives its `--languages` choices and `all`
   expansion from it (`SUPPORTED_LANGUAGES = list(LANGUAGE_FETCHERS)` in
   `features/version_cache.py`), so registering here automatically extends
   `cache-version` too. **Never hardcode a language list** anywhere that the registry
   can supply — derive it, the way `version_cache.py` does.
3. **Matrix update CLI** — `json2vars_setter/features/matrix_update.py`: add the
   `--<lang>` argument, the `args.<lang> = args.all` line in the `--all` block, and
   the `if args.<lang>: language_strategies["<lang>"] = ...` wiring.
4. **Action contract** — `action.yml`: add the `<lang>-strategy` input, the
   `versions_<lang>` output, and the strategy-arg building block. **No per-language
   summary `echo` is needed**: `features/github_output.py` (`print_output_summary`)
   logs a matrix-proportional summary of only the keys present in the JSON, so the
   action's output log scales with the matrix, not the language set.
5. **Tests (keep 100% coverage)** — `tests/version/fetchers/test_<lang>.py`, plus add
   the language to `tests/version/test_registry.py` and the `--all` / individual-flag
   assertions in `tests/features/test_matrix_update.py`. The version-cache tests are
   registry-derived (`test_supported_languages_matches_registry` and the `all`-expansion
   assertion in `tests/features/test_version_cache.py` reference `LANGUAGE_FETCHERS` /
   `SUPPORTED_LANGUAGES`), so they pick up the new language automatically — re-run them
   to confirm, no hardcoded list to edit.
6. **Example project** — `examples/<lang>/`: a small JSON-parser project with source,
   tests, `<lang>_project_matrix.json`, build config, and `README.md` (mirror
   `examples/ruby/`). The matrix versions must be in the format the language's
   `setup-*` action accepts. **Also decide on Dependabot coverage**: if the example
   ships a dependency manifest that Dependabot supports (e.g. `composer.json`→`composer`,
   `*.csproj`→`nuget`, `pom.xml`→`maven`, `pubspec.yaml`→`pub`, `Package.swift`→`swift`,
   `go.mod`→`gomod`, `Cargo.toml`→`cargo`, `package.json`→`npm`, `Gemfile`→`bundler`), add a
   matching `package-ecosystem` block in `.github/dependabot.yml` mirroring the existing
   example entries (weekly, grouped `*`, **major-version bumps ignored**, limit 10).
   Languages whose manifest Dependabot does **not** support — crystal (shards), haskell
   (cabal), julia (Pkg), ocaml (opam), kotlin (kotlinc CLI, no build file), deno, zig — get **no** entry; note that in the PR so
   the omission is intentional, not drift.
7. **Example CI workflow** — `.github/workflows/<lang>_test.yml` (mirror
   `ruby_test.yml`): `set_variables` → `run_tests` (matrix) → `update_badge`. The
   `update_badge` job needs a **dedicated gist** (`<lang>-test-badge.json`, written via
   `GIST_TOKEN`) — its `gistID` must be created by the repo owner and cannot be
   generated programmatically.
8. **Status badges** — add a row to the language table in `README.md` **and** the
   matching badge in `docs/index.md`, pointing at the new gist
   (`gist.githubusercontent.com/7rikazhexde/<GIST_ID>/raw/<lang>-test-badge.json`) and
   the new workflow. Also update any "supported languages" prose (README intro,
   `docs/features/dynamic-update.md`, `docs/features/version-caching.md`,
   `docs/reference/options.md`, this file's Project Overview + fetcher list).
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

## Sample Workflows (use-case gallery)

Beyond the per-language `*_test.yml` tests, the repo carries **`sample_*.yml`** workflows:
runnable, CI-validated demonstrations of *use cases* (single source of truth, monorepo,
template-from-cache, …). Their purpose is adoption confidence — a cautious user trusts a
**green badge on a real run** far more than a doc snippet, and can copy the files to
reproduce it. The "Sample Workflows" tables in `README.md` and `docs/index.md` are the
registry. The roadmap (remaining: conditional matrix, dynamic-update/scheduled
maintenance, reusable `workflow_call`, version caching) lives in the
`sample-workflows-gallery` memory.

**Execution & maintenance policy (keeps CI cheap as the gallery grows):**

- **Distinguish by filename, not folders** — GitHub only scans `.github/workflows/`
  flatly, so each sample is `sample_<usecase>.yml`.
- **Triggers:** `schedule` (weekly, **stagger the cron** across samples so they don't all
  fire at once) + `workflow_dispatch` + `pull_request` scoped to **that sample's own
  files only** (its `examples/showcase/<usecase>/**` dir + the workflow file). So routine
  PRs never run samples; editing a sample (or a Dependabot action bump touching it) runs
  only that one; the weekly run keeps the badge fresh and catches upstream drift.
- **Version maintenance stays automatic:** Dependabot bumps the third-party action SHAs
  (the bump PR touches the sample file → validates by running just that sample);
  `sync-version-refs.sh` keeps the `json2vars-setter@vX.Y.Z` self-ref current on release
  (validated by the next weekly run).
- **API-hitting samples** (dynamic update, cache refresh) must pass
  `env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}`; prefer `dry-run`/template-only where
  possible so the run is green and side-effect-free.
- **High-impact changes** to the action itself (`action.yml`, `json2vars_setter/**`) do
  **not** auto-run all samples — run them on demand via `workflow_dispatch`.

**Adding a Sample Workflow (checklist):**

1. **Example data** — `examples/showcase/<usecase>/` with the matrix JSON(s) + a
   `README.md` (what it shows + copy-to-adopt steps), mirroring
   `examples/showcase/monorepo/`.
2. **Workflow** — `.github/workflows/sample_<usecase>.yml`: triggers per the policy above
   (staggered `schedule` + `workflow_dispatch` + own-file `paths`),
   `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`, the demo jobs, and an `update_badge` job mirroring
   the per-language pattern.
3. **Badge gist** — a **dedicated gist** (`sample-<usecase>-badge.json`, written via
   `GIST_TOKEN`) whose `gistID` must be created by the repo owner (cannot be generated in
   CI). Wire it into the `update_badge` job.
4. **Registry** — add a row to the "Sample Workflows" table in **both** `README.md` and
   `docs/index.md` (endpoint badge + links to the workflow and the example).

## Code Conventions

- **Commit messages**: Follow [gitmoji](https://gitmoji.dev/) conventions. Releases are automated by **semantic-release-gitmoji**, which reads the gitmoji to pick the next version: `:boom:` → major, `:sparkles:` → minor, and fixes/maintenance (`:bug:`, `:lock:`, `:ambulance:`, `:zap:`, `:wrench:`, `:recycle:`, `:arrow_up:`, …) → patch. Other gitmoji (e.g. `:memo:`, `:art:`, `:white_check_mark:`) don't trigger a release. The full mapping is the `releaseRules` in `.releaserc.json`.
- **Branch naming**: Use prefixes: `feature-`, `bugfix-`, `docs-`, `refactor-`
- **GitHub Actions selection**: Prefer **official** actions (the `actions/*` org, or the
  language's first-party action such as `ruby/setup-ruby`, `actions/setup-dotnet`,
  `actions/setup-java`). When no official action exists, use a widely-adopted,
  actively-maintained third-party action (highest usage / trending), e.g.
  `shivammathur/setup-php` for PHP. Pin every `uses:` to a commit SHA with the version
  tag as a trailing comment (except the `7rikazhexde/json2vars-setter@vX.Y.Z`
  self-reference, which the Versioning Rule keeps as a tag).
- **Python version**: 3.10+ (mypy `python_version` and ruff `target-version` both track the 3.10 support floor)
- **Linting**: Ruff with E, F, I rules (E402 and E501 ignored)
- **Type checking**: mypy with strict settings (`disallow_untyped_defs`, `warn_return_any`)
- **Test coverage**: Minimum 95%, goal 100%. Branch coverage is disabled in config due to testmon compatibility
- **Testing framework**: pytest with pytest-mock, pytest-cov

## Versioning Rule

When the action version is bumped, **all usage examples must be pinned to the new version**. Every `uses: 7rikazhexde/json2vars-setter@vX.Y.Z` reference across `README.md`, `docs/**`, and the example workflows in `.github/workflows/**` must point to the version being released — usage examples must never lag behind the latest tag. Releases are automated by **semantic-release** (`.github/workflows/semantic-release.yml`): its `@semantic-release/exec` step runs `.github/scripts/sync-version-refs.sh <new-version>` (and `uv version` / `uv lock`), then `@semantic-release/git` commits the synced references back to `main` as part of the release. Keep that script in sync if reference locations change, and apply the same rule for any manual version bump.

The **third-party / official** action versions in the docs/README usage examples (`actions/checkout`, `actions/setup-python`, …) are a separate concern: `sync-version-refs.sh` only touches the `json2vars-setter` self-reference, and Dependabot only updates real workflows / `action.yml` (never Markdown). `.github/scripts/sync_doc_action_refs.py` closes that gap — it treats the SHA-pinned workflows + `action.yml` as the source of truth and rewrites each matching action's version tag in `README.md` and `docs/**`. It runs as the `sync-doc-action-refs` pre-commit hook (and `--check` for CI). Actions that appear only in the docs (e.g. `dorny/paths-filter`) have no source of truth and are left alone.

### Releasing (semantic-release-gitmoji)

Releases are **manually triggered** (`workflow_dispatch` on `semantic-release.yml`) but otherwise automatic: semantic-release-gitmoji derives the next version from the gitmoji of commits since the last tag, bumps `pyproject.toml` + `uv.lock`, syncs usage-example references, updates `CHANGELOG.md`, commits these to `main`, and creates the `vX.Y.Z` tag + GitHub Release. It uses `PAT_FOR_PUSHES` so the new tag can trigger downstream workflows. (Switch the trigger to `push: branches: [main]` for fully continuous releases.)

## Key File Locations

- Matrix JSON: `.github/json2vars-setter/matrix.json`
- Cache file: `.github/json2vars-setter/cache/version_cache.json`
- **Refreshing the sample data** (`matrix.json`, `cache/`, `sample/matrix.json`): run the
  `Refresh data files` workflow (`.github/workflows/refresh-data-files.yml`,
  `workflow_dispatch`). It runs the version tooling on a Linux runner (the fetchers crash
  on Windows OpenSSL locally) and opens a reviewable PR — never hand-edit the cache (its
  per-release commit SHAs can only come from the fetchers).
- Test fixtures: `tests/matrix_static.json`, `tests/python_project_matrix.json`
- Docs site: `docs/` (MkDocs Material, deployed to GitHub Pages)
- PowerShell completion script: `scripts/json2vars-completion.ps1`
- Future-improvement backlog: `.issues/`

## Future-Improvement Backlog (`.issues/`)

`.issues/` is a **lightweight, in-repo backlog** of ideas that are **not worth a
GitHub issue yet** but could be **promoted to one later** (kept visible in the repo
rather than lost in chat). It is a notepad, not a tracker. One Markdown file per idea,
named `issue<N>-<type>-<slug>.md` (`<type>` ∈ `enhancement`/`bug`/`docs`/`refactor`),
each capturing the problem, findings, options, and effort. See `.issues/README.md`.
