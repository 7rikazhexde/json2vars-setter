from typing import Any, Dict, List

import pytest
import pytest_mock

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import ReleaseInfo
from json2vars_setter.version.fetchers.python import (
    PythonVersionFetcher,
    python_filter_func,
)


@pytest.fixture
def python_fetcher() -> PythonVersionFetcher:
    """Fixture to create a PythonVersionFetcher instance"""
    return PythonVersionFetcher()


def test_is_stable_tag(python_fetcher: PythonVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    # Stable version tags
    stable_tags: List[Dict[str, Any]] = [
        {"name": "v3.9.0"},
        {"name": "v3.10.5"},
        {"name": "v4.0.0"},
    ]

    # Unstable version tags
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "v3.9.0rc1"},
        {"name": "v3.10.5b2"},
        {"name": "v4.0.0a1"},
        {"name": "v3.9.0beta"},
        {"name": "v3.10.5pre"},
    ]

    # Test stable tags
    for tag in stable_tags:
        assert python_fetcher._is_stable_tag(tag) is True

    # Test unstable tags
    for tag in unstable_tags:
        assert python_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(python_fetcher: PythonVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    # Valid tag
    valid_tag: Dict[str, Any] = {
        "name": "v3.9.2",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = python_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "3.9.2"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "v3.9.2"
    assert release_info.additional_info["commit"]["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    # Invalid tag (no name)
    with pytest.raises(ParseError):
        python_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria(python_fetcher: PythonVersionFetcher) -> None:
    """Test _get_stability_criteria method"""
    # Prepare sample releases
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="3.12.0"),
        ReleaseInfo(version="3.11.5"),
        ReleaseInfo(version="3.10.3"),
        ReleaseInfo(version="3.9.7"),
    ]

    latest, stable = python_fetcher._get_stability_criteria(releases)

    assert latest.version == "3.12.0"
    assert stable.version == "3.11.5"

    # Case with single release
    single_release: List[ReleaseInfo] = [ReleaseInfo(version="3.12.0")]
    latest, stable = python_fetcher._get_stability_criteria(single_release)

    assert latest.version == "3.12.0"
    assert stable.version == "3.12.0"

    # Empty releases case
    with pytest.raises(ValueError):
        python_fetcher._get_stability_criteria([])


def test_python_filter_func() -> None:
    """Test python_filter_func with various tag names"""
    # Stable tags
    stable_tags: List[Dict[str, Any]] = [
        {"name": "v3.9.0"},
        {"name": "v4.0.1"},
        {"name": "v3.10.5"},
    ]

    # Unstable tags
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "v3.9.0rc1"},
        {"name": "v3.10.5b2"},
        {"name": "v4.0.0a1"},
        {"name": "v3.9.0beta"},
        {"name": "v3.10.5pre"},
        {"name": "latest"},  # Not starting with v3 or v4
        {"name": ""},  # Empty name
    ]

    # Test stable tags
    for tag in stable_tags:
        assert python_filter_func(tag) is True

    # Test unstable tags
    for tag in unstable_tags:
        assert python_filter_func(tag) is False


def test_fetch_versions_integration(
    python_fetcher: PythonVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """
    Test fetch_versions method with mocked API calls

    Note: This is an integration-style test that mocks the GitHub API calls
    """
    # Prepare mock tags
    mock_tags: List[Dict[str, Any]] = [
        {
            "name": "v3.12.0",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/3.12.0",
            "zipball_url": "https://example.com/zipball/3.12.0",
        },
        {
            "name": "v3.11.5",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/3.11.5",
            "zipball_url": "https://example.com/zipball/3.11.5",
        },
    ]

    # Mock _get_github_tags method to return predefined tags
    mocker.patch.object(python_fetcher, "_get_github_tags", return_value=mock_tags)

    # Fetch versions
    versions = python_fetcher.fetch_versions(recent_count=2)

    # Validate results
    assert versions.latest == "3.12.0"
    assert versions.stable == "3.11.5"
    assert len(versions.recent_releases) == 2

    # Check details
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:python/cpython"
    assert "latest_info" in versions.details
    assert "stable_info" in versions.details
