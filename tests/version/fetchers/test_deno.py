from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.deno import DenoVersionFetcher, deno_filter_func


@pytest.fixture
def deno_fetcher() -> DenoVersionFetcher:
    """Fixture to create a DenoVersionFetcher instance"""
    return DenoVersionFetcher()


def test_init(deno_fetcher: DenoVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert deno_fetcher.github_owner == "denoland"
    assert deno_fetcher.github_repo == "deno"


def test_is_stable_tag(deno_fetcher: DenoVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "v2.8.2"},
        {"name": "v1.46.3"},
        {"name": "v2.0.0"},
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "v2.8.0-rc.1"},
        {"name": "v2.8"},  # only two components
        {"name": "2.8.2"},  # missing v prefix
        {"name": "canary"},
        {"name": ""},
    ]

    for tag in stable_tags:
        assert deno_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert deno_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(deno_fetcher: DenoVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    valid_tag: JsonObject = {
        "name": "v2.1.4",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = deno_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "2.1.4"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "v2.1.4"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError):
        deno_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria(deno_fetcher: DenoVersionFetcher) -> None:
    """Test _get_stability_criteria method"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="2.8.2"),
        ReleaseInfo(version="2.7.5"),
        ReleaseInfo(version="2.6.1"),
    ]

    latest, stable = deno_fetcher._get_stability_criteria(releases)
    assert latest.version == "2.8.2"
    assert stable.version == "2.7.5"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="2.8.2")]
    latest, stable = deno_fetcher._get_stability_criteria(single_release)
    assert latest.version == "2.8.2"
    assert stable.version == "2.8.2"

    with pytest.raises(ValueError):
        deno_fetcher._get_stability_criteria([])


def test_deno_filter_func() -> None:
    """Test deno_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "v2.8.2"},
        {"name": "v1.46.3"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "v2.8.0-rc.1"},
        {"name": "v2.8"},
        {"name": "latest"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert deno_filter_func(tag) is True
    for tag in unstable_tags:
        assert deno_filter_func(tag) is False


def test_fetch_versions_integration(
    deno_fetcher: DenoVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "v2.8.2",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/2.8.2",
            "zipball_url": "https://example.com/zipball/2.8.2",
        },
        {
            "name": "v2.7.5",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/2.7.5",
            "zipball_url": "https://example.com/zipball/2.7.5",
        },
    ]

    mocker.patch.object(deno_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = deno_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "2.8.2"
    assert versions.stable == "2.7.5"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:denoland/deno"


def test_get_stability_criteria_invalid_latest_version(
    deno_fetcher: DenoVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(deno_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="2.7.5"),
    ]
    latest, stable = deno_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_previous_minor(
    deno_fetcher: DenoVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when no previous minor version exists"""
    mocker.patch.object(deno_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="2.8.2"),
        ReleaseInfo(version="2.8.1"),  # same minor
        ReleaseInfo(version="1.46.3"),  # different major
    ]
    latest, stable = deno_fetcher._get_stability_criteria(releases)
    assert latest.version == "2.8.2"
    assert stable.version == "2.8.2"


def test_get_stability_criteria_invalid_release_version(
    deno_fetcher: DenoVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(deno_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="2.8.2"),
        ReleaseInfo(version="2.7.invalid"),  # skipped
        ReleaseInfo(version="2.7.5"),
    ]
    latest, stable = deno_fetcher._get_stability_criteria(releases)
    assert latest.version == "2.8.2"
    assert stable.version == "2.7.5"
