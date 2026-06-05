from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.elixir import (
    ElixirVersionFetcher,
    elixir_filter_func,
)


@pytest.fixture
def elixir_fetcher() -> ElixirVersionFetcher:
    """Fixture to create an ElixirVersionFetcher instance"""
    return ElixirVersionFetcher()


def test_init(elixir_fetcher: ElixirVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert elixir_fetcher.github_owner == "elixir-lang"
    assert elixir_fetcher.github_repo == "elixir"


def test_is_stable_tag(elixir_fetcher: ElixirVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "v1.18.4"},
        {"name": "v1.19.5"},
        {"name": "v1.0.0"},
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "v1.20.0-rc.0"},  # release candidate
        {"name": "v1.20-latest"},  # moving tag
        {"name": "v1.18"},  # only two components
        {"name": "1.18.4"},  # missing prefix
        {"name": ""},
    ]

    for tag in stable_tags:
        assert elixir_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert elixir_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(elixir_fetcher: ElixirVersionFetcher) -> None:
    """Test _parse_version_from_tag method"""
    valid_tag: JsonObject = {
        "name": "v1.18.4",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = elixir_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "1.18.4"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "v1.18.4"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError):
        elixir_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria(elixir_fetcher: ElixirVersionFetcher) -> None:
    """Test _get_stability_criteria method"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="1.19.5"),
        ReleaseInfo(version="1.18.4"),
        ReleaseInfo(version="1.17.3"),
    ]

    latest, stable = elixir_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.19.5"
    assert stable.version == "1.18.4"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="1.19.5")]
    latest, stable = elixir_fetcher._get_stability_criteria(single_release)
    assert latest.version == "1.19.5"
    assert stable.version == "1.19.5"

    with pytest.raises(ValueError):
        elixir_fetcher._get_stability_criteria([])


def test_elixir_filter_func() -> None:
    """Test elixir_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "v1.18.4"},
        {"name": "v1.19.5"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "v1.20.0-rc.0"},
        {"name": "v1.20-latest"},
        {"name": "v1.18"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert elixir_filter_func(tag) is True
    for tag in unstable_tags:
        assert elixir_filter_func(tag) is False


def test_fetch_versions_integration(
    elixir_fetcher: ElixirVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "v1.19.5",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/1.19.5",
            "zipball_url": "https://example.com/zipball/1.19.5",
        },
        {
            "name": "v1.18.4",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/1.18.4",
            "zipball_url": "https://example.com/zipball/1.18.4",
        },
    ]

    mocker.patch.object(elixir_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = elixir_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "1.19.5"
    assert versions.stable == "1.18.4"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:elixir-lang/elixir"


def test_get_stability_criteria_invalid_latest_version(
    elixir_fetcher: ElixirVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(elixir_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="1.18.4"),
    ]
    latest, stable = elixir_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_previous_minor(
    elixir_fetcher: ElixirVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when no previous minor version exists"""
    mocker.patch.object(elixir_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="1.19.5"),
        ReleaseInfo(version="1.19.4"),  # same minor
        ReleaseInfo(version="0.9.0"),  # different major
    ]
    latest, stable = elixir_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.19.5"
    assert stable.version == "1.19.5"


def test_get_stability_criteria_invalid_release_version(
    elixir_fetcher: ElixirVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(elixir_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="1.19.5"),
        ReleaseInfo(version="1.18.invalid"),  # skipped
        ReleaseInfo(version="1.18.4"),
    ]
    latest, stable = elixir_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.19.5"
    assert stable.version == "1.18.4"
