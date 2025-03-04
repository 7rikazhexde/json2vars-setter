import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest
from pytest_mock import MockerFixture

from json2vars_setter.update_matrix_dynamic import (
    VersionStrategy,
    get_version_fetcher,
    get_versions_from_strategy,
    load_json_file,
    main,
    save_json_file,
    update_matrix_json,
)
from json2vars_setter.version.core.base import (
    BaseVersionFetcher,
    ReleaseInfo,
    VersionInfo,
)

# ---- Fixtures and Mocks ----


@pytest.fixture
def sample_matrix_json() -> Dict[str, Any]:
    """Sample matrix.json data for testing"""
    return {
        "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
        "versions": {"python": ["3.10", "3.11"], "nodejs": ["16", "18"]},
        "ghpages_branch": "gh-pages",
    }


@pytest.fixture
def temp_json_file(sample_matrix_json: Dict[str, Any]) -> Generator[str, None, None]:
    """Create a temporary JSON file with sample data"""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(sample_matrix_json, f)
    yield path
    os.unlink(path)


class MockVersionFetcher(BaseVersionFetcher):
    """Mock version fetcher for testing"""

    def __init__(
        self, stable: Optional[str] = "2.0.0", latest: Optional[str] = "2.1.0"
    ):
        # Call the parent class constructor with dummy values
        super().__init__(github_owner="mock-owner", github_repo="mock-repo")
        self.mock_stable = stable
        self.mock_latest = latest

    def fetch_versions(self, recent_count: int = 5) -> VersionInfo:
        """Return mock version info with specified stable and latest versions"""
        return VersionInfo(
            stable=self.mock_stable,
            latest=self.mock_latest,
            recent_releases=[],
            details={
                "source": "mock",
            },
        )

    def _is_stable_tag(self, tag: Dict[str, Any]) -> bool:
        """Mock implementation of abstract method"""
        return True

    def _parse_version_from_tag(self, tag: Dict[str, Any]) -> ReleaseInfo:
        """Mock implementation of abstract method"""
        # Return stable ReleaseInfo from tag
        return ReleaseInfo(version=tag.get("name", "1.0.0"), prerelease=False)


# ---- Test Functions ----


def test_version_strategy_validation() -> None:
    """Test VersionStrategy.is_valid"""
    assert VersionStrategy.is_valid(VersionStrategy.STABLE) is True
    assert VersionStrategy.is_valid(VersionStrategy.LATEST) is True
    assert VersionStrategy.is_valid(VersionStrategy.BOTH) is True
    assert VersionStrategy.is_valid("invalid") is False


def test_get_version_fetcher(mocker: MockerFixture) -> None:
    """Test get_version_fetcher returns correct fetcher for each language"""
    # Set up mocks for each fetcher
    mock_python = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.PythonVersionFetcher"
    )
    mock_nodejs = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.NodejsVersionFetcher"
    )
    mock_ruby = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.RubyVersionFetcher"
    )
    mock_go = mocker.patch("json2vars_setter.update_matrix_dynamic.GoVersionFetcher")
    mock_rust = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.RustVersionFetcher"
    )

    # Set return values
    mock_python.return_value = mock_python
    mock_nodejs.return_value = mock_nodejs
    mock_ruby.return_value = mock_ruby
    mock_go.return_value = mock_go
    mock_rust.return_value = mock_rust

    assert get_version_fetcher("python") == mock_python
    assert get_version_fetcher("nodejs") == mock_nodejs
    assert get_version_fetcher("ruby") == mock_ruby
    assert get_version_fetcher("go") == mock_go
    assert get_version_fetcher("rust") == mock_rust

    # Test unsupported language
    with pytest.raises(ValueError, match="Unsupported language: invalid"):
        get_version_fetcher("invalid")


