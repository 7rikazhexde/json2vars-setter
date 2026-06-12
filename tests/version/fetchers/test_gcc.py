from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.gcc import GccVersionFetcher, gcc_filter_func


@pytest.fixture
def gcc_fetcher() -> GccVersionFetcher:
    """Fixture to create a GccVersionFetcher instance"""
    return GccVersionFetcher()


def test_init(gcc_fetcher: GccVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert gcc_fetcher.github_owner == "gcc-mirror"
    assert gcc_fetcher.github_repo == "gcc"


def test_is_stable_tag(gcc_fetcher: GccVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "releases/gcc-16.1.0"},
        {"name": "releases/gcc-15.3.0"},
        {"name": "releases/gcc-14.2.0"},
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "releases/libgcj-2.95.1"},  # libgcj, not gcc
        {"name": "releases/libf2c-0.5.22"},  # libf2c
        {"name": "vendors/ARM/release-12.3.rel1"},  # vendor branch
        {"name": "basepoints/gcc-15"},  # basepoint marker
        {"name": "releases/gcc-15.1"},  # missing patch component
        {"name": "gcc-15.1.0"},  # missing the "releases/" prefix
        {"name": ""},
    ]

    for tag in stable_tags:
        assert gcc_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert gcc_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(gcc_fetcher: GccVersionFetcher) -> None:
    """Test _parse_version_from_tag extracts the version from the release tag"""
    valid_tag: JsonObject = {
        "name": "releases/gcc-15.1.0",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = gcc_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "15.1.0"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "releases/gcc-15.1.0"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError):
        gcc_fetcher._parse_version_from_tag({"name": ""})

    # A non-release tag name cannot be parsed
    with pytest.raises(ParseError):
        gcc_fetcher._parse_version_from_tag({"name": "vendors/ARM/release-12.3.rel1"})


def test_version_sort_key(gcc_fetcher: GccVersionFetcher) -> None:
    """Test _version_sort_key builds a numeric (major, minor, patch) key"""
    assert gcc_fetcher._version_sort_key({"name": "releases/gcc-16.1.0"}) == (16, 1, 0)
    assert gcc_fetcher._version_sort_key({"name": "releases/gcc-9.5.0"}) == (9, 5, 0)


def test_get_github_tags_sorts_and_truncates(
    gcc_fetcher: GccVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_github_tags sorts by semantic version and truncates"""
    # Unsorted, mimicking the unreliable gcc-mirror/gcc tag order
    unsorted_tags: List[JsonObject] = [
        {"name": "releases/gcc-14.2.0"},
        {"name": "releases/gcc-16.1.0"},
        {"name": "releases/gcc-15.1.0"},
        {"name": "releases/gcc-15.3.0"},
    ]
    mocker.patch.object(
        BaseVersionFetcher, "_get_github_tags", return_value=unsorted_tags
    )

    top_two = gcc_fetcher._get_github_tags(2)
    assert [str(tag["name"]) for tag in top_two] == [
        "releases/gcc-16.1.0",
        "releases/gcc-15.3.0",
    ]

    all_tags = gcc_fetcher._get_github_tags()
    assert [str(tag["name"]) for tag in all_tags] == [
        "releases/gcc-16.1.0",
        "releases/gcc-15.3.0",
        "releases/gcc-15.1.0",
        "releases/gcc-14.2.0",
    ]


def test_get_stability_criteria_previous_major(
    gcc_fetcher: GccVersionFetcher,
) -> None:
    """Test _get_stability_criteria picks latest and the previous major series"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="16.1.0"),
        ReleaseInfo(version="15.3.0"),
        ReleaseInfo(version="15.2.0"),
    ]

    latest, stable = gcc_fetcher._get_stability_criteria(releases)
    assert latest.version == "16.1.0"
    assert stable.version == "15.3.0"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="16.1.0")]
    latest, stable = gcc_fetcher._get_stability_criteria(single_release)
    assert latest.version == "16.1.0"
    assert stable.version == "16.1.0"

    with pytest.raises(ValueError):
        gcc_fetcher._get_stability_criteria([])


def test_get_stability_criteria_skips_same_major(
    gcc_fetcher: GccVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Stable is the previous MAJOR series, not the previous minor of the same major."""
    mocker.patch.object(gcc_fetcher, "logger", mocker.Mock())

    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="15.3.0"),
        ReleaseInfo(version="15.2.0"),  # same major (15) -> skipped
        ReleaseInfo(version="14.3.0"),
    ]
    latest, stable = gcc_fetcher._get_stability_criteria(releases)
    assert latest.version == "15.3.0"
    assert stable.version == "14.3.0"


def test_gcc_filter_func() -> None:
    """Test gcc_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "releases/gcc-16.1.0"},
        {"name": "releases/gcc-15.3.0"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "releases/libgcj-2.95.1"},
        {"name": "vendors/ARM/release-12.3.rel1"},
        {"name": "releases/gcc-15.1"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert gcc_filter_func(tag) is True
    for tag in unstable_tags:
        assert gcc_filter_func(tag) is False


def test_fetch_versions_integration(
    gcc_fetcher: GccVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "releases/gcc-16.1.0",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/16.1.0",
            "zipball_url": "https://example.com/zipball/16.1.0",
        },
        {
            "name": "releases/gcc-15.3.0",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/15.3.0",
            "zipball_url": "https://example.com/zipball/15.3.0",
        },
    ]

    mocker.patch.object(gcc_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = gcc_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "16.1.0"
    assert versions.stable == "15.3.0"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:gcc-mirror/gcc"


def test_get_stability_criteria_invalid_latest_version(
    gcc_fetcher: GccVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(gcc_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="15.3.0"),
    ]
    latest, stable = gcc_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_other_major(
    gcc_fetcher: GccVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when every release shares the major series"""
    mocker.patch.object(gcc_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="15.3.0"),
        ReleaseInfo(version="15.2.0"),  # same major
    ]
    latest, stable = gcc_fetcher._get_stability_criteria(releases)
    assert latest.version == "15.3.0"
    assert stable.version == "15.3.0"


def test_get_stability_criteria_invalid_release_version(
    gcc_fetcher: GccVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(gcc_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="16.1.0"),
        ReleaseInfo(version="15.invalid"),  # skipped
        ReleaseInfo(version="15.3.0"),
    ]
    latest, stable = gcc_fetcher._get_stability_criteria(releases)
    assert latest.version == "16.1.0"
    assert stable.version == "15.3.0"
