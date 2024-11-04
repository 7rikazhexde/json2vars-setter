import json
import subprocess
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch

from json2vars_setter.json_to_github_output import parse_json, set_github_output

MATRIX_JSON_PATH = ".github/workflows/matrix.json"


# --- Test case for parse_json() ---


def test_parse_matrix_json() -> None:
    """Read matrix.json and test parse_json"""
    with open(MATRIX_JSON_PATH, "r") as f:
        data = json.load(f)

    expected_outputs = {
        "OS": '["ubuntu-latest", "windows-latest", "macos-latest"]',
        "OS_0": "ubuntu-latest",
        "OS_1": "windows-latest",
        "OS_2": "macos-latest",
        "VERSIONS_PYTHON": '["3.10", "3.11", "3.12", "3.13"]',
        # if empty list
        # "VERSIONS_PYTHON": "[]",
        "VERSIONS_PYTHON_0": "3.10",
        "VERSIONS_PYTHON_1": "3.11",
        "VERSIONS_PYTHON_2": "3.12",
        "VERSIONS_PYTHON_3": "3.13",
        "VERSIONS_RUBY": '["3.0.6", "3.1.6", "3.2.6"]',
        "VERSIONS_RUBY_0": "3.0.6",
        "VERSIONS_RUBY_1": "3.1.6",
        "VERSIONS_RUBY_2": "3.2.6",
        "VERSIONS_NODEJS": '["16", "18", "20", "22"]',
        "VERSIONS_NODEJS_0": "16",
        "VERSIONS_NODEJS_1": "18",
        "VERSIONS_NODEJS_2": "20",
        "VERSIONS_NODEJS_3": "22",
        "VERSIONS_GO": '["1.23.0", "1.23.1", "1.23.2"]',
        "VERSIONS_GO_0": "1.23.0",
        "VERSIONS_GO_1": "1.23.1",
        "VERSIONS_GO_2": "1.23.2",
        "VERSIONS_RUST": '["1.79.0", "1.80.0", "1.81.0", "1.82.0", "stable"]',
        "VERSIONS_RUST_0": "1.79.0",
        "VERSIONS_RUST_1": "1.80.0",
        "VERSIONS_RUST_2": "1.81.0",
        "VERSIONS_RUST_3": "1.82.0",
        "VERSIONS_RUST_4": "stable",
        "GHPAGES_BRANCH": "ghgapes",
    }

    outputs = parse_json(data)
    assert outputs == expected_outputs


def test_empty_json() -> None:
    """Test empty JSON data with parse_json"""
    data: dict[str, Any] = {}
    expected_outputs: dict[str, Any] = {}
    outputs = parse_json(data)
    assert outputs == expected_outputs


def test_invalid_data_type() -> None:
    """Test exceptions when invalid data types are passed"""
    data: Any = "invalid_type"
    with pytest.raises(TypeError):
        parse_json(data)


def test_parse_json_nested_list() -> None:
    """Test JSON data in nested list structure with parse_json"""
    data = [{"key": "value"}]
    expected_outputs = {"": '[{"key": "value"}]', "0_KEY": "value"}

    outputs = parse_json(data, debug=False)
    assert outputs == expected_outputs


# --- Test case for set_github_output() ---


def test_set_github_output(monkeypatch: MonkeyPatch, tmpdir: Any) -> None:
    """Test if output is written correctly using set_github_output"""
    output_file = tmpdir.join("GITHUB_OUTPUT")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output_file))

    outputs = {"TEST_OUTPUT": "test_value"}
    set_github_output(outputs, debug=True)

    with open(output_file, "r") as f:
        lines = f.readlines()

    assert "TEST_OUTPUT=test_value\n" in lines


def test_github_output_not_set(monkeypatch: MonkeyPatch) -> None:
    """Test if sys.exit(1) occurs when GITHUB_OUTPUT is not set"""
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    with pytest.raises(SystemExit) as excinfo:
        set_github_output({"TEST_OUTPUT": "test"}, debug=False)
    assert excinfo.value.code == 1


def test_set_github_output_without_debug(
    monkeypatch: MonkeyPatch, tmpdir: Any, capsys: Any
) -> None:
    """Test that debug messages are not output when debug=False"""
    github_output_file = tmpdir.join("GITHUB_OUTPUT")
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output_file))

    outputs = {"TEST_OUTPUT": "test_value"}
    set_github_output(outputs, debug=False)

    captured = capsys.readouterr()
    assert captured.out == ""


# --- Test cases with sub-processes ---


def test_main_execution_with_matrix_json(monkeypatch: MonkeyPatch, tmpdir: Any) -> None:
    """Test executing a script in a sub-process using matrix.json"""
    github_output_file = tmpdir.join("GITHUB_OUTPUT")
    monkeypatch.setenv("GITHUB_OUTPUT", str(github_output_file))

    # Script Execution
    result = subprocess.run(
        [
            "python",
            "json2vars_setter/json_to_github_output.py",
            MATRIX_JSON_PATH,
            "--debug",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Written to GITHUB_OUTPUT" in result.stdout