def test_get_versions_from_strategy() -> None:
    """Test get_versions_from_strategy returns correct versions based on strategy"""
    version_info = VersionInfo(stable="2.0.0", latest="2.1.0")

    # Test STABLE strategy
    versions = get_versions_from_strategy(version_info, VersionStrategy.STABLE)
    assert versions == ["2.0.0"]

    # Test LATEST strategy
    versions = get_versions_from_strategy(version_info, VersionStrategy.LATEST)
    assert versions == ["2.1.0"]

    # Test BOTH strategy
    versions = get_versions_from_strategy(version_info, VersionStrategy.BOTH)
    assert versions == ["2.0.0", "2.1.0"]

    # Test when stable version is None
    version_info = VersionInfo(stable=None, latest="2.1.0")
    versions = get_versions_from_strategy(version_info, VersionStrategy.STABLE)
    assert versions == []

    # Test when latest version is None
    version_info = VersionInfo(stable="2.0.0", latest=None)
    versions = get_versions_from_strategy(version_info, VersionStrategy.LATEST)
    assert versions == []

    # Test when stable and latest are the same
    version_info = VersionInfo(stable="2.0.0", latest="2.0.0")
    versions = get_versions_from_strategy(version_info, VersionStrategy.BOTH)
    assert versions == ["2.0.0"]  # Should not duplicate

    # Test invalid strategy
    with pytest.raises(ValueError, match="Invalid strategy: invalid"):
        get_versions_from_strategy(version_info, "invalid")


def test_load_json_file(
    temp_json_file: str, sample_matrix_json: Dict[str, Any]
) -> None:
    """Test load_json_file loads JSON correctly"""
    data = load_json_file(temp_json_file)
    assert data == sample_matrix_json

    # Test file not found
    with pytest.raises(SystemExit):
        load_json_file("nonexistent.json")

    # Test invalid JSON
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        f.write("invalid json")

    with pytest.raises(SystemExit):
        load_json_file(path)

    os.unlink(path)


