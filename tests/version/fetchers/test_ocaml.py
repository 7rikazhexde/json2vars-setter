from typing import List, cast

import pytest
import pytest_mock

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.ocaml import (
    OcamlVersionFetcher,
    ocaml_filter_func,
)


@pytest.fixture
def ocaml_fetcher() -> OcamlVersionFetcher:
    """Fixture to create an OcamlVersionFetcher instance"""
    return OcamlVersionFetcher()


def test_init(ocaml_fetcher: OcamlVersionFetcher) -> None:
    """Test __init__ sets the correct GitHub repository information"""
    assert ocaml_fetcher.github_owner == "ocaml"
    assert ocaml_fetcher.github_repo == "ocaml"


def test_is_stable_tag(ocaml_fetcher: OcamlVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios"""
    stable_tags: List[JsonObject] = [
        {"name": "5.4.1"},
        {"name": "5.3.0"},
        {"name": "4.14.2"},
    ]

    unstable_tags: List[JsonObject] = [
        {"name": "5.5.0-beta1"},  # beta
        {"name": "5.5.0-alpha1"},  # alpha
        {"name": "csl-1.15"},  # ancient Caml Special Light tag
        {"name": "5.4"},  # only two components
        {"name": ""},
    ]

    for tag in stable_tags:
        assert ocaml_fetcher._is_stable_tag(tag) is True
    for tag in unstable_tags:
        assert ocaml_fetcher._is_stable_tag(tag) is False


def test_parse_version_from_tag(ocaml_fetcher: OcamlVersionFetcher) -> None:
    """Test _parse_version_from_tag returns the bare version"""
    valid_tag: JsonObject = {
        "name": "5.4.1",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }

    release_info: ReleaseInfo = ocaml_fetcher._parse_version_from_tag(valid_tag)

    assert release_info.version == "5.4.1"
    assert release_info.prerelease is False
    assert release_info.additional_info["tag_name"] == "5.4.1"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError):
        ocaml_fetcher._parse_version_from_tag({"name": ""})


def test_version_sort_key(ocaml_fetcher: OcamlVersionFetcher) -> None:
    """Test _version_sort_key builds a numeric (major, minor, patch) key"""
    assert ocaml_fetcher._version_sort_key({"name": "5.4.1"}) == (5, 4, 1)
    assert ocaml_fetcher._version_sort_key({"name": "5.3.0"}) == (5, 3, 0)


def test_get_github_tags_sorts_and_truncates(
    ocaml_fetcher: OcamlVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_github_tags sorts by semantic version and truncates"""
    # Unsorted, mimicking the unreliable ocaml/ocaml tag order
    unsorted_tags: List[JsonObject] = [
        {"name": "5.3.0"},
        {"name": "5.4.1"},
        {"name": "4.14.2"},
        {"name": "5.4.0"},
    ]
    mocker.patch.object(
        BaseVersionFetcher, "_get_github_tags", return_value=unsorted_tags
    )

    top_two = ocaml_fetcher._get_github_tags(2)
    assert [str(tag["name"]) for tag in top_two] == ["5.4.1", "5.4.0"]

    all_tags = ocaml_fetcher._get_github_tags()
    assert [str(tag["name"]) for tag in all_tags] == [
        "5.4.1",
        "5.4.0",
        "5.3.0",
        "4.14.2",
    ]


def test_get_stability_criteria(ocaml_fetcher: OcamlVersionFetcher) -> None:
    """Test _get_stability_criteria picks latest and the previous minor line"""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="5.4.1"),
        ReleaseInfo(version="5.4.0"),
        ReleaseInfo(version="5.3.0"),
    ]

    latest, stable = ocaml_fetcher._get_stability_criteria(releases)
    assert latest.version == "5.4.1"
    assert stable.version == "5.3.0"

    single_release: List[ReleaseInfo] = [ReleaseInfo(version="5.4.1")]
    latest, stable = ocaml_fetcher._get_stability_criteria(single_release)
    assert latest.version == "5.4.1"
    assert stable.version == "5.4.1"

    with pytest.raises(ValueError):
        ocaml_fetcher._get_stability_criteria([])


def test_ocaml_filter_func() -> None:
    """Test ocaml_filter_func with various tag names"""
    stable_tags: List[JsonObject] = [
        {"name": "5.4.1"},
        {"name": "5.3.0"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "5.5.0-beta1"},
        {"name": "csl-1.15"},
        {"name": "5.4"},
        {"name": ""},
    ]
    for tag in stable_tags:
        assert ocaml_filter_func(tag) is True
    for tag in unstable_tags:
        assert ocaml_filter_func(tag) is False


def test_fetch_versions_integration(
    ocaml_fetcher: OcamlVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions method with mocked API calls"""
    mock_tags: List[JsonObject] = [
        {
            "name": "5.4.1",
            "commit": {"sha": "abc123"},
            "tarball_url": "https://example.com/tarball/5.4.1",
            "zipball_url": "https://example.com/zipball/5.4.1",
        },
        {
            "name": "5.3.0",
            "commit": {"sha": "def456"},
            "tarball_url": "https://example.com/tarball/5.3.0",
            "zipball_url": "https://example.com/zipball/5.3.0",
        },
    ]

    mocker.patch.object(ocaml_fetcher, "_get_github_tags", return_value=mock_tags)

    versions = ocaml_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "5.4.1"
    assert versions.stable == "5.3.0"
    assert len(versions.recent_releases) == 2
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "github:ocaml/ocaml"


def test_get_stability_criteria_invalid_latest_version(
    ocaml_fetcher: OcamlVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when the latest version is unparsable"""
    mocker.patch.object(ocaml_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="invalid"),
        ReleaseInfo(version="5.3.0"),
    ]
    latest, stable = ocaml_fetcher._get_stability_criteria(releases)
    assert latest.version == "invalid"
    assert stable.version == "invalid"


def test_get_stability_criteria_no_other_minor(
    ocaml_fetcher: OcamlVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when every release shares the minor line"""
    mocker.patch.object(ocaml_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="5.4.1"),
        ReleaseInfo(version="5.4.0"),  # same minor
    ]
    latest, stable = ocaml_fetcher._get_stability_criteria(releases)
    assert latest.version == "5.4.1"
    assert stable.version == "5.4.1"


def test_get_stability_criteria_invalid_release_version(
    ocaml_fetcher: OcamlVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version in the releases list"""
    mocker.patch.object(ocaml_fetcher, "logger", mocker.Mock())

    releases = [
        ReleaseInfo(version="5.4.1"),
        ReleaseInfo(version="5.3.invalid"),  # skipped
        ReleaseInfo(version="5.3.0"),
    ]
    latest, stable = ocaml_fetcher._get_stability_criteria(releases)
    assert latest.version == "5.4.1"
    assert stable.version == "5.3.0"
