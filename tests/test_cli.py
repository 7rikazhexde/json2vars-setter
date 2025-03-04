"""
Tests for json2vars_setter.cli
"""

import subprocess
import sys
from typing import Any, List

from pytest import MonkeyPatch
from typer.testing import CliRunner

from json2vars_setter.cli import app


def test_usage_command() -> None:
    """Test for the usage command"""
    # Set up the runner for CLI tests
    runner = CliRunner()

    # Execute the usage command
    result = runner.invoke(app, ["usage"])

    # Test verification
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


def test_cache_version_command(monkeypatch: MonkeyPatch) -> None:
    """Test for the cache-version command"""

    # Mock subprocess.run and sys.exit
    def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="", stderr=""
        )

    exit_code: int = 0

    def mock_exit(code: int = 0) -> None:
        nonlocal exit_code
        exit_code = code

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(sys, "exit", mock_exit)

    # Set up the runner for CLI tests
    runner = CliRunner()

    # Execute the command
    result = runner.invoke(app, ["cache-version"])

    # Verification
    assert result.exit_code == 0
    assert exit_code == 0


def test_cache_version_with_help(monkeypatch: MonkeyPatch) -> None:
    """Test for the cache-version command with help option"""

    # Mock subprocess.run and sys.exit
    def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="", stderr=""
        )

    exit_code: int = 0

    def mock_exit(code: int = 0) -> None:
        nonlocal exit_code
        exit_code = code

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(sys, "exit", mock_exit)

    # Set up the runner for CLI tests
    runner = CliRunner()

    # Execute the command (with help flag)
    result = runner.invoke(app, ["cache-version", "--help"])

    # Verification
    assert result.exit_code == 0
    assert exit_code == 0


def test_cache_version_error(monkeypatch: MonkeyPatch) -> None:
    """Test for error case of the cache-version command"""
    # Mock subprocess.run to raise an error
    exit_calls: List[int] = []

    def mock_run_error(*args: Any, **kwargs: Any) -> None:
        raise subprocess.CalledProcessError(1, "mock command")

    def mock_exit(code: int = 0) -> None:
        exit_calls.append(code)

    monkeypatch.setattr(subprocess, "run", mock_run_error)
    monkeypatch.setattr(sys, "exit", mock_exit)

    # Set up the runner for CLI tests
    runner = CliRunner()

    # Execute the command
    result = runner.invoke(app, ["cache-version"], catch_exceptions=False)

    # Verification
    assert "Error:" in result.stdout
    # Verify that sys.exit was called with the appropriate code
    assert len(exit_calls) > 0
    assert 1 in exit_calls  # At least one call with code 1


def test_update_matrix_command(monkeypatch: MonkeyPatch) -> None:
    """Test for the update-matrix command"""

    # Mock subprocess.run and sys.exit
    def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="", stderr=""
        )

    exit_code: int = 0

    def mock_exit(code: int = 0) -> None:
        nonlocal exit_code
        exit_code = code

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(sys, "exit", mock_exit)

    # Set up the runner for CLI tests
    runner = CliRunner()

    # Execute the command
    result = runner.invoke(app, ["update-matrix"])

    # Verification
    assert result.exit_code == 0
    assert exit_code == 0


def test_update_matrix_with_help(monkeypatch: MonkeyPatch) -> None:
    """Test for the update-matrix command with help option"""

    # Mock subprocess.run and sys.exit
    def mock_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[Any]:
        return subprocess.CompletedProcess(
            args=args[0], returncode=0, stdout="", stderr=""
        )

    exit_code: int = 0

    def mock_exit(code: int = 0) -> None:
        nonlocal exit_code
        exit_code = code

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(sys, "exit", mock_exit)

    # Set up the runner for CLI tests
    runner = CliRunner()

    # Execute the command (with help flag)
    result = runner.invoke(app, ["update-matrix", "--help"])

    # Verification
    assert result.exit_code == 0
    assert exit_code == 0


def test_update_matrix_error(monkeypatch: MonkeyPatch) -> None:
    """Test for error case of the update-matrix command"""
    # Mock subprocess.run to raise an error
    exit_calls: List[int] = []

    def mock_run_error(*args: Any, **kwargs: Any) -> None:
        raise subprocess.CalledProcessError(1, "mock command")

    def mock_exit(code: int = 0) -> None:
        exit_calls.append(code)

    monkeypatch.setattr(subprocess, "run", mock_run_error)
    monkeypatch.setattr(sys, "exit", mock_exit)

    # Set up the runner for CLI tests
    runner = CliRunner()

    # Execute the command
    result = runner.invoke(app, ["update-matrix"], catch_exceptions=False)

    # Verification
    assert "Error:" in result.stdout
    # Verify that sys.exit was called with the appropriate code
    assert len(exit_calls) > 0
    assert 1 in exit_calls  # At least one call with code 1
