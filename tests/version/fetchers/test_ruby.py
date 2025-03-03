from typing import Any, Dict, List

import pytest
import pytest_mock

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import ReleaseInfo
from json2vars_setter.version.fetchers.ruby import RubyVersionFetcher, ruby_filter_func


@pytest.fixture
def ruby_fetcher() -> RubyVersionFetcher:
    """Fixture to create a RubyVersionFetcher instance"""
    return RubyVersionFetcher()


def test_is_stable_tag(ruby_fetcher: RubyVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    # Stable version tags
    stable_tags: List[Dict[str, Any]] = [
        {"name": "v3_9_0"},
        {"name": "v3_10_5"},
        {"name": "v4_0_0"},
    ]

    # Unstable version tags
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "v3_9_0rc1"},
        {"name": "v3_10_5b2"},
        {"name": "v4_0_0a1"},
        {"name": "v3_9_0beta"},
        {"name": "v3_10_5pre"},
        {"name": "v3_9_0alpha"},
        {"name": "v3_10_5dev"},
        {"name": "v4_0_0snapshot"},
    ]

    # Test stable tags
    for tag in stable_tags:
        assert ruby_fetcher._is_stable_tag(tag) is True

    # Test unstable tags
    for tag in unstable_tags:
        assert ruby_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(ruby_fetcher: RubyVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    # Valid tag
    valid_tag: Dict[str, Any] = {
        "name": "v3_9_2",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = ruby_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "3.9.2"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "v3_9_2"
    assert release_info.additional_info["commit"]["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    # Invalid tag (no name)
    with pytest.raises(ParseError):
        ruby_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria(ruby_fetcher: RubyVersionFetcher) -> None:
    """Test _get_stability_criteria method"""
    # Prepare sample releases
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="3.12.0"),
        ReleaseInfo(version="3.11.5"),
        ReleaseInfo(version="3.10.3"),
        ReleaseInfo(version="3.9.7"),
    ]

    latest, stable = ruby_fetcher._get_stability_criteria(releases)

    assert latest.version == "3.12.0"
    assert stable.version == "3.11.5"

    # Case with single release
    single_release: List[ReleaseInfo] = [ReleaseInfo(version="3.12.0")]
    latest, stable = ruby_fetcher._get_stability_criteria(single_release)

    assert latest.version == "3.12.0"
    assert stable.version == "3.12.0"

    # Empty releases case
    with pytest.raises(ValueError):
        ruby_fetcher._get_stability_criteria([])


def test_ruby_filter_func() -> None:
    """Test ruby_filter_func with various tag names"""
    # Stable tags
    stable_tags: List[Dict[str, Any]] = [
        {"name": "v3_9_0"},
        {"name": "v4_0_1"},
        {"name": "v3_10_5"},
    ]

    # Unstable tags
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "v3_9_0rc1"},
        {"name": "v3_10_5b2"},
        {"name": "v4_0_0a1"},
        {"name": "v3_9_0beta"},
        {"name": "v3_10_5pre"},
        {"name": "v3_9_0alpha"},
        {"name": "v3_10_5dev"},
        {"name": "v4_0_0snapshot"},
        {"name": "latest"},  # Not starting with v or no underscore
        {"name": ""},  # Empty name
    ]

    # Test stable tags
    for tag in stable_tags:
        assert ruby_filter_func(tag) is True

    # Test unstable tags
    for tag in unstable_tags:
        assert ruby_filter_func(tag) is False


def test_fetch_versions_integration(
    ruby_fetcher: RubyVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """
    Test fetch_versions method with mocked API calls
    """
    # Prepare mock tags
    mock_tags: List[Dict[str, Any]] = [
        {
            "name": "v3_12_0",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/3.12.0",
            "zipball_url": "https://example.com/zipball/3.12.0",
        },
        {
            "name": "v3_11_5",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/3.11.5",
            "zipball_url": "https://example.com/zipball/3.11.5",
        },
    ]

    # Mock _get_github_tags method to return predefined tags
    mocker.patch.object(ruby_fetcher, "_get_github_tags", return_value=mock_tags)

    # Fetch versions
    versions = ruby_fetcher.fetch_versions(recent_count=2)

    # Validate results
    assert versions.latest == "3.12.0"
    assert versions.stable == "3.11.5"
    assert len(versions.recent_releases) == 2

    # Check details
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:ruby/ruby"
    assert "latest_info" in versions.details
    assert "stable_info" in versions.details


# 既存の test_get_stability_criteria に追加する形で拡張


def test_get_stability_criteria_invalid_version_format(
    ruby_fetcher: RubyVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with invalid version format"""
    # Mock logger
    mocker.patch.object(ruby_fetcher, "logger", mocker.Mock())

    # Prepare releases with invalid version format, simulating _parse_version_from_tag
    releases = [
        ruby_fetcher._parse_version_from_tag(
            {"name": "v_invalid_version"}
        ),  # Will become "invalid.version"
        ruby_fetcher._parse_version_from_tag(
            {"name": "v3_11_5"}
        ),  # Will become "3.11.5"
    ]

    # Execute method
    latest, stable = ruby_fetcher._get_stability_criteria(releases)

    # Verify results
    assert (
        latest.version == "invalid.version"
    )  # Match the result of _parse_version_from_tag
    assert stable.version == "invalid.version"  # If match fails, latest becomes stable


def test_get_stability_criteria_no_previous_minor(
    ruby_fetcher: RubyVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when no previous minor version exists"""
    # Mock logger
    mocker.patch.object(ruby_fetcher, "logger", mocker.Mock())

    # Prepare releases with no previous minor version match
    releases = [
        ReleaseInfo(version="3.12.0"),
        ReleaseInfo(version="3.12.1"),  # Same minor version
        ReleaseInfo(version="2.11.5"),  # Different major version
    ]

    # Execute method
    latest, stable = ruby_fetcher._get_stability_criteria(releases)

    # Verify results
    assert latest.version == "3.12.0"
    assert stable.version == "3.12.0"  # Use latest as no previous minor version exists


def test_get_stability_criteria_invalid_release_version(
    ruby_fetcher: RubyVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with invalid version in releases list"""
    # Mock logger
    mocker.patch.object(ruby_fetcher, "logger", mocker.Mock())

    # Prepare releases where a release has an invalid version format
    releases = [
        ReleaseInfo(version="3.12.0"),
        ReleaseInfo(version="3.11.invalid"),  # Does not match regex
        ReleaseInfo(version="3.11.5"),
    ]

    # Execute method
    latest, stable = ruby_fetcher._get_stability_criteria(releases)

    # Verify results
    assert latest.version == "3.12.0"
    assert stable.version == "3.11.5"  # Skip invalid and select correct stable version
