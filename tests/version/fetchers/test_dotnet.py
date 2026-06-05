from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.dotnet import (
    DotnetVersionFetcher,
    dotnet_filter_func,
)


@pytest.fixture
def dotnet_fetcher() -> DotnetVersionFetcher:
    """Fixture to create a DotnetVersionFetcher instance"""
    return DotnetVersionFetcher()


def test_init(dotnet_fetcher: DotnetVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert dotnet_fetcher.github_owner == "dotnet"
    assert dotnet_fetcher.github_repo == "sdk"


def test_is_stable_tag(dotnet_fetcher: DotnetVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    # Stable version tags
    stable_tags: List[JsonObject] = [
        {"name": "v8.0.100"},
        {"name": "v9.0.314"},
        {"name": "v10.0.300"},
    ]

    # Unstable / unrelated tags
    unstable_tags: List[JsonObject] = [
        {"name": "v11.0.100-preview.4.26230.115"},
        {"name": "v10.0.100-rc.1.25451.107"},
        {"name": "v8.0"},  # only two components
        {"name": "8.0.100"},  # missing v prefix
        {"name": ""},  # empty name
    ]

    # Test stable tags
    for tag in stable_tags:
        assert dotnet_fetcher._is_stable_tag(tag) is True

    # Test unstable tags
    for tag in unstable_tags:
        assert dotnet_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(dotnet_fetcher: DotnetVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    # Valid tag
    valid_tag: JsonObject = {
        "name": "v8.0.100",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = dotnet_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "8.0.100"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "v8.0.100"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    # Invalid tag (no name)
    with pytest.raises(ParseError):
        dotnet_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria(dotnet_fetcher: DotnetVersionFetcher) -> None:
    """Test _get_stability_criteria method (stable = previous major)"""
    # Prepare sample releases (newest first)
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="10.0.300"),
        ReleaseInfo(version="10.0.108"),
        ReleaseInfo(version="9.0.314"),
        ReleaseInfo(version="8.0.421"),
    ]

    latest, stable = dotnet_fetcher._get_stability_criteria(releases)

    assert latest.version == "10.0.300"
    assert stable.version == "9.0.314"

    # Case with single release
    single_release: List[ReleaseInfo] = [ReleaseInfo(version="10.0.300")]
    latest, stable = dotnet_fetcher._get_stability_criteria(single_release)

    assert latest.version == "10.0.300"
    assert stable.version == "10.0.300"

    # Empty releases case
    with pytest.raises(ValueError):
        dotnet_fetcher._get_stability_criteria([])


def test_dotnet_filter_func() -> None:
    """Test dotnet_filter_func with various tag names"""
    # Stable tags
    stable_tags: List[JsonObject] = [
        {"name": "v8.0.100"},
        {"name": "v9.0.314"},
        {"name": "v10.0.300"},
    ]

    # Unstable / unrelated tags
    unstable_tags: List[JsonObject] = [
        {"name": "v11.0.100-preview.4.26230.115"},
        {"name": "v10.0.100-rc.1.25451.107"},
        {"name": "v8.0"},
        {"name": "latest"},
        {"name": ""},
    ]

    # Test stable tags
    for tag in stable_tags:
        assert dotnet_filter_func(tag) is True

    # Test unstable tags
    for tag in unstable_tags:
        assert dotnet_filter_func(tag) is False


def test_fetch_versions_integration(
    dotnet_fetcher: DotnetVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """
    Test fetch_versions method with mocked API calls
    """
    # Prepare mock tags
    mock_tags: List[JsonObject] = [
        {
            "name": "v10.0.300",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/10.0.300",
            "zipball_url": "https://example.com/zipball/10.0.300",
        },
        {
            "name": "v9.0.314",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/9.0.314",
            "zipball_url": "https://example.com/zipball/9.0.314",
        },
    ]

    # Mock _get_github_tags method to return predefined tags
    mocker.patch.object(dotnet_fetcher, "_get_github_tags", return_value=mock_tags)

    # Fetch versions
    versions = dotnet_fetcher.fetch_versions(recent_count=2)

    # Validate results
    assert versions.latest == "10.0.300"
    assert versions.stable == "9.0.314"
    assert len(versions.recent_releases) == 2

    # Check details
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:dotnet/sdk"
    assert "latest_info" in versions.details
    assert "stable_info" in versions.details


def test_get_stability_criteria_invalid_latest_version(
    dotnet_fetcher: DotnetVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    # Mock logger
    mocker.patch.object(dotnet_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),  # latest does not match the semver regex
        ReleaseInfo(version="9.0.314"),
    ]

    latest, stable = dotnet_fetcher._get_stability_criteria(releases)

    # When latest cannot be parsed, it falls back to using latest as stable
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_previous_major(
    dotnet_fetcher: DotnetVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when no previous major version exists"""
    # Mock logger
    mocker.patch.object(dotnet_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="10.0.300"),
        ReleaseInfo(version="10.0.108"),  # Same major version
    ]

    latest, stable = dotnet_fetcher._get_stability_criteria(releases)

    assert latest.version == "10.0.300"
    assert stable.version == "10.0.300"  # Use latest as no previous major exists


def test_get_stability_criteria_invalid_release_version(
    dotnet_fetcher: DotnetVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    # Mock logger
    mocker.patch.object(dotnet_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="10.0.300"),
        ReleaseInfo(version="9.0.invalid"),  # Does not match regex, must be skipped
        ReleaseInfo(version="9.0.314"),
    ]

    latest, stable = dotnet_fetcher._get_stability_criteria(releases)

    assert latest.version == "10.0.300"
    assert stable.version == "9.0.314"  # Skip invalid and select correct stable version