def test_save_json_file_io_error(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test save_json_file handles IOError correctly"""
    # Set up mocks
    mock_logger = mocker.patch("json2vars_setter.update_matrix_dynamic.logger")
    mock_exit = mocker.patch("sys.exit")
    test_data = {"test": "value"}

    # Temporary file path for testing
    test_file = tmp_path / "test_file.json"

    # Simulate IOError when opening the file
    mocker.patch("builtins.open", side_effect=IOError("Simulated IO error"))

    # Execute the function
    save_json_file(str(test_file), test_data)

    # Assertions
    mock_logger.error.assert_called_with("Error saving JSON file: Simulated IO error")
    mock_exit.assert_called_with(1)


def test_save_json_file_type_error(mocker: MockerFixture, tmp_path: Path) -> None:
    """Test save_json_file handles TypeError correctly"""
    # Set up mocks
    mock_logger = mocker.patch("json2vars_setter.update_matrix_dynamic.logger")
    mock_exit = mocker.patch("sys.exit")
    test_data = {"test": "value"}

    # Temporary file path for testing
    test_file = tmp_path / "test_file.json"

    # Simulate TypeError when dumping JSON
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("json.dump", side_effect=TypeError("Simulated Type error"))

    # Execute the function
    save_json_file(str(test_file), test_data)

    # Assertions
    mock_logger.error.assert_called_with("Error saving JSON file: Simulated Type error")
    mock_exit.assert_called_with(1)


def test_update_matrix_json(
    mocker: MockerFixture, sample_matrix_json: Dict[str, Any]
) -> None:
    """Test update_matrix_json updates the JSON correctly"""
    # Set up mocks
    mock_load = mocker.patch("json2vars_setter.update_matrix_dynamic.load_json_file")
    mock_load.return_value = sample_matrix_json.copy()

    mock_save = mocker.patch("json2vars_setter.update_matrix_dynamic.save_json_file")

    # Create a real MockVersionFetcher instance
    mock_fetcher_instance = MockVersionFetcher(stable="3.12", latest="3.13")
    mock_get_fetcher = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.get_version_fetcher"
    )
    mock_get_fetcher.return_value = mock_fetcher_instance

    # Test with single language - stable
    update_matrix_json("test.json", {"python": "stable"}, dry_run=False)

    # Check the matrix was updated correctly
    updated_matrix = mock_save.call_args[0][1]
    assert updated_matrix["versions"]["python"] == ["3.12"]

    # Test with multiple languages
    mock_load.return_value = sample_matrix_json.copy()

    # Set up mock to return different instances for different calls
    python_fetcher = MockVersionFetcher(stable="3.12", latest="3.13")
    nodejs_fetcher = MockVersionFetcher(stable="20", latest="22")
    mock_get_fetcher.side_effect = [python_fetcher, nodejs_fetcher]

    update_matrix_json(
        "test.json", {"python": "stable", "nodejs": "latest"}, dry_run=False
    )
    updated_matrix = mock_save.call_args[0][1]
    assert updated_matrix["versions"]["python"] == ["3.12"]
    assert updated_matrix["versions"]["nodejs"] == ["22"]

    # Test dry run mode
    mock_load.return_value = sample_matrix_json.copy()
    mock_save.reset_mock()
    mock_get_fetcher.return_value = MockVersionFetcher(stable="3.12", latest="3.13")

    update_matrix_json("test.json", {"python": "both"}, dry_run=True)
    mock_save.assert_not_called()

    # Test exception handling
    mock_load.return_value = sample_matrix_json.copy()
    mock_get_fetcher.side_effect = Exception("Test error")

    # Should not raise exception, just log it
    update_matrix_json("test.json", {"python": "both"}, dry_run=False)


def test_main_function(mocker: MockerFixture) -> None:
    """Test the main function parses arguments correctly"""
    mock_update = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.update_matrix_json"
    )

    # Test with --all
    mocker.patch(
        "sys.argv",
        [
            "update_matrix_dynamic.py",
            "--all",
            "stable",
            "--json-file",
            "custom.json",
        ],
    )

    main()
    mock_update.assert_called_with(
        "custom.json",
        {
            "python": "stable",
            "nodejs": "stable",
            "ruby": "stable",
            "go": "stable",
            "rust": "stable",
        },
        False,
    )

    # Test with individual language flags
    mocker.patch(
        "sys.argv",
        [
            "update_matrix_dynamic.py",
            "--python",
            "latest",
            "--nodejs",
            "both",
            "--dry-run",
        ],
    )

    main()
    mock_update.assert_called_with(
        os.path.join(".github", "workflows", "matrix.json"),  # Default path
        {"python": "latest", "nodejs": "both"},
        True,  # dry_run=True
    )

    # Test with no language specified
    mocker.patch("sys.argv", ["update_matrix_dynamic.py", "--verbose"])

    with pytest.raises(SystemExit):
        main()


def test_main_function_integration(mocker: MockerFixture, temp_json_file: str) -> None:
    """Integration test for the main function"""
    # Mock the fetch_versions to return controlled values
    mock_get_fetcher = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.get_version_fetcher"
    )
    mock_get_fetcher.return_value = MockVersionFetcher(stable="3.12", latest="3.13")

    # This test will actually call the real functions
    mocker.patch(
        "sys.argv",
        [
            "update_matrix_dynamic.py",
            "--json-file",
            temp_json_file,
            "--python",
            "stable",
            "--dry-run",
        ],
    )

    main()

    # File should be unchanged because of dry-run
    with open(temp_json_file, "r") as f:
        data = json.load(f)

    assert data["versions"]["python"] == ["3.10", "3.11"]  # Still original values


# ---- Edge Cases ----


def test_version_fetcher_none_values() -> None:
    """Test behavior when version fetcher returns None values"""
    fetcher = MockVersionFetcher(stable=None, latest=None)
    version_info = fetcher.fetch_versions()

    # Should return empty list for any strategy
    assert get_versions_from_strategy(version_info, VersionStrategy.STABLE) == []
    assert get_versions_from_strategy(version_info, VersionStrategy.LATEST) == []
    assert get_versions_from_strategy(version_info, VersionStrategy.BOTH) == []


def test_update_matrix_json_missing_versions_key(mocker: MockerFixture) -> None:
    """Test update_matrix_json handles missing versions key"""
    # Matrix without versions key
    matrix_without_versions = {"os": ["ubuntu-latest"]}

    mock_load = mocker.patch("json2vars_setter.update_matrix_dynamic.load_json_file")
    mock_load.return_value = matrix_without_versions

    mock_save = mocker.patch("json2vars_setter.update_matrix_dynamic.save_json_file")

    mock_get_fetcher = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.get_version_fetcher"
    )
    mock_get_fetcher.return_value = MockVersionFetcher(stable="3.12", latest="3.13")

    update_matrix_json("test.json", {"python": "both"}, dry_run=False)

    updated_matrix = mock_save.call_args[0][1]
    assert "versions" in updated_matrix
    assert updated_matrix["versions"]["python"] == ["3.12", "3.13"]


def test_update_matrix_json_new_language(
    mocker: MockerFixture, sample_matrix_json: Dict[str, Any]
) -> None:
    """Test update_matrix_json adds a new language if it doesn't exist"""
    mock_load = mocker.patch("json2vars_setter.update_matrix_dynamic.load_json_file")
    mock_load.return_value = sample_matrix_json.copy()

    mock_save = mocker.patch("json2vars_setter.update_matrix_dynamic.save_json_file")

    mock_get_fetcher = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.get_version_fetcher"
    )
    mock_get_fetcher.return_value = MockVersionFetcher(stable="3.0.6", latest="3.1.6")

    # Ruby is not in the original sample data
    update_matrix_json("test.json", {"ruby": "both"}, dry_run=False)

    updated_matrix = mock_save.call_args[0][1]
    assert "ruby" in updated_matrix["versions"]
    assert updated_matrix["versions"]["ruby"] == ["3.0.6", "3.1.6"]

    # Original versions should be untouched
    assert updated_matrix["versions"]["python"] == ["3.10", "3.11"]
    assert updated_matrix["versions"]["nodejs"] == ["16", "18"]


