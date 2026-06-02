"""
Tests for json2vars_setter.cli
"""

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from json2vars_setter.cli import app

runner = CliRunner()


def test_usage_command() -> None:
    """Test for the usage command"""
    result = runner.invoke(app, ["usage"])

    assert result.exit_code == 0

    # Verify the output content
    assert "json2vars_setter Usage Examples" in result.stdout
    assert "Available commands:" in result.stdout
    assert "cache-version" in result.stdout
    assert "update-matrix" in result.stdout
    assert "usage" in result.stdout

    # Verify examples
    assert "Cache Version Information:" in result.stdout
    assert "Update Matrix:" in result.stdout


def test_cache_version_passthrough(mocker: MockerFixture) -> None:
    """cache-version forwards all extra args to version_cache.main in-process"""
    mock_main = mocker.patch("json2vars_setter.cli.version_cache.main")

    result = runner.invoke(app, ["cache-version", "--languages", "python", "--force"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with(["--languages", "python", "--force"])


def test_update_matrix_passthrough(mocker: MockerFixture) -> None:
    """update-matrix forwards all extra args to matrix_update.main in-process"""
    mock_main = mocker.patch("json2vars_setter.cli.matrix_update.main")

    result = runner.invoke(app, ["update-matrix", "--all", "latest"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with(["--all", "latest"])


def test_systemexit_help_returns_zero(mocker: MockerFixture) -> None:
    """A SystemExit with code 0 (e.g. --help) is treated as success"""
    mocker.patch("json2vars_setter.cli.version_cache.main", side_effect=SystemExit(0))

    result = runner.invoke(app, ["cache-version", "--help"])

    assert result.exit_code == 0


def test_systemexit_none_returns_zero(mocker: MockerFixture) -> None:
    """A SystemExit with code None is treated as success"""
    mocker.patch(
        "json2vars_setter.cli.version_cache.main", side_effect=SystemExit(None)
    )

    result = runner.invoke(app, ["cache-version"])

    assert result.exit_code == 0


def test_systemexit_nonzero_propagates_code(mocker: MockerFixture) -> None:
    """A non-zero integer SystemExit (argparse usage error) propagates the code"""
    mocker.patch("json2vars_setter.cli.matrix_update.main", side_effect=SystemExit(2))

    result = runner.invoke(app, ["update-matrix"])

    assert result.exit_code == 2


def test_systemexit_non_integer_code_maps_to_one(mocker: MockerFixture) -> None:
    """A SystemExit with a non-integer code maps to exit code 1"""
    mocker.patch(
        "json2vars_setter.cli.version_cache.main", side_effect=SystemExit("boom")
    )

    result = runner.invoke(app, ["cache-version"])

    assert result.exit_code == 1


def test_generic_error_reported(mocker: MockerFixture) -> None:
    """Any other exception is surfaced as a CLI error with exit code 1"""
    mocker.patch(
        "json2vars_setter.cli.version_cache.main",
        side_effect=RuntimeError("kaboom"),
    )

    result = runner.invoke(app, ["cache-version"])

    assert result.exit_code == 1
    # The error message is written to stderr via typer.echo(err=True);
    # Click >=8.2 keeps stderr separate from stdout in CliRunner.
    assert "Error: Failed to execute version_cache" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__])
