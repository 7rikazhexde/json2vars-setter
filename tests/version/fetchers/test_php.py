from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.php import PhpVersionFetcher, php_filter_func


@pytest.fixture
def php_fetcher() -> PhpVersionFetcher:
    """Fixture to create a PhpVersionFetcher instance"""
    return PhpVersionFetcher()


def test_init(php_fetcher: PhpVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert php_fetcher.github_owner == "php"
    assert php_fetcher.github_repo == "php-src"


def test_is_stable_tag(php_fetcher: PhpVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    # Stable version tags
    stable_tags: List[JsonObject] = [
        {"name": "php-8.3.0"},
        {"name": "php-8.4.1"},
        {"name": "php-7.4.33"},
    ]

    # Unstable / unrelated tags
    unstable_tags: List[JsonObject] = [
        {"name": "php-8.5.0RC1"},
        {"name": "php-8.5.0beta1"},
        {"name": "php-8.5.0alpha2"},
        {"name": "yaf-2.1.0"},  # unrelated project tag
        {"name": "security-audit-2024"},
        {"name": "php-8.4"},  # only two components
        {"name": ""},  # empty name
    ]

    # Test stable tags
    for tag in stable_tags:
        assert php_fetcher._is_stable_tag(tag) is True

    # Test unstable tags
    for tag in unstable_tags:
        assert php_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(php_fetcher: PhpVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    # Valid tag
    valid_tag: JsonObject = {
        "name": "php-8.3.2",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = php_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "8.3.2"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "php-8.3.2"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    # Invalid tag (no name)
    with pytest.raises(ParseError):
        php_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria(php_fetcher: PhpVersionFetcher) -> None:
    """Test _get_stability_criteria method"""
    # Prepare sample releases
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="8.4.1"),
        ReleaseInfo(version="8.3.6"),
        ReleaseInfo(version="8.2.15"),
        ReleaseInfo(version="8.1.27"),
    ]

    latest, stable = php_fetcher._get_stability_criteria(releases)

    assert latest.version == "8.4.1"
    assert stable.version == "8.3.6"

    # Case with single release
    single_release: List[ReleaseInfo] = [ReleaseInfo(version="8.4.1")]
    latest, stable = php_fetcher._get_stability_criteria(single_release)

    assert latest.version == "8.4.1"
    assert stable.version == "8.4.1"

    # Empty releases case
    with pytest.raises(ValueError):
        php_fetcher._get_stability_criteria([])


def test_php_filter_func() -> None:
    """Test php_filter_func with various tag names"""
    # Stable tags
    stable_tags: List[JsonObject] = [
        {"name": "php-8.3.0"},
        {"name": "php-8.4.1"},
        {"name": "php-7.4.33"},
    ]

    # Unstable / unrelated tags
    unstable_tags: List[JsonObject] = [
        {"name": "php-8.5.0RC1"},
        {"name": "php-8.5.0beta1"},
        {"name": "php-8.5.0alpha2"},
        {"name": "yaf-2.1.0"},
        {"name": "security-audit-2024"},
        {"name": "php-8.4"},
        {"name": "latest"},
        {"name": ""},
    ]

    # Test stable tags
    for tag in stable_tags:
        assert php_filter_func(tag) is True

    # Test unstable tags
    for tag in unstable_tags:
        assert php_filter_func(tag) is False


def test_fetch_versions_integration(
    php_fetcher: PhpVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """
    Test fetch_versions method with mocked API calls
    """
    # Prepare mock tags
    mock_tags: List[JsonObject] = [
        {
            "name": "php-8.4.1",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/8.4.1",
            "zipball_url": "https://example.com/zipball/8.4.1",
        },
        {
            "name": "php-8.3.6",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/8.3.6",
            "zipball_url": "https://example.com/zipball/8.3.6",
        },
    ]

    # Mock _get_github_tags method to return predefined tags
    mocker.patch.object(php_fetcher, "_get_github_tags", return_value=mock_tags)

    # Fetch versions
    versions = php_fetcher.fetch_versions(recent_count=2)

    # Validate results
    assert versions.latest == "8.4.1"
    assert versions.stable == "8.3.6"
    assert len(versions.recent_releases) == 2

    # Check details
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:php/php-src"
    assert "latest_info" in versions.details
    assert "stable_info" in versions.details


def test_get_stability_criteria_invalid_latest_version(
    php_fetcher: PhpVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    # Mock logger
    mocker.patch.object(php_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),  # latest does not match the semver regex
        ReleaseInfo(version="8.3.6"),
    ]

    latest, stable = php_fetcher._get_stability_criteria(releases)

    # When latest cannot be parsed, it falls back to using latest as stable
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_previous_minor(
    php_fetcher: PhpVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when no previous minor version exists"""
    # Mock logger
    mocker.patch.object(php_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="8.4.0"),
        ReleaseInfo(version="8.4.1"),  # Same minor version
        ReleaseInfo(version="7.4.33"),  # Different major version
    ]

    latest, stable = php_fetcher._get_stability_criteria(releases)

    assert latest.version == "8.4.0"
    assert stable.version == "8.4.0"  # Use latest as no previous minor version exists


def test_get_stability_criteria_invalid_release_version(
    php_fetcher: PhpVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    # Mock logger
    mocker.patch.object(php_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="8.4.1"),
        ReleaseInfo(version="8.3.invalid"),  # Does not match regex, must be skipped
        ReleaseInfo(version="8.3.6"),
    ]

    latest, stable = php_fetcher._get_stability_criteria(releases)

    assert latest.version == "8.4.1"
    assert stable.version == "8.3.6"  # Skip invalid and select correct stable version
