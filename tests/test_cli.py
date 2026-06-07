"""
Tests for json2vars_setter.cli
"""

import pytest
from click.testing import CliRunner
from pytest_mock import MockerFixture

from json2vars_setter.cli import app

runner = CliRunner()


def test_usage_command() -> None:
    """The usage command prints a task-oriented goal->command guide"""
    result = runner.invoke(app, ["usage"])

    assert result.exit_code == 0

    # Task-oriented headings and the commands they map to
    assert "what do you want to do?" in result.stdout
    assert "json2vars update-matrix --all latest" in result.stdout
    assert "json2vars cache-version" in result.stdout
    assert "json2vars parse" in result.stdout
    assert "GITHUB_OUTPUT" in result.stdout
    # Discoverability of shell completion (bash / PowerShell)
    assert "json2vars --install-completion" in result.stdout


def test_no_args_shows_help() -> None:
    """Running with no command shows the help/command list, not just an error"""
    result = runner.invoke(app, [])

    # no_args_is_help renders the full help (Usage + Commands). Click uses
    # exit code 2 for a missing command; the point is the guidance is shown.
    assert result.exit_code == 2
    assert "Usage" in result.stdout
    assert "update-matrix" in result.stdout
    assert "cache-version" in result.stdout
    assert "parse" in result.stdout


def test_version_option() -> None:
    """--version prints the installed package version and exits 0"""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "json2vars-setter" in result.stdout


def test_parse_forwards_file_and_debug(mocker: MockerFixture) -> None:
    """parse forwards the JSON path (and --debug) to github_output.main in-process"""
    mock_main = mocker.patch("json2vars_setter.cli.github_output.main")

    result = runner.invoke(app, ["parse", "matrix.json", "--debug"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with(["matrix.json", "--debug"])


def test_parse_without_debug(mocker: MockerFixture) -> None:
    """parse omits --debug when the flag is not given"""
    mock_main = mocker.patch("json2vars_setter.cli.github_output.main")

    result = runner.invoke(app, ["parse", "matrix.json"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with(["matrix.json"])


def test_cache_version_bridges_options(mocker: MockerFixture) -> None:
    """cache-version reconstructs an argv list for version_cache.main"""
    mock_main = mocker.patch("json2vars_setter.cli.version_cache.main")

    result = runner.invoke(app, ["cache-version", "--languages", "python", "--force"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with(["--languages", "python", "--force"])


def test_cache_version_repeated_languages_and_typed_options(
    mocker: MockerFixture,
) -> None:
    """Repeated --languages collapses to one flag; int/Path options round-trip"""
    mock_main = mocker.patch("json2vars_setter.cli.version_cache.main")

    result = runner.invoke(
        app,
        [
            "cache-version",
            "--languages",
            "python",
            "--languages",
            "nodejs",
            "--max-age",
            "7",
            "--cache-file",
            "cache.json",
            "--template-only",
        ],
    )

    assert result.exit_code == 0
    mock_main.assert_called_once_with(
        [
            "--languages",
            "python",
            "nodejs",
            "--max-age",
            "7",
            "--cache-file",
            "cache.json",
            "--template-only",
        ]
    )


def test_update_matrix_bridges_options(mocker: MockerFixture) -> None:
    """update-matrix reconstructs an argv list for matrix_update.main"""
    mock_main = mocker.patch("json2vars_setter.cli.matrix_update.main")

    result = runner.invoke(app, ["update-matrix", "--all", "latest", "--dry-run"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with(["--all", "latest", "--dry-run"])


def test_update_matrix_no_options_yields_empty_argv(mocker: MockerFixture) -> None:
    """With no options set, the reconstructed argv is empty"""
    mock_main = mocker.patch("json2vars_setter.cli.matrix_update.main")

    result = runner.invoke(app, ["update-matrix"])

    assert result.exit_code == 0
    mock_main.assert_called_once_with([])


def test_completion_exposes_options() -> None:
    """The bridged commands expose their argparse options as Click params"""
    cache = app.commands["cache-version"]
    names = {opt for p in cache.params for opt in p.opts}
    assert {"--languages", "--max-age", "--cache-file", "--template-only"} <= names

    matrix = app.commands["update-matrix"]
    matrix_names = {opt for p in matrix.params for opt in p.opts}
    assert {"--python", "--all", "--dry-run"} <= matrix_names


def test_systemexit_zero_returns_zero(mocker: MockerFixture) -> None:
    """A SystemExit with code 0 from the feature main is treated as success"""
    mocker.patch("json2vars_setter.cli.version_cache.main", side_effect=SystemExit(0))

    result = runner.invoke(app, ["cache-version", "--template-only"])

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
    # The error message is written to stderr via typer.echo(err=True) and names
    # the command that failed.
    assert "Error: Failed to execute cache-version" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__])
