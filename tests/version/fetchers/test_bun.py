from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.bun import BunVersionFetcher, bun_filter_func


@pytest.fixture
def bun_fetcher() -> BunVersionFetcher:
    """Fixture to create a BunVersionFetcher instance"""
    return BunVersionFetcher()


def test_init(bun_fetcher: BunVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert bun_fetcher.github_owner == "oven-sh"
    assert bun_fetcher.github_repo == "bun"


def test_is_stable_tag(bun_fetcher: BunVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "bun-v1.3.14"},
        {"name": "bun-v1.2.23"},
        {"name": "bun-v1.0.0"},
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "canary"},
        {"name": "not-quite-v0"},
        {"name": "v0.1.1"},  # legacy format
        {"name": "bun-v1.3"},  # only two components
        {"name": "1.3.14"},  # missing prefix
        {"name": ""},
    ]

    for tag in stable_tags:
        assert bun_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert bun_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(bun_fetcher: BunVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    valid_tag: JsonObject = {
        "name": "bun-v1.3.14",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = bun_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "1.3.14"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "bun-v1.3.14"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError):
        bun_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria(bun_fetcher: BunVersionFetcher) -> None:
    """Test _get_stability_criteria method"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="1.3.14"),
        ReleaseInfo(version="1.2.23"),
        ReleaseInfo(version="1.1.40"),
    ]

    latest, stable = bun_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.3.14"
    assert stable.version == "1.2.23"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="1.3.14")]
    latest, stable = bun_fetcher._get_stability_criteria(single_release)
    assert latest.version == "1.3.14"
    assert stable.version == "1.3.14"

    with pytest.raises(ValueError):
        bun_fetcher._get_stability_criteria([])


def test_bun_filter_func() -> None:
    """Test bun_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "bun-v1.3.14"},
        {"name": "bun-v1.2.23"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "canary"},
        {"name": "v0.1.1"},
        {"name": "bun-v1.3"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert bun_filter_func(tag) is True
    for tag in unstable_tags:
        assert bun_filter_func(tag) is False


def test_fetch_versions_integration(
    bun_fetcher: BunVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "bun-v1.3.14",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/1.3.14",
            "zipball_url": "https://example.com/zipball/1.3.14",
        },
        {
            "name": "bun-v1.2.23",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/1.2.23",
            "zipball_url": "https://example.com/zipball/1.2.23",
        },
    ]

    mocker.patch.object(bun_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = bun_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "1.3.14"
    assert versions.stable == "1.2.23"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:oven-sh/bun"


def test_get_stability_criteria_invalid_latest_version(
    bun_fetcher: BunVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(bun_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="1.2.23"),
    ]
    latest, stable = bun_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_previous_minor(
    bun_fetcher: BunVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when no previous minor version exists"""
    mocker.patch.object(bun_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="1.3.14"),
        ReleaseInfo(version="1.3.13"),  # same minor
        ReleaseInfo(version="0.9.0"),  # different major
    ]
    latest, stable = bun_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.3.14"
    assert stable.version == "1.3.14"


def test_get_stability_criteria_invalid_release_version(
    bun_fetcher: BunVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(bun_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="1.3.14"),
        ReleaseInfo(version="1.2.invalid"),  # skipped
        ReleaseInfo(version="1.2.23"),
    ]
    latest, stable = bun_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.3.14"
    assert stable.version == "1.2.23"
