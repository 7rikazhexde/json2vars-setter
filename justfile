# json2vars-setter task runner (uv + just)
# Usage: `just <recipe>` (run `just` or `just --list` to see all recipes)

# Show available recipes
default:
    @just --list

# Run the test suite
test:
    uv run pytest

# Run tests with coverage (terminal + HTML report)
test-cov:
    uv run pytest --cov=json2vars_setter --cov-branch --cov-report term-missing --cov-report html

# Run tests with verbose coverage output
test-cov-verbose:
    uv run pytest -s -vv --cov=json2vars_setter --cov-branch --cov-report term-missing --cov-report html

# Generate a standalone HTML test report
test-html:
    uv run pytest --html=htmlcov/report_page.html

# CI: run tests and emit XML coverage (coverage.xml / pytest.xml / pytest-coverage.txt)
test-ci-xml:
    uv run python scripts/run_tests.py --report xml

# CI: run tests with terminal coverage report
test-ci-term:
    uv run python scripts/run_tests.py --report term

# Lint and format check
lint:
    uv run ruff check json2vars_setter
    uv run ruff format --check json2vars_setter

# Static type check
typecheck:
    uv run mypy --config-file=pyproject.toml

# Install the pre-commit git hook (run once per clone so hooks fire on commit)
install-hooks:
    uv run pre-commit install

# Run all pre-commit hooks
pre-commit:
    uv run pre-commit run --all-files

# Show CLI usage for the cache / dynamic-update modules
usage:
    uv run python json2vars_setter/cache_version_info.py --help
    uv run python json2vars_setter/update_matrix_dynamic.py --help
