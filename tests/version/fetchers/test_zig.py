from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.zig import ZigVersionFetcher, zig_filter_func


@pytest.fixture
def zig_fetcher() -> ZigVersionFetcher:
    """Fixture to create a ZigVersionFetcher instance"""
    return ZigVersionFetcher()


def test_init(zig_fetcher: ZigVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert zig_fetcher.github_owner == "ziglang"
    assert zig_fetcher.github_repo == "zig"


def test_is_stable_tag(zig_fetcher: ZigVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "0.15.2"},
        {"name": "0.14.1"},
        {"name": "1.0.0"},
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "master"},
        {"name": "0.15.0-dev.123"},  # nightly
        {"name": "0.15"},  # only two components
        {"name": "v0.15.2"},  # unexpected prefix
        {"name": ""},
    ]

    for tag in stable_tags:
        assert zig_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert zig_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(zig_fetcher: ZigVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    valid_tag: JsonObject = {
        "name": "0.15.2",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = zig_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "0.15.2"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "0.15.2"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError):
        zig_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria(zig_fetcher: ZigVersionFetcher) -> None:
    """Test _get_stability_criteria method"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="0.15.2"),
        ReleaseInfo(version="0.14.1"),
        ReleaseInfo(version="0.13.0"),
    ]

    latest, stable = zig_fetcher._get_stability_criteria(releases)
    assert latest.version == "0.15.2"
    assert stable.version == "0.14.1"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="0.15.2")]
    latest, stable = zig_fetcher._get_stability_criteria(single_release)
    assert latest.version == "0.15.2"
    assert stable.version == "0.15.2"

    with pytest.raises(ValueError):
        zig_fetcher._get_stability_criteria([])


def test_zig_filter_func() -> None:
    """Test zig_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "0.15.2"},
        {"name": "0.14.1"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "master"},
        {"name": "0.15.0-dev.123"},
        {"name": "0.15"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert zig_filter_func(tag) is True
    for tag in unstable_tags:
        assert zig_filter_func(tag) is False


def test_fetch_versions_integration(
    zig_fetcher: ZigVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "0.15.2",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/0.15.2",
            "zipball_url": "https://example.com/zipball/0.15.2",
        },
        {
            "name": "0.14.1",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/0.14.1",
            "zipball_url": "https://example.com/zipball/0.14.1",
        },
    ]

    mocker.patch.object(zig_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = zig_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "0.15.2"
    assert versions.stable == "0.14.1"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:ziglang/zig"


def test_get_stability_criteria_invalid_latest_version(
    zig_fetcher: ZigVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(zig_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="0.14.1"),
    ]
    latest, stable = zig_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_previous_minor(
    zig_fetcher: ZigVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when no previous minor version exists"""
    mocker.patch.object(zig_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="0.15.2"),
        ReleaseInfo(version="0.15.1"),  # same minor
        ReleaseInfo(version="1.0.0"),  # different major
    ]
    latest, stable = zig_fetcher._get_stability_criteria(releases)
    assert latest.version == "0.15.2"
    assert stable.version == "0.15.2"


def test_get_stability_criteria_invalid_release_version(
    zig_fetcher: ZigVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(zig_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="0.15.2"),
        ReleaseInfo(version="0.14.invalid"),  # skipped
        ReleaseInfo(version="0.14.1"),
    ]
    latest, stable = zig_fetcher._get_stability_criteria(releases)
    assert latest.version == "0.15.2"
    assert stable.version == "0.14.1"
