import json
import os
import platform
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
        "VERSIONS_RUBY": '["3.0.6", "3.1.6", "3.2.6", "3.3.6", "3.4.0", "3.4.1", "3.3.7", "3.2.7", "3.4.2"]',
        "VERSIONS_RUBY_0": "3.0.6",
        "VERSIONS_RUBY_1": "3.1.6",
        "VERSIONS_RUBY_2": "3.2.6",
        "VERSIONS_RUBY_3": "3.3.6",
        "VERSIONS_RUBY_4": "3.4.0",
        "VERSIONS_RUBY_5": "3.4.1",
        "VERSIONS_RUBY_6": "3.3.7",
        "VERSIONS_RUBY_7": "3.2.7",
        "VERSIONS_RUBY_8": "3.4.2",
        "VERSIONS_NODEJS": '["16", "18", "20", "22", "23"]',
        "VERSIONS_NODEJS_0": "16",
        "VERSIONS_NODEJS_1": "18",
        "VERSIONS_NODEJS_2": "20",
        "VERSIONS_NODEJS_3": "22",
        "VERSIONS_NODEJS_4": "23",
        "VERSIONS_GO": '["1.23.0", "1.23.1", "1.23.2", "1.23.3", "1.23.4", "1.23.5", "1.23.6", "1.24.0"]',
        "VERSIONS_GO_0": "1.23.0",
        "VERSIONS_GO_1": "1.23.1",
        "VERSIONS_GO_2": "1.23.2",
        "VERSIONS_GO_3": "1.23.3",
        "VERSIONS_GO_4": "1.23.4",
        "VERSIONS_GO_5": "1.23.5",
        "VERSIONS_GO_6": "1.23.6",
        "VERSIONS_GO_7": "1.24.0",
        "VERSIONS_RUST": '["1.79.0", "1.80.0", "1.81.0", "1.82.0", "1.83.0", "1.84.0", "1.84.1", "1.85.0", "stable"]',
        "VERSIONS_RUST_0": "1.79.0",
        "VERSIONS_RUST_1": "1.80.0",
        "VERSIONS_RUST_2": "1.81.0",
        "VERSIONS_RUST_3": "1.82.0",
        "VERSIONS_RUST_4": "1.83.0",
        "VERSIONS_RUST_5": "1.84.0",
        "VERSIONS_RUST_6": "1.84.1",
        "VERSIONS_RUST_7": "1.85.0",
        "VERSIONS_RUST_8": "stable",
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


def test_windows_path_handling(monkeypatch: MonkeyPatch, tmpdir: Any) -> None:
    """Test handling of Windows-style paths"""
    # Normalize path using platform-specific separator
    output_file = os.path.normpath(os.path.join(str(tmpdir), "GITHUB_OUTPUT"))

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create empty file
    with open(output_file, "w") as f:
        pass

    monkeypatch.setenv("GITHUB_OUTPUT", output_file)

    # Test with Windows-specific data
    test_data = {
        "PATH": os.path.normpath("C:/Program Files/Python"),
        "NESTED": {"SUB_PATH": os.path.normpath("D:/data/test")},
    }

    outputs = parse_json(test_data, debug=True)
    set_github_output(outputs, debug=True)

    with open(output_file, "r") as f:
        content = f.read()

    expected_path = os.path.normpath("C:/Program Files/Python")
    expected_sub_path = os.path.normpath("D:/data/test")

    assert f"PATH={expected_path}\n" in content
    assert f"NESTED_SUB_PATH={expected_sub_path}\n" in content


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
def test_windows_environment_vars(monkeypatch: MonkeyPatch, tmpdir: Any) -> None:
    """Test Windows-specific environment variable handling"""
    output_file = os.path.normpath(os.path.join(str(tmpdir), "GITHUB_OUTPUT"))

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create empty file
    with open(output_file, "w") as f:
        pass

    monkeypatch.setenv("GITHUB_OUTPUT", output_file)
    monkeypatch.setenv("TEMP", str(tmpdir))

    test_data = {
        "WINDOWS_VAR": os.path.normpath("%TEMP%/test"),
        "MIXED_PATH": os.path.normpath("C:/Program Files/Python"),
    }

    outputs = parse_json(test_data)
    set_github_output(outputs, debug=False)

    with open(output_file, "r") as f:
        content = f.read()

    expected_temp_path = os.path.normpath("%TEMP%/test")
    expected_mixed_path = os.path.normpath("C:/Program Files/Python")

    assert f"WINDOWS_VAR={expected_temp_path}\n" in content
    assert f"MIXED_PATH={expected_mixed_path}\n" in content


def test_empty_file_handling(monkeypatch: MonkeyPatch, tmpdir: Any) -> None:
    """Test handling of empty files"""
    output_file = os.path.normpath(os.path.join(str(tmpdir), "GITHUB_OUTPUT"))

    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create empty file
    with open(output_file, "w") as f:
        pass

    monkeypatch.setenv("GITHUB_OUTPUT", output_file)

    outputs = {"TEST": "value"}
    set_github_output(outputs, debug=False)

    with open(output_file, "r") as f:
        content = f.read()

    assert "TEST=value\n" in content
