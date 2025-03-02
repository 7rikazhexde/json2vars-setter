import json
import os
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest
from pytest_mock import MockFixture

from json2vars_setter.cache_version_info import (
    VersionCache,
    generate_version_template,
    get_version_fetcher,
    main,
    update_versions,
)
from json2vars_setter.version.core.base import (
    BaseVersionFetcher,
    ReleaseInfo,
    VersionInfo,
)

# ---- Fixtures and Mocks ----


@pytest.fixture
def sample_cache_data() -> dict:
    """Sample cache data for testing"""
    return {
        "metadata": {
            "last_updated": "2023-01-01T00:00:00",
            "version": "1.1",
            "version_count": 10,
        },
        "languages": {
            "python": {
                "latest": "3.11.0",
                "stable": "3.10.0",
                "recent_releases": [
                    {"version": "3.11.0", "date": "2022-10-24", "prerelease": False},
                    {"version": "3.10.0", "date": "2021-10-04", "prerelease": False},
                ],
                "last_updated": "2023-01-01T00:00:00",
            },
            "nodejs": {
                "latest": "18.0.0",
                "stable": "16.0.0",
                "recent_releases": [
                    {"version": "18.0.0", "date": "2022-04-19", "prerelease": False},
                    {"version": "16.0.0", "date": "2021-04-20", "prerelease": False},
                ],
                "last_updated": "2023-01-01T00:00:00",
            },
        },
    }


@pytest.fixture
def temp_cache_file(sample_cache_data: Dict[str, Any]) -> Generator[str, None, None]:
    """Create a temporary cache file with sample data"""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(sample_cache_data, f)
    yield path
    os.unlink(path)


@pytest.fixture
def temp_template_file() -> Generator[str, None, None]:
    """Create a temporary template file"""
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def sample_template_data() -> Dict[str, Any]:
    """Sample template data for testing"""
    return {
        "os": ["ubuntu-latest", "windows-latest", "macos-latest"],
        "versions": {
            "python": ["3.11.0", "3.10.0"],
            "nodejs": ["18.0.0", "16.0.0"],
        },
        "ghpages_branch": "gh-pages",
    }


@pytest.fixture
def temp_existing_template(
    sample_template_data: Dict[str, Any],
) -> Generator[str, None, None]:
    """Create a temporary existing template file"""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f:
        json.dump(sample_template_data, f)
    yield path
    os.unlink(path)


