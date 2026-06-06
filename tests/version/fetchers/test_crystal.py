from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.crystal import (
    CrystalVersionFetcher,
    crystal_filter_func,
)


@pytest.fixture
def crystal_fetcher() -> CrystalVersionFetcher:
    """Fixture to create a CrystalVersionFetcher instance"""
    return CrystalVersionFetcher()


def test_init(crystal_fetcher: CrystalVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert crystal_fetcher.github_owner == "crystal-lang"
    assert crystal_fetcher.github_repo == "crystal"


def test_is_stable_tag(crystal_fetcher: CrystalVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "1.20.2"},  # current form (no prefix)
        {"name": "v1.17.1"},  # older form (v prefix)
        {"name": "v0.24.1"},  # ancient release
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "ruby"},  # junk tag
        {"name": "test-ci-1"},  # junk tag
        {"name": "1.20"},  # only two components
        {"name": "1.20.0-pre1"},  # pre-release suffix
        {"name": ""},
    ]

    for tag in stable_tags:
        assert crystal_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert crystal_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(crystal_fetcher: CrystalVersionFetcher) -> None:
    """Test _parse_version_from_tag method strips an optional v prefix"""
    valid_tag: JsonObject = {
        "name": "v1.17.1",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = crystal_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "1.17.1"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "v1.17.1"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    # The current (prefix-less) form is returned unchanged
    no_prefix: JsonObject = {"name": "1.20.2"}
    assert crystal_fetcher._parse_version_from_tag(no_prefix).version == "1.20.2"

    with pytest.raises(ParseError):
        crystal_fetcher._parse_version_from_tag({"name": ""})


def test_version_sort_key(crystal_fetcher: CrystalVersionFetcher) -> None:
    """Test _version_sort_key normalizes both tag forms to a numeric key"""
    assert crystal_fetcher._version_sort_key({"name": "1.20.2"}) == (1, 20, 2)
    assert crystal_fetcher._version_sort_key({"name": "v1.17.1"}) == (1, 17, 1)


def test_get_github_tags_sorts_and_truncates(
    crystal_fetcher: CrystalVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_github_tags sorts by semantic version and truncates"""
    # Mixed forms and unsorted, mimicking the real crystal-lang/crystal tag order
    unsorted_tags: List[JsonObject] = [
        {"name": "v1.17.1"},
        {"name": "v0.24.1"},
        {"name": "1.20.2"},
        {"name": "1.19.2"},
    ]
    mocker.patch.object(
        BaseVersionFetcher, "_get_github_tags", return_value=unsorted_tags
    )

    top_two = crystal_fetcher._get_github_tags(2)
    assert [str(tag["name"]) for tag in top_two] == ["1.20.2", "1.19.2"]

    all_tags = crystal_fetcher._get_github_tags()
    assert [str(tag["name"]) for tag in all_tags] == [
        "1.20.2",
        "1.19.2",
        "v1.17.1",
        "v0.24.1",
    ]


def test_get_stability_criteria(crystal_fetcher: CrystalVersionFetcher) -> None:
    """Test _get_stability_criteria picks latest and the previous minor line"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="1.20.2"),
        ReleaseInfo(version="1.20.1"),
        ReleaseInfo(version="1.19.2"),
    ]

    latest, stable = crystal_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.20.2"
    assert stable.version == "1.19.2"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="1.20.2")]
    latest, stable = crystal_fetcher._get_stability_criteria(single_release)
    assert latest.version == "1.20.2"
    assert stable.version == "1.20.2"

    with pytest.raises(ValueError):
        crystal_fetcher._get_stability_criteria([])


def test_crystal_filter_func() -> None:
    """Test crystal_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "1.20.2"},
        {"name": "v1.17.1"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "ruby"},
        {"name": "test-ci-1"},
        {"name": "1.20"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert crystal_filter_func(tag) is True
    for tag in unstable_tags:
        assert crystal_filter_func(tag) is False


def test_fetch_versions_integration(
    crystal_fetcher: CrystalVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "1.20.2",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/1.20.2",
            "zipball_url": "https://example.com/zipball/1.20.2",
        },
        {
            "name": "1.19.2",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/1.19.2",
            "zipball_url": "https://example.com/zipball/1.19.2",
        },
    ]

    mocker.patch.object(crystal_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = crystal_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "1.20.2"
    assert versions.stable == "1.19.2"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:crystal-lang/crystal"


def test_get_stability_criteria_invalid_latest_version(
    crystal_fetcher: CrystalVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(crystal_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="1.19.2"),
    ]
    latest, stable = crystal_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_other_minor(
    crystal_fetcher: CrystalVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when every release shares the minor line"""
    mocker.patch.object(crystal_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="1.20.2"),
        ReleaseInfo(version="1.20.1"),  # same minor
    ]
    latest, stable = crystal_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.20.2"
    assert stable.version == "1.20.2"


def test_get_stability_criteria_invalid_release_version(
    crystal_fetcher: CrystalVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(crystal_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="1.20.2"),
        ReleaseInfo(version="1.19.invalid"),  # skipped
        ReleaseInfo(version="1.19.2"),
    ]
    latest, stable = crystal_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.20.2"
    assert stable.version == "1.19.2"