def test_update_matrix_json_empty_versions(mocker: MockerFixture) -> None:
    """Test handling of empty version lists"""
    # Prepare sample data
    sample_data = {"versions": {"python": ["3.10"]}}

    mock_load = mocker.patch("json2vars_setter.update_matrix_dynamic.load_json_file")
    mock_load.return_value = sample_data

    mock_save = mocker.patch("json2vars_setter.update_matrix_dynamic.save_json_file")

    # Create a mock with empty versions
    mock_get_fetcher = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.get_version_fetcher"
    )
    mock_fetcher = MockVersionFetcher(stable=None, latest=None)
    mock_get_fetcher.return_value = mock_fetcher

    # Execute
    update_matrix_json("test.json", {"python": "both"}, dry_run=False)

    # Python version should not be changed (not updated to an empty list)
    updated_matrix = mock_save.call_args[0][1]
    assert "python" in updated_matrix["versions"]


def test_backup_creation_success(mocker: MockerFixture) -> None:
    """Test successful backup creation"""
    # Test data
    sample_data = {"versions": {"python": ["3.10"]}}

    # Set up mocks
    mock_load = mocker.patch("json2vars_setter.update_matrix_dynamic.load_json_file")
    mock_load.return_value = sample_data

    # Mock save_json_file
    mocker.patch("json2vars_setter.update_matrix_dynamic.save_json_file")

    mock_get_fetcher = mocker.patch(
        "json2vars_setter.update_matrix_dynamic.get_version_fetcher"
    )
    mock_get_fetcher.return_value = MockVersionFetcher(stable="3.11", latest="3.12")

    # Patch open function to mock file operations
    mock_file = mocker.mock_open(read_data='{"versions": {"python": ["3.10"]}}')
    mocker.patch("builtins.open", mock_file)

    # Execute
    update_matrix_json("test.json", {"python": "stable"}, dry_run=False)

    # Verify that backup file handling was called
    # Verify that write operation was performed
    assert (
        mock_file().write.call_count >= 1
    )  # Write operation to backup file was performed


def test_real_backup_creation(temp_json_file: str) -> None:
    """Test real backup creation using the file system"""
    # Test data
    test_data = {"versions": {"python": ["3.10"]}}

    # Create a temporary file
    fd, json_file = tempfile.mkstemp(suffix=".json")
    os.close(fd)  # Explicitly close the file descriptor

    # Write JSON data
    with open(json_file, "w") as f:
        json.dump(test_data, f)

    backup_file = f"{json_file}.bak"

    try:
        # Execute test
        with pytest.MonkeyPatch.context() as mp:
            # Patch get_version_fetcher
            mp.setattr(
                "json2vars_setter.update_matrix_dynamic.get_version_fetcher",
                lambda lang: MockVersionFetcher(stable="3.11", latest="3.12"),
            )

            # Execute update_matrix_json
            update_matrix_json(json_file, {"python": "stable"}, dry_run=False)

            # Verify that backup file was created
            assert os.path.exists(backup_file)

            # Verify that backup content matches the original file
            with open(backup_file, "r") as f:
                backup_data = json.load(f)
            assert backup_data == test_data
    finally:
        # Delete files after test
        if os.path.exists(json_file):
            os.unlink(json_file)
        if os.path.exists(backup_file):
            os.unlink(backup_file)