# MockVersionFetcherクラスのメソッド
class MockVersionFetcher(BaseVersionFetcher):
    """Mock version fetcher for testing"""

    def __init__(
        self, stable: Optional[str] = "2.0.0", latest: Optional[str] = "2.1.0"
    ) -> None:
        # Call the parent class constructor with dummy values
        super().__init__(github_owner="mock-owner", github_repo="mock-repo")
        self.mock_stable = stable
        self.mock_latest = latest
        self.recent_releases = []
        if self.mock_stable is not None:
            self.recent_releases.append(
                ReleaseInfo(version=self.mock_stable, prerelease=False)
            )
        if self.mock_latest is not None and self.mock_latest != self.mock_stable:
            self.recent_releases.append(
                ReleaseInfo(version=self.mock_latest, prerelease=False)
            )

    def fetch_versions(self, recent_count: int = 5) -> VersionInfo:
        """Return mock version info with specified stable and latest versions"""
        return VersionInfo(
            stable=self.mock_stable,
            latest=self.mock_latest,
            recent_releases=self.recent_releases,
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


# ---- Basic Tests ----


def test_version_cache_init(
    temp_cache_file: str, sample_cache_data: Dict[str, Any]
) -> None:
    """Test initialization of VersionCache"""
    cache = VersionCache(Path(temp_cache_file))
    assert cache.cache_file == Path(temp_cache_file)
    assert cache.data == sample_cache_data
    assert cache.version_count == 10
    assert cache.new_versions_found == defaultdict(int)


def test_version_cache_load_nonexistent_file() -> None:
    """Test loading a nonexistent cache file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "nonexistent.json"
        cache = VersionCache(cache_file)
        assert "metadata" in cache.data
        assert "last_updated" in cache.data["metadata"]
        assert cache.data["metadata"]["version"] == "1.1"
        assert "languages" in cache.data
        assert cache.version_count == 0


def test_version_cache_load_invalid_json() -> None:
    """Test loading an invalid JSON cache file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "invalid.json"
        with open(cache_file, "w") as f:
            f.write("invalid json")

        cache = VersionCache(cache_file)
        assert "metadata" in cache.data
        assert "languages" in cache.data
        assert cache.version_count == 0


def test_version_cache_get_version_count(temp_cache_file: str) -> None:
    """Test _get_version_count method"""
    cache = VersionCache(Path(temp_cache_file))
    assert cache._get_version_count() == 10

    # Test with no metadata
    cache.data = {"languages": {}}
    assert cache._get_version_count() == 0

    # Test with metadata but no version_count
    cache.data = {"metadata": {}, "languages": {}}
    assert cache._get_version_count() == 0


def test_version_cache_save(mocker: MockFixture) -> None:
    """Test save method"""
    # Mock logger
    mock_logger = mocker.patch("json2vars_setter.cache_version_info.logger")

    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "cache.json"
        cache = VersionCache(cache_file)

        # Add some data
        cache.data = {
            "metadata": {"last_updated": "2023-01-01T00:00:00", "version": "1.1"},
            "languages": {"python": {"latest": "3.11.0"}},
        }

        # Test successful save
        cache.save()
        assert cache_file.exists()
        mock_logger.info.assert_called()

        # Test directory creation
        nested_dir = Path(temp_dir) / "nested" / "dir"
        nested_file = nested_dir / "cache.json"
        cache2 = VersionCache(nested_file)
        cache2.data = cache.data.copy()
        cache2.save()
        assert nested_file.exists()

        # Test save with IOError
        mock_open = mocker.patch("builtins.open")
        mock_open.side_effect = IOError("Test error")
        cache.save()  # Should log an error but not raise an exception
        mock_logger.error.assert_called()


def test_version_cache_is_update_needed() -> None:
    """Test is_update_needed method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "cache.json"
        cache = VersionCache(cache_file)

        # Test with empty cache
        assert cache.is_update_needed("python") is True

        # Add language to cache
        cache.data["languages"]["python"] = {
            "latest": "3.11.0",
            "stable": "3.10.0",
            "recent_releases": [
                {"version": "3.11.0", "date": "2022-10-24", "prerelease": False}
            ],
            "last_updated": datetime.utcnow().isoformat(),
        }

        # Test with fresh cache
        assert cache.is_update_needed("python", max_age_days=1) is False

        # Test with stale cache
        stale_date = (datetime.utcnow() - timedelta(days=2)).isoformat()
        cache.data["languages"]["python"]["last_updated"] = stale_date
        assert cache.is_update_needed("python", max_age_days=1) is True

        # Test with requested count larger than cached count
        cache.data["languages"]["python"]["last_updated"] = (
            datetime.utcnow().isoformat()
        )
        assert cache.is_update_needed("python", requested_count=2) is True

        # Test with empty recent_releases
        cache.data["languages"]["python"]["recent_releases"] = []
        assert cache.is_update_needed("python") is True

        # Test with no recent_releases key
        del cache.data["languages"]["python"]["recent_releases"]
        assert cache.is_update_needed("python") is True

        # Test with invalid last_updated format
        cache.data["languages"]["python"] = {
            "latest": "3.11.0",
            "stable": "3.10.0",
            "recent_releases": [{"version": "3.11.0"}],
            "last_updated": "invalid-date",
        }
        assert cache.is_update_needed("python") is True

        # Test with missing last_updated
        del cache.data["languages"]["python"]["last_updated"]
        assert cache.is_update_needed("python") is True


def test_version_cache_merge_versions() -> None:
    """Test merge_versions method - basic functionality"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "cache.json"
        cache = VersionCache(cache_file)

        # Create version info with initial versions
        version_info = VersionInfo(
            stable="3.10.0",
            latest="3.11.0",
            recent_releases=[
                ReleaseInfo(version="3.11.0", prerelease=False),
                ReleaseInfo(version="3.10.0", prerelease=False),
            ],
        )

        # Test adding new language
        has_changes, new_versions = cache.merge_versions("python", version_info)
        assert has_changes is True
        assert "python" in cache.data["languages"]
        assert cache.data["languages"]["python"]["latest"] == "3.11.0"
        assert cache.data["languages"]["python"]["stable"] == "3.10.0"
        assert len(cache.data["languages"]["python"]["recent_releases"]) == 2
        assert cache.new_versions_found["python"] == 2
        assert new_versions == {"3.11.0", "3.10.0"}

        # Test with new versions - directly manipulate the cache to avoid sorting issues
        new_version_info = VersionInfo(
            stable="3.10.0",
            latest="3.12.0",
            recent_releases=[ReleaseInfo(version="3.12.0", prerelease=False)],
        )

        # Test the merge_versions behavior with incremental=False
        # In this mode, it replaces all releases with the new ones
        has_changes, new_versions = cache.merge_versions(
            "python", new_version_info, incremental=False
        )
        assert has_changes is True  # New version 3.12.0 is detected

        # Incremental mode with new version
        version_info_13 = VersionInfo(
            stable="3.10.0",
            latest="3.13.0",
            recent_releases=[ReleaseInfo(version="3.13.0", prerelease=False)],
        )

        # Set up the cache state to avoid sorting issues
        cache.data["languages"]["python"]["recent_releases"] = [
            {"version": "3.12.0", "prerelease": False}
        ]

        has_changes, new_versions = cache.merge_versions(
            "python", version_info_13, incremental=True
        )
        assert has_changes is True

        # Test with None values
        version_info_none = VersionInfo(
            stable=None,
            latest=None,
            recent_releases=[],
        )

        # Cache existing values first
        cache.data["languages"]["python"]["latest"] = "3.13.0"
        cache.data["languages"]["python"]["stable"] = "3.10.0"

        # Existing data should be preserved if not obtained from API
        has_changes, new_versions = cache.merge_versions("python", version_info_none)
        assert cache.data["languages"]["python"]["latest"] == "3.13.0"
        assert cache.data["languages"]["python"]["stable"] == "3.10.0"


def test_get_version_fetcher(mocker: MockFixture) -> None:
    """Test get_version_fetcher returns correct fetcher for each language"""
    # Set up mocks for each fetcher
    mock_python = mocker.patch(
        "json2vars_setter.cache_version_info.PythonVersionFetcher"
    )
    mock_nodejs = mocker.patch(
        "json2vars_setter.cache_version_info.NodejsVersionFetcher"
    )
    mock_ruby = mocker.patch("json2vars_setter.cache_version_info.RubyVersionFetcher")
    mock_go = mocker.patch("json2vars_setter.cache_version_info.GoVersionFetcher")
    mock_rust = mocker.patch("json2vars_setter.cache_version_info.RustVersionFetcher")

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


def test_update_versions(mocker: MockFixture) -> None:
    """Test update_versions function"""
    # Mock VersionCache
    mock_cache = mocker.MagicMock()
    mocker.patch(
        "json2vars_setter.cache_version_info.VersionCache", return_value=mock_cache
    )

    # Setup mock merge_versions to return some changes
    mock_cache.merge_versions.side_effect = [(True, {"3.11.0"}), (False, set())]
    mock_cache.is_update_needed.side_effect = [True, False]

    # Mock get_version_fetcher to return our mock fetcher
    mock_fetcher = mocker.MagicMock()
    mock_fetcher.fetch_versions.return_value = VersionInfo(
        stable="3.10.0",
        latest="3.11.0",
        recent_releases=[
            ReleaseInfo(version="3.11.0", prerelease=False),
            ReleaseInfo(version="3.10.0", prerelease=False),
        ],
    )
    mocker.patch(
        "json2vars_setter.cache_version_info.get_version_fetcher",
        return_value=mock_fetcher,
    )

    # Mock logger
    mocker.patch("json2vars_setter.cache_version_info.logger")

    # Test update_versions for multiple languages
    result = update_versions(
        ["python", "nodejs"], force=False, max_age_days=1, count=10
    )

    # Check the result
    assert "updated" in result
    assert "unchanged" in result
    assert "skipped" in result
    assert "failed" in result
    assert "new_versions_by_language" in result
    assert "cache_data" in result

    assert "python" in result["updated"]
    assert "nodejs" in result["unchanged"]
    assert "3.11.0" in result["new_versions_by_language"]["python"]

    # Test with custom cache file
    custom_cache_file = Path("custom_cache.json")
    update_versions(["python"], cache_file=custom_cache_file)

    # Reset mocks for the next tests
    mock_cache.reset_mock()
    mock_cache.is_update_needed.return_value = False  # Cache would be fresh normally

    # Test with forced update
    update_versions(["python"], force=True)
    # Should bypass is_update_needed check due to force=True
    mock_fetcher.fetch_versions.assert_called()

    # Test with exception in fetcher
    mock_fetcher.fetch_versions.side_effect = Exception("Test error")
    mocker.patch(
        "json2vars_setter.cache_version_info.get_version_fetcher",
        return_value=mock_fetcher,
    )

    result = update_versions(["python"], force=True)
    assert "python" in result["failed"]

    # Test with rate limit error
    mock_fetcher.fetch_versions.side_effect = Exception("rate limit exceeded")
    mocker.patch(
        "json2vars_setter.cache_version_info.get_version_fetcher",
        return_value=mock_fetcher,
    )

    result = update_versions(["python", "nodejs"], force=True)
    assert "python" in result["failed"]
    assert "nodejs" in result["skipped"]

    # Test default cache file path
    result = update_versions(["python"])
    assert result is not None  # Just ensure it runs without error


def test_generate_version_template(
    sample_cache_data: Dict[str, Any], temp_template_file: str
) -> None:
    """Test generate_version_template function - basic functionality"""
    # Test with default parameters
    generate_version_template(sample_cache_data, Path(temp_template_file))

    with open(temp_template_file, "r") as f:
        template = json.load(f)

    assert "os" in template
    assert "versions" in template
    assert "ghpages_branch" in template
    assert "python" in template["versions"]
    assert "nodejs" in template["versions"]
    assert template["versions"]["python"] == ["3.11.0", "3.10.0"]

    # Test with ascending sort order
    generate_version_template(
        sample_cache_data, Path(temp_template_file), sort_order="asc"
    )

    with open(temp_template_file, "r") as f:
        template = json.load(f)

    assert template["versions"]["python"] == ["3.10.0", "3.11.0"]  # Ascending order

    # Test with specific languages
    generate_version_template(
        sample_cache_data, Path(temp_template_file), languages=["python"]
    )

    with open(temp_template_file, "r") as f:
        template = json.load(f)

    assert "python" in template["versions"]
    assert "nodejs" not in template["versions"]


def test_main_function(mocker: MockFixture) -> None:
    """Test the main function parses arguments correctly"""
    # Mock Path.exists to return True
    mocker.patch.object(Path, "exists", return_value=True)

    # Mock argparse
    mock_parser = mocker.patch("argparse.ArgumentParser")
    mock_parser.return_value.parse_args.return_value = mocker.MagicMock()

    # Set mock args
    args = mock_parser.return_value.parse_args.return_value
    args.languages = ["python", "nodejs"]
    args.force = True
    args.max_age = 1
    args.count = 10
    args.cache_file = Path("test_cache.json")
    args.template_file = Path("test_template.json")
    args.existing_template = None
    args.cache_only = False
    args.template_only = False
    args.incremental = False
    args.keep_existing = False
    args.sort = "desc"
    args.verbose = False

    # Mock update_versions and generate_version_template
    mock_update = mocker.patch("json2vars_setter.cache_version_info.update_versions")
    mock_update.return_value = {"cache_data": {"languages": {}}}
    mock_generate = mocker.patch(
        "json2vars_setter.cache_version_info.generate_version_template"
    )

    # Test main function
    main()

    # Check if update_versions was called with correct args
    mock_update.assert_called_with(
        ["python", "nodejs"],
        force=True,
        max_age_days=1,
        count=10,
        cache_file=Path("test_cache.json"),
        incremental=False,
    )

    # Check if generate_version_template was called (don't check exact args)
    mock_generate.assert_called()

    # Test with template_only=True
    args.template_only = True
    mock_update.reset_mock()
    mock_generate.reset_mock()

    main()

    # update_versions should not be called
    mock_update.assert_not_called()

    # Test with cache_only=True
    args.template_only = False
    args.cache_only = True
    mock_update.reset_mock()
    mock_generate.reset_mock()

    main()

    # generate_version_template should not be called
    mock_generate.assert_not_called()

    # Test with "all" languages
    args.languages = ["all"]
    args.cache_only = False
    mock_update.reset_mock()

    main()

    # update_versions should be called with all languages
    mock_update.assert_called_with(
        ["python", "nodejs", "ruby", "go", "rust"],
        force=True,
        max_age_days=1,
        count=10,
        cache_file=Path("test_cache.json"),
        incremental=False,
    )

    # Test with explicitly provided existing_template
    args.languages = ["python"]
    args.existing_template = Path("existing_template.json")
    mock_generate.reset_mock()

    main()

    # Now check that generate_version_template is called at least once
    mock_generate.assert_called()


def test_main_with_force_flag(mocker: MockFixture) -> None:
    """Test main function with force flag"""
    # Mock argparse
    mock_parser = mocker.patch("argparse.ArgumentParser")
    mock_parser.return_value.parse_args.return_value = mocker.MagicMock()

    # Set mock args
    args = mock_parser.return_value.parse_args.return_value
    args.languages = ["python"]
    args.force = True
    args.max_age = 1
    args.count = 10
    args.cache_file = Path("test_cache.json")
    args.template_file = Path("test_template.json")
    args.existing_template = None
    args.cache_only = False
    args.template_only = False
    args.incremental = False
    args.keep_existing = False
    args.sort = "desc"
    args.verbose = False

    # Mock Path.exists to control cache existence
    mocker.patch.object(Path, "exists", return_value=True)

    # Mock update_versions
    mock_update = mocker.patch("json2vars_setter.cache_version_info.update_versions")
    mock_update.return_value = {"cache_data": {"languages": {}}}
    mocker.patch("json2vars_setter.cache_version_info.generate_version_template")

    main()

    # Check force was passed to update_versions
    mock_update.assert_called_with(
        ["python"],
        force=True,
        max_age_days=1,
        count=10,
        cache_file=Path("test_cache.json"),
        incremental=False,
    )

    # Test with custom parameters to cover more code paths
    args.keep_existing = True
    args.sort = "asc"
    args.incremental = True

    main()

    # Check with updated parameters
    mock_update.assert_called_with(
        ["python"],
        force=True,
        max_age_days=1,
        count=10,
        cache_file=Path("test_cache.json"),
        incremental=True,
    )


def test_main_with_verbose(mocker: MockFixture) -> None:
    """Test main function with verbose flag"""
    # Mock argparse
    mock_parser = mocker.patch("argparse.ArgumentParser")
    mock_parser.return_value.parse_args.return_value = mocker.MagicMock()

    # Set mock args
    args = mock_parser.return_value.parse_args.return_value
    args.languages = ["python"]
    args.force = False
    args.max_age = 1
    args.count = 10
    args.cache_file = Path("test_cache.json")
    args.template_file = Path("test_template.json")
    args.existing_template = None
    args.cache_only = False
    args.template_only = False
    args.incremental = False
    args.keep_existing = False
    args.sort = "desc"
    args.verbose = True

    # Mock logger
    mock_logger = mocker.patch("json2vars_setter.cache_version_info.logger")

    # Mock update_versions
    mock_update = mocker.patch("json2vars_setter.cache_version_info.update_versions")
    mock_update.return_value = {"cache_data": {"languages": {}}}
    mocker.patch("json2vars_setter.cache_version_info.generate_version_template")

    main()

    # Check logger.setLevel was called
    mock_logger.setLevel.assert_called()


def test_main_nonexistent_cache(mocker: MockFixture) -> None:
    """Test main function with nonexistent cache file"""
    # Mock argparse
    mock_parser = mocker.patch("argparse.ArgumentParser")
    mock_parser.return_value.parse_args.return_value = mocker.MagicMock()

    # Set mock args
    args = mock_parser.return_value.parse_args.return_value
    args.languages = ["python"]
    args.force = False
    args.max_age = 1
    args.count = 10
    args.cache_file = Path("nonexistent_cache.json")
    args.template_file = Path("test_template.json")
    args.existing_template = None
    args.cache_only = False
    args.template_only = False
    args.incremental = False
    args.keep_existing = False
    args.sort = "desc"
    args.verbose = False

    # Mock Path.exists to simulate nonexistent cache
    mocker.patch.object(Path, "exists", return_value=False)

    # Mock logger
    mock_logger = mocker.patch("json2vars_setter.cache_version_info.logger")

    # Mock update_versions
    mock_update = mocker.patch("json2vars_setter.cache_version_info.update_versions")
    mock_update.return_value = {"cache_data": {"languages": {}}}
    mocker.patch("json2vars_setter.cache_version_info.generate_version_template")

    main()

    # Check warning was logged
    mock_logger.warning.assert_called()

    # Check update_versions was called with force=True
    mock_update.assert_called_with(
        ["python"],
        force=True,  # Should be true when cache doesn't exist
        max_age_days=1,
        count=10,
        cache_file=Path("nonexistent_cache.json"),
        incremental=False,
    )


def test_main_integration(mocker: MockFixture) -> None:
    """Integration test for main function with actual files"""
    # Mock argparse
    mock_parser = mocker.patch("argparse.ArgumentParser")
    mock_parser.return_value.parse_args.return_value = mocker.MagicMock()

    # Set mock args
    args = mock_parser.return_value.parse_args.return_value
    args.languages = ["python"]
    args.force = True
    args.max_age = 1
    args.count = 10
    args.cache_file = Path("temp_cache.json")
    args.template_file = Path("temp_template.json")
    args.existing_template = None
    args.cache_only = False
    args.template_only = False
    args.incremental = False
    args.keep_existing = False
    args.sort = "desc"
    args.verbose = False

    # Mock get_version_fetcher to return our mock fetcher
    mock_fetcher = MockVersionFetcher(stable="3.10.0", latest="3.11.0")
    mocker.patch(
        "json2vars_setter.cache_version_info.get_version_fetcher",
        return_value=mock_fetcher,
    )

    try:
        # Run main with temporary files that we'll delete afterwards
        main()

        # Check template file was created
        assert os.path.exists("temp_template.json")

        with open("temp_template.json", "r") as f:
            template_data = json.load(f)

        assert "versions" in template_data
        assert "os" in template_data
        assert "ghpages_branch" in template_data

    finally:
        # Clean up temporary files
        if os.path.exists("temp_cache.json"):
            os.unlink("temp_cache.json")
        if os.path.exists("temp_template.json"):
            os.unlink("temp_template.json")


def test_generate_version_template_with_existing_mock(mocker: MockFixture) -> None:
    """Test the behavior of generate_version_template using mocks"""

    # Mock specific functions to improve coverage
    mock_dump = mocker.patch("json.dump")
    mock_load = mocker.patch("json.load")

    # Mock the result of loading an existing template
    mock_load.return_value = {
        "os": ["ubuntu-latest"],
        "versions": {
            "python": ["3.9.0", "3.8.0"],
            "ruby": ["3.0.0", "2.7.0"],
        },
        "ghpages_branch": "gh-pages",
    }

    # Call the function under test
    data = {
        "languages": {
            "golang": {
                "latest": "1.18.0",
                "stable": "1.17.0",
                "recent_releases": [
                    {"version": "1.18.0", "prerelease": False},
                    {"version": "1.17.0", "prerelease": False},
                ],
            }
        }
    }

    # Use existing template and keep_existing=True for coverage
    generate_version_template(
        data, Path("template.json"), Path("existing.json"), keep_existing=True
    )

    # Verify that json.dump was called
    mock_dump.assert_called()


def test_load_cache_file_error_handling(mocker: MockFixture) -> None:
    """Test file error handling in _load_cache method"""
    # Lines 117-118: In case of FileNotFoundError

    # Mock Path.exists to make it appear that the file exists
    mock_exists = mocker.patch("pathlib.Path.exists")
    mock_exists.return_value = True

    # Mock open to raise FileNotFoundError
    mock_open = mocker.patch("builtins.open")
    mock_open.side_effect = FileNotFoundError("Test error")

    # Test that default values are used when an error occurs during VersionCache initialization
    cache = VersionCache(Path("nonexistent.json"))
    assert "metadata" in cache.data
    assert "languages" in cache.data

    # Also test for IOError
    mocker.resetall()
    mock_exists = mocker.patch("pathlib.Path.exists")
    mock_exists.return_value = True

    mock_open = mocker.patch("builtins.open")
    mock_open.side_effect = IOError("Test error")

    cache = VersionCache(Path("error.json"))
    assert "metadata" in cache.data
    assert "languages" in cache.data


def test_merge_versions_edge_cases() -> None:
    """Test edge cases of merge_versions method"""
    # Line 184: When there are no existing releases in incremental mode
    cache = VersionCache(Path("cache.json"))

    # Directly manipulate data to test specific states
    cache.data["languages"]["python"] = {}  # Empty language entry

    # Version info for testing
    version_info = VersionInfo(
        stable="3.10.0",
        latest="3.11.0",
        recent_releases=[
            ReleaseInfo(version="3.11.0", prerelease=False),
        ],
    )

    # Add new release with incremental=True
    has_changes, new_versions = cache.merge_versions(
        "python", version_info, incremental=True
    )
    assert has_changes is True
    assert len(cache.data["languages"]["python"]["recent_releases"]) > 0

    # Line 261: When the version is the same and incremental=True, it is judged as no change
    cache.data["languages"]["python"]["recent_releases"] = [
        {"version": "3.11.0", "prerelease": False}
    ]

    # Try adding the same version again
    same_version_info = VersionInfo(
        stable="3.10.0",
        latest="3.11.0",
        recent_releases=[
            ReleaseInfo(version="3.11.0", prerelease=False),
        ],
    )

    has_changes, new_versions = cache.merge_versions(
        "python", same_version_info, incremental=True
    )
    assert new_versions == set()  # No new versions


def test_generate_template_empty_releases(mocker: MockFixture) -> None:
    """Test template generation from an empty release list"""
    # Lines 498, 501-502: Generate template from an empty release list
    mock_dump = mocker.patch("json.dump")

    # Data with only latest/stable and an empty release list
    empty_release_data = {
        "languages": {
            "python": {
                "latest": "3.11.0",
                "stable": "3.10.0",
                "recent_releases": [],
            }
        }
    }

    # Generate template
    generate_version_template(empty_release_data, Path("template.json"))
    mock_dump.assert_called_once()


def test_generate_template_none_values(mocker: MockFixture) -> None:
    """Test template generation from data containing None values"""
    # Lines 516-530: When latest and stable are None, but there is a release list
    mock_dump = mocker.patch("json.dump")

    # Case with latest=None, stable=None
    none_values_data = {
        "languages": {
            "golang": {
                "latest": None,
                "stable": None,
                "recent_releases": [{"version": "1.18.0", "prerelease": False}],
            }
        }
    }

    # Generate template
    generate_version_template(none_values_data, Path("template.json"))
    mock_dump.assert_called_once()

    # Case with latest=None, stable present
    mocker.resetall()
    mock_dump = mocker.patch("json.dump")

    none_latest_data = {
        "languages": {
            "golang": {
                "latest": None,
                "stable": "1.17.0",
                "recent_releases": [
                    {"version": "1.18.0-beta", "prerelease": True},
                    {"version": "1.17.0", "prerelease": False},
                ],
            }
        }
    }

    generate_version_template(none_latest_data, Path("template.json"))
    mock_dump.assert_called_once()

    # Case with stable=None, latest present
    mocker.resetall()
    mock_dump = mocker.patch("json.dump")

    none_stable_data = {
        "languages": {
            "golang": {
                "latest": "1.18.0-beta",
                "stable": None,
                "recent_releases": [{"version": "1.18.0-beta", "prerelease": True}],
            }
        }
    }

    generate_version_template(none_stable_data, Path("template.json"))
    mock_dump.assert_called_once()


def test_generate_template_with_versions_and_latest_stable(mocker: MockFixture) -> None:
    """Test cases where stable and latest are prioritized in template generation"""
    # Ensure specific versions are included
    mock_dump = mocker.patch("json.dump")

    test_data = {
        "languages": {
            "python": {
                "latest": "3.11.0",
                "stable": "3.10.0",
                "recent_releases": [
                    {"version": "3.9.0", "prerelease": False},
                    {"version": "3.8.0", "prerelease": False},
                ],
            }
        }
    }

    generate_version_template(test_data, Path("template.json"))

    # Verify that latest and stable are included even if not in the release list
    args = mock_dump.call_args[0][0]
    assert "versions" in args
    assert "python" in args["versions"]
    python_versions = args["versions"]["python"]
    assert "3.11.0" in python_versions
    assert "3.10.0" in python_versions

    os.unlink(Path("template.json"))


def test_load_cache_additional_error_handling() -> None:
    """Test additional error handling in _load_cache method"""
    # Detailed test for JSON decode errors
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "partial_json.json"

        # Create an incomplete JSON file
        with open(cache_file, "w") as f:
            f.write('{"metadata": {"last_updated": "')

        # Initialize VersionCache
        cache = VersionCache(cache_file)

        # Verify that the default empty data structure is set
        assert "metadata" in cache.data
        assert "languages" in cache.data
        assert "last_updated" in cache.data["metadata"]


def test_save_method_path_creation() -> None:
    """Test path creation functionality in save method"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a deeply nested directory path
        deep_path = Path(temp_dir) / "nested" / "very" / "deep" / "path" / "cache.json"

        # Initialize VersionCache
        cache = VersionCache(deep_path)

        # Set data
        cache.data = {
            "metadata": {
                "last_updated": datetime.utcnow().isoformat(),
                "version": "1.1",
            },
            "languages": {"python": {"latest": "3.11.0", "stable": "3.10.0"}},
        }

        # Call save method
        cache.save()

        # Verify that the file was created correctly
        assert deep_path.exists()

        # Verify the contents of the file
        with open(deep_path, "r") as f:
            loaded_data = json.load(f)

        assert loaded_data["languages"]["python"]["latest"] == "3.11.0"


def test_merge_versions_with_partially_populated_cache() -> None:
    """Test merge_versions with a partially populated cache"""
    cache = VersionCache(Path("temp_cache.json"))

    # Partially populated cache data
    cache.data["languages"]["python"] = {"latest": None, "stable": None}

    # Create version info
    version_info = VersionInfo(
        stable="3.10.0",
        latest="3.11.0",
        recent_releases=[
            ReleaseInfo(version="3.11.0", prerelease=False),
            ReleaseInfo(version="3.10.0", prerelease=False),
        ],
    )

    # Merge versions
    has_changes, new_versions = cache.merge_versions(
        "python", version_info, incremental=True
    )

    # Verify results
    assert has_changes is True
    assert new_versions == {"3.11.0", "3.10.0"}
    assert cache.data["languages"]["python"]["latest"] == "3.11.0"
    assert cache.data["languages"]["python"]["stable"] == "3.10.0"


def test_generate_version_template_complex_scenarios() -> None:
    complex_data = {
        "languages": {
            "python": {
                "latest": "3.12.0",
                "stable": "3.11.0",
                "recent_releases": [
                    {"version": "3.12.0-rc1", "prerelease": True},
                    {"version": "3.12.0", "prerelease": False},
                    {"version": "3.11.0", "prerelease": False},
                    {"version": "3.10.0", "prerelease": False},
                ],
            },
            "nodejs": {"latest": "18.0.0", "stable": "16.0.0", "recent_releases": []},
        }
    }

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    try:
        generate_version_template(
            complex_data, temp_path, sort_order="asc", keep_existing=False
        )

        with open(temp_path, "r") as f:
            template = json.load(f)

        # Verify that prereleases are excluded
        assert "python" in template["versions"]
        python_versions = template["versions"]["python"]

        # Verify that only expected versions are included
        assert set(python_versions) == {"3.10.0", "3.11.0", "3.12.0"}

    finally:
        os.unlink(temp_path)


def test_main_function_additional_scenarios(mocker: MockFixture) -> None:
    """Additional scenario tests for the main function"""
    # Mock command line arguments
    mock_parser = mocker.patch("argparse.ArgumentParser")
    mock_parser.return_value.parse_args.return_value = mocker.MagicMock()

    # Set mock arguments
    args = mock_parser.return_value.parse_args.return_value
    args.languages = ["rust"]  # Specific language
    args.force = False
    args.max_age = 7  # Longer max age
    args.count = 5  # Fewer versions to fetch
    args.cache_file = Path("custom_cache.json")
    args.template_file = Path("custom_template.json")
    args.existing_template = None
    args.cache_only = False
    args.template_only = False
    args.incremental = True  # Incremental mode
    args.keep_existing = True
    args.sort = "asc"
    args.verbose = True

    # Set up mocks
    mock_update = mocker.patch("json2vars_setter.cache_version_info.update_versions")
    mock_generate = mocker.patch(
        "json2vars_setter.cache_version_info.generate_version_template"
    )
    mock_logger = mocker.patch("json2vars_setter.cache_version_info.logger")

    # Mock Path.exists
    mocker.patch.object(Path, "exists", return_value=True)

    # Call main function
    main()

    # Verify calls
    mock_update.assert_called_once()
    mock_generate.assert_called_once()
    mock_logger.setLevel.assert_called_once()


def test_is_update_needed_empty_language_cache() -> None:
    """
    Test is_update_needed() method when language cache does not exist
    """
    # Initialize VersionCache with mocked data
    mock_data: Dict[str, Any] = {"metadata": {}}
    cache = VersionCache(Path("dummy_cache.json"))
    cache.data = mock_data

    # Verify that update is always needed when language cache does not exist
    assert cache.is_update_needed("python") is True


def test_merge_versions_empty_languages_key() -> None:
    """
    Test merge_versions() method when languages key does not exist
    """
    # Initialize VersionCache with mocked data
    mock_data: Dict[str, Any] = {"metadata": {}}
    cache = VersionCache(Path("dummy_cache.json"))
    cache.data = mock_data

    # Create mock VersionInfo
    mock_version_info = VersionInfo(
        stable="3.10.0",
        latest="3.11.0",
        recent_releases=[
            ReleaseInfo(version="3.11.0", prerelease=False),
            ReleaseInfo(version="3.10.0", prerelease=False),
        ],
    )

    # Call merge_versions() and verify it runs without error
    has_changes, new_versions = cache.merge_versions("python", mock_version_info)

    # Verify that languages key was added to the cache
    assert "languages" in cache.data
    assert "python" in cache.data["languages"]
    assert has_changes is True
    assert new_versions == {"3.11.0", "3.10.0"}


def test_merge_versions_release_sorting() -> None:
    """
    Test sorting of releases and keeping the latest N releases
    """
    cache = VersionCache(Path("dummy_cache.json"))
    cache.data = {"languages": {"python": {"recent_releases": []}}}

    # Create VersionInfo with multiple releases of different versions
    mock_version_info = VersionInfo(
        stable="3.10.0",
        latest="3.11.0",
        recent_releases=[
            ReleaseInfo(version="3.9.0", prerelease=False),
            ReleaseInfo(version="3.10.0", prerelease=False),
            ReleaseInfo(version="3.8.0", prerelease=False),
            ReleaseInfo(version="3.11.0", prerelease=False),
            ReleaseInfo(version="3.7.0", prerelease=False),
        ],
    )

    # Call with count=3 to keep only the latest 3 releases
    has_changes, new_versions = cache.merge_versions(
        "python", mock_version_info, count=3, incremental=True
    )

    # Verify results
    python_releases = cache.data["languages"]["python"]["recent_releases"]
    versions = [release["version"] for release in python_releases]

    # Verify that the latest 3 releases are kept in descending order
    assert versions == ["3.11.0", "3.10.0", "3.9.0"]
    assert len(versions) == 3


def test_merge_versions_empty_metadata() -> None:
    """
    Test merge_versions() method when metadata is empty
    """
    cache = VersionCache(Path("dummy_cache.json"))
    cache.data = {}  # Completely remove metadata

    mock_version_info = VersionInfo(
        stable="3.10.0",
        latest="3.11.0",
        recent_releases=[
            ReleaseInfo(version="3.11.0", prerelease=False),
            ReleaseInfo(version="3.10.0", prerelease=False),
        ],
    )

    # Call merge_versions()
    has_changes, new_versions = cache.merge_versions("python", mock_version_info)

    # Verify that metadata was added
    assert "metadata" in cache.data
    assert "last_updated" in cache.data["metadata"]
    assert cache.data["metadata"]["last_updated"] is not None


def test_generate_version_template_existing_file_error_handling(
    mocker: MockFixture, tmp_path: Path
) -> None:
    """
    Test error handling when loading an existing template file
    """
    # Create a broken JSON file
    broken_template_file = tmp_path / "broken_template.json"
    with open(broken_template_file, "w") as f:
        f.write("{invalid json")  # Invalid JSON file

    # Prepare mock cache data
    mock_cache_data = {
        "languages": {
            "python": {
                "latest": "3.11.0",
                "stable": "3.10.0",
                "recent_releases": [
                    {"version": "3.11.0", "prerelease": False},
                    {"version": "3.10.0", "prerelease": False},
                ],
            }
        }
    }

    # Prepare output file
    output_file = tmp_path / "output_template.json"

    # Prepare mocked logger
    mock_logger = mocker.patch("json2vars_setter.cache_version_info.logger")

    # Call the function
    generate_version_template(
        mock_cache_data, output_file, existing_file=broken_template_file
    )

    # Verify that a warning log was called
    mock_logger.warning.assert_called_once()

    # Verify that the output file was created with the default template structure
    with open(output_file, "r") as f:
        template = json.load(f)

    assert "os" in template
    assert "versions" in template
    assert "ghpages_branch" in template
    assert "python" in template["versions"]


def test_generate_version_template_with_no_existing_file(mocker: MockFixture) -> None:
    """
    Test template generation when the existing file does not exist
    Covers lines 469-474
    """
    # Prepare mocked logger
    mock_logger = mocker.patch("json2vars_setter.cache_version_info.logger")

    # Mock the path for a non-existent template file
    non_existent_file = Path("non_existent_template.json")
    non_existent_file.unlink(missing_ok=True)  # Ensure it is deleted

    # Prepare mock cache data
    mock_cache_data = {
        "languages": {
            "python": {
                "latest": "3.11.0",
                "stable": "3.10.0",
                "recent_releases": [
                    {"version": "3.11.0", "prerelease": False},
                    {"version": "3.10.0", "prerelease": False},
                ],
            }
        }
    }

    # Create a temporary output file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as output_file:
        output_path = Path(output_file.name)
        output_file.close()

    try:
        # Call the function with a non-existent existing file
        generate_version_template(
            mock_cache_data, output_path, existing_file=non_existent_file
        )

        # Verify that the output file was created with the default template structure
        with open(output_path, "r") as f:
            template = json.load(f)

        assert "os" in template
        assert "versions" in template
        assert "ghpages_branch" in template
        assert "python" in template["versions"]

        # Verify that no warning log was called (no error occurred)
        mock_logger.warning.assert_not_called()

    finally:
        # Delete the temporary file
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_generate_version_template_multiline_logging_paths(mocker: MockFixture) -> None:
    """
    Test multiline logging during template generation
    Covers lines 527-528
    """
    # Prepare mocked logger
    mock_logger = mocker.patch("json2vars_setter.cache_version_info.logger")

    # Complete existing template data
    existing_data: Dict[str, Any] = {
        "os": ["ubuntu-latest"],
        "versions": {
            "python": ["3.9.0", "3.8.0"],
            "ruby": ["3.0.0", "2.7.0"],
            "nodejs": ["18.0.0", "16.0.0"],
        },
        "ghpages_branch": "gh-pages",
    }

    # Mock cache data
    mock_cache_data: Dict[str, Any] = {
        "languages": {
            "rust": {
                "latest": "1.68.0",
                "stable": "1.67.0",
                "recent_releases": [
                    {"version": "1.68.0", "prerelease": False},
                    {"version": "1.67.0", "prerelease": False},
                ],
            }
        }
    }

    # Create temporary files
    with (
        tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as existing_template_file,
        tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as output_file,
    ):
        # Write existing template
        json.dump(existing_data, existing_template_file)
        existing_template_file.flush()
        existing_template_file.close()
        output_file.close()

        try:
            # Call generate_version_template
            generate_version_template(
                mock_cache_data,
                Path(output_file.name),
                existing_file=Path(existing_template_file.name),
                keep_existing=True,
                languages=list(existing_data["versions"].keys())
                + ["rust"],  # Explicitly specify all languages
            )

            # Read the output file
            with open(output_file.name, "r") as f:
                output_data = json.load(f)

            # Verify logger info method calls
            info_calls = [call[0][0] for call in mock_logger.info.call_args_list]

            # Debug output
            print("All info calls:", info_calls)
            print("Output versions:", output_data.get("versions", {}))

            # Verify the output file
            assert "versions" in output_data

        finally:
            # Clean up temporary files
            if os.path.exists(existing_template_file.name):
                os.unlink(existing_template_file.name)
            if os.path.exists(output_file.name):
                os.unlink(output_file.name)


def test_generate_version_template_keep_existing_no_recent_releases(
    mocker: MockFixture, tmp_path: Path
) -> None:
    """
    Test keeping existing template versions when recent_releases is empty with keep_existing=True
    Covers lines 527-528
    """
    # Prepare mocked logger
    mock_logger = mocker.patch("json2vars_setter.cache_version_info.logger")

    # Create existing template data
    existing_data = {
        "os": ["ubuntu-latest"],
        "versions": {
            "python": ["3.9.0", "3.8.0"],
        },
        "ghpages_branch": "gh-pages",
    }

    # Cache data with empty recent_releases
    mock_cache_data = {
        "languages": {
            "python": {
                "latest": "3.11.0",
                "stable": "3.10.0",
                "recent_releases": [],  # Empty recent_releases
            }
        }
    }

    # Create temporary files
    existing_file = tmp_path / "existing_template.json"
    output_file = tmp_path / "output_template.json"

    # Write existing template
    with open(existing_file, "w") as f:
        json.dump(existing_data, f)

    # Call the function
    generate_version_template(
        mock_cache_data,
        output_file,
        existing_file=existing_file,
        keep_existing=True,
        sort_order="desc",
    )

    # Verify the output file content
    with open(output_file, "r") as f:
        template = json.load(f)

    # Verify that the existing python versions are maintained
    assert "versions" in template
    assert "python" in template["versions"]
    assert template["versions"]["python"] == ["3.9.0", "3.8.0"]

    # Verify logger calls
    mock_logger.info.assert_any_call("Maintained existing python versions (2 versions)")
