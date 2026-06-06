from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.haskell import (
    HaskellVersionFetcher,
    haskell_filter_func,
)


@pytest.fixture
def haskell_fetcher() -> HaskellVersionFetcher:
    """Fixture to create a HaskellVersionFetcher instance"""
    return HaskellVersionFetcher()


def test_init(haskell_fetcher: HaskellVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert haskell_fetcher.github_owner == "ghc"
    assert haskell_fetcher.github_repo == "ghc"


def test_is_stable_tag(haskell_fetcher: HaskellVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "ghc-9.10.1-release"},
        {"name": "ghc-9.8.4-release"},
        {"name": "ghc-9.14.1-release"},
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "ghc-9.14.1-rc1"},  # release candidate
        {"name": "ghc-9.14.1-alpha1"},  # alpha
        {"name": "ghc-9.15-start"},  # branch marker
        {"name": "wip/ghc-8.6.5"},  # work in progress
        {"name": "9.10.1"},  # missing ghc- prefix / -release suffix
        {"name": ""},
    ]

    for tag in stable_tags:
        assert haskell_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert haskell_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(haskell_fetcher: HaskellVersionFetcher) -> None:
    """Test _parse_version_from_tag extracts the version from the release tag"""
    valid_tag: JsonObject = {
        "name": "ghc-9.10.1-release",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = haskell_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "9.10.1"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "ghc-9.10.1-release"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError):
        haskell_fetcher._parse_version_from_tag({"name": ""})

    # A non-release tag name cannot be parsed
    with pytest.raises(ParseError):
        haskell_fetcher._parse_version_from_tag({"name": "ghc-9.15-start"})


def test_version_sort_key(haskell_fetcher: HaskellVersionFetcher) -> None:
    """Test _version_sort_key builds a numeric (major, minor, patch) key"""
    assert haskell_fetcher._version_sort_key({"name": "ghc-9.10.1-release"}) == (
        9,
        10,
        1,
    )
    assert haskell_fetcher._version_sort_key({"name": "ghc-9.8.4-release"}) == (9, 8, 4)


def test_get_github_tags_sorts_and_truncates(
    haskell_fetcher: HaskellVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_github_tags sorts by semantic version and truncates"""
    # Unsorted, mimicking the unreliable ghc/ghc tag order
    unsorted_tags: List[JsonObject] = [
        {"name": "ghc-9.8.4-release"},
        {"name": "ghc-9.14.1-release"},
        {"name": "ghc-9.10.1-release"},
        {"name": "ghc-9.12.2-release"},
    ]
    mocker.patch.object(
        BaseVersionFetcher, "_get_github_tags", return_value=unsorted_tags
    )

    top_two = haskell_fetcher._get_github_tags(2)
    assert [str(tag["name"]) for tag in top_two] == [
        "ghc-9.14.1-release",
        "ghc-9.12.2-release",
    ]

    all_tags = haskell_fetcher._get_github_tags()
    assert [str(tag["name"]) for tag in all_tags] == [
        "ghc-9.14.1-release",
        "ghc-9.12.2-release",
        "ghc-9.10.1-release",
        "ghc-9.8.4-release",
    ]


def test_get_stability_criteria(haskell_fetcher: HaskellVersionFetcher) -> None:
    """Test _get_stability_criteria picks latest and the previous minor line"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="9.14.1"),
        ReleaseInfo(version="9.12.2"),
        ReleaseInfo(version="9.12.1"),
    ]

    latest, stable = haskell_fetcher._get_stability_criteria(releases)
    assert latest.version == "9.14.1"
    assert stable.version == "9.12.2"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="9.14.1")]
    latest, stable = haskell_fetcher._get_stability_criteria(single_release)
    assert latest.version == "9.14.1"
    assert stable.version == "9.14.1"

    with pytest.raises(ValueError):
        haskell_fetcher._get_stability_criteria([])


def test_haskell_filter_func() -> None:
    """Test haskell_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "ghc-9.10.1-release"},
        {"name": "ghc-9.8.4-release"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "ghc-9.14.1-rc1"},
        {"name": "ghc-9.15-start"},
        {"name": "wip/ghc-8.6.5"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert haskell_filter_func(tag) is True
    for tag in unstable_tags:
        assert haskell_filter_func(tag) is False


def test_fetch_versions_integration(
    haskell_fetcher: HaskellVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "ghc-9.14.1-release",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/9.14.1",
            "zipball_url": "https://example.com/zipball/9.14.1",
        },
        {
            "name": "ghc-9.12.2-release",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/9.12.2",
            "zipball_url": "https://example.com/zipball/9.12.2",
        },
    ]

    mocker.patch.object(haskell_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = haskell_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "9.14.1"
    assert versions.stable == "9.12.2"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:ghc/ghc"


def test_get_stability_criteria_invalid_latest_version(
    haskell_fetcher: HaskellVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(haskell_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="9.12.2"),
    ]
    latest, stable = haskell_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_other_minor(
    haskell_fetcher: HaskellVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when every release shares the minor line"""
    mocker.patch.object(haskell_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="9.14.1"),
        ReleaseInfo(version="9.14.0"),  # same minor
    ]
    latest, stable = haskell_fetcher._get_stability_criteria(releases)
    assert latest.version == "9.14.1"
    assert stable.version == "9.14.1"


def test_get_stability_criteria_invalid_release_version(
    haskell_fetcher: HaskellVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(haskell_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="9.14.1"),
        ReleaseInfo(version="9.12.invalid"),  # skipped
        ReleaseInfo(version="9.12.2"),
    ]
    latest, stable = haskell_fetcher._get_stability_criteria(releases)
    assert latest.version == "9.14.1"
    assert stable.version == "9.12.2"
