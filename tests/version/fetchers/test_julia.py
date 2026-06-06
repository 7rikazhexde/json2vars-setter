from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.julia import (
    JuliaVersionFetcher,
    julia_filter_func,
)


@pytest.fixture
def julia_fetcher() -> JuliaVersionFetcher:
    """Fixture to create a JuliaVersionFetcher instance"""
    return JuliaVersionFetcher()


def test_init(julia_fetcher: JuliaVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert julia_fetcher.github_owner == "JuliaLang"
    assert julia_fetcher.github_repo == "julia"


def test_is_stable_tag(julia_fetcher: JuliaVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "v1.11.2"},
        {"name": "v1.12.6"},
        {"name": "v1.0.0"},
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "v1.13.0-rc1"},  # release candidate
        {"name": "v1.13.0-beta3"},  # beta
        {"name": "v1.13.0-alpha1"},  # alpha
        {"name": "v1.11"},  # only two components
        {"name": "1.11.2"},  # missing prefix
        {"name": ""},
    ]

    for tag in stable_tags:
        assert julia_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert julia_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(julia_fetcher: JuliaVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    valid_tag: JsonObject = {
        "name": "v1.12.6",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = julia_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "1.12.6"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "v1.12.6"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError):
        julia_fetcher._parse_version_from_tag({"name": ""})


def test_version_sort_key(julia_fetcher: JuliaVersionFetcher) -> None:
    """Test _version_sort_key builds a numeric (major, minor, patch) key"""
    assert julia_fetcher._version_sort_key({"name": "v1.12.6"}) == (1, 12, 6)
    assert julia_fetcher._version_sort_key({"name": "v1.11.2"}) == (1, 11, 2)


def test_get_github_tags_sorts_and_truncates(
    julia_fetcher: JuliaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_github_tags sorts by semantic version and truncates"""
    # Deliberately unsorted, mimicking the unreliable GitHub tag order
    unsorted_tags: List[JsonObject] = [
        {"name": "v1.11.2"},
        {"name": "v1.12.6"},
        {"name": "v1.10.9"},
        {"name": "v1.12.5"},
    ]
    mocker.patch.object(
        BaseVersionFetcher, "_get_github_tags", return_value=unsorted_tags
    )

    # Truncated request returns the newest versions in descending order
    top_two = julia_fetcher._get_github_tags(2)
    assert [str(tag["name"]) for tag in top_two] == ["v1.12.6", "v1.12.5"]

    # Default (count=None -> 5) returns everything, still sorted
    all_tags = julia_fetcher._get_github_tags()
    assert [str(tag["name"]) for tag in all_tags] == [
        "v1.12.6",
        "v1.12.5",
        "v1.11.2",
        "v1.10.9",
    ]


def test_get_stability_criteria(julia_fetcher: JuliaVersionFetcher) -> None:
    """Test _get_stability_criteria picks latest and the previous minor line"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="1.12.6"),
        ReleaseInfo(version="1.12.5"),
        ReleaseInfo(version="1.11.6"),
    ]

    latest, stable = julia_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.12.6"
    assert stable.version == "1.11.6"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="1.12.6")]
    latest, stable = julia_fetcher._get_stability_criteria(single_release)
    assert latest.version == "1.12.6"
    assert stable.version == "1.12.6"

    with pytest.raises(ValueError):
        julia_fetcher._get_stability_criteria([])


def test_julia_filter_func() -> None:
    """Test julia_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "v1.11.2"},
        {"name": "v1.12.6"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "v1.13.0-rc1"},
        {"name": "v1.13.0-beta3"},
        {"name": "v1.11"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert julia_filter_func(tag) is True
    for tag in unstable_tags:
        assert julia_filter_func(tag) is False


def test_fetch_versions_integration(
    julia_fetcher: JuliaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "v1.12.6",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/1.12.6",
            "zipball_url": "https://example.com/zipball/1.12.6",
        },
        {
            "name": "v1.11.6",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/1.11.6",
            "zipball_url": "https://example.com/zipball/1.11.6",
        },
    ]

    mocker.patch.object(julia_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = julia_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "1.12.6"
    assert versions.stable == "1.11.6"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:JuliaLang/julia"


def test_get_stability_criteria_invalid_latest_version(
    julia_fetcher: JuliaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(julia_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="1.11.6"),
    ]
    latest, stable = julia_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_other_minor(
    julia_fetcher: JuliaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when every release shares the minor line"""
    mocker.patch.object(julia_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="1.12.6"),
        ReleaseInfo(version="1.12.5"),  # same minor
    ]
    latest, stable = julia_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.12.6"
    assert stable.version == "1.12.6"


def test_get_stability_criteria_invalid_release_version(
    julia_fetcher: JuliaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(julia_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="1.12.6"),
        ReleaseInfo(version="1.11.invalid"),  # skipped
        ReleaseInfo(version="1.11.6"),
    ]
    latest, stable = julia_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.12.6"
    assert stable.version == "1.11.6"
