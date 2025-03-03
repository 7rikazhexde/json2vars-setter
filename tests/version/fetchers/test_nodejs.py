from typing import Any, Dict, List, Optional

import pytest
import pytest_mock
import requests

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import ReleaseInfo
from json2vars_setter.version.fetchers.nodejs import (
    NodejsVersionFetcher,
    nodejs_filter_func,
)


@pytest.fixture
def nodejs_fetcher(mocker: "pytest_mock.MockerFixture") -> NodejsVersionFetcher:
    """Fixture to create a NodejsVersionFetcher instance with mocked logger."""
    fetcher: NodejsVersionFetcher = NodejsVersionFetcher()
    mocker.patch.object(fetcher, "logger", autospec=True)  # Mock logger for all tests
    return fetcher


def test_init(nodejs_fetcher: NodejsVersionFetcher) -> None:
    """Test __init__ method."""
    assert nodejs_fetcher.github_owner == "nodejs"
    assert nodejs_fetcher.github_repo == "node"


def test_is_stable_tag(nodejs_fetcher: NodejsVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios."""
    stable_tags: List[Dict[str, Any]] = [
        {"name": "v18.20.0"},
        {"name": "v20.11.1"},
        {"name": "v22.0.0"},
    ]
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "v18.20.0-rc.1"},
        {"name": "v20.11.1-alpha.1"},
        {"name": "v22.0.0-beta.1"},
        {"name": "v18.20.0-nightly"},
        {"name": "v20.11.1-test"},
        {"name": "v22.0.0-next"},
        {"name": "v18.20.0-experimental"},
        {"name": ""},  # Missing name
    ]

    for tag in stable_tags:
        assert nodejs_fetcher._is_stable_tag(tag) is True, f"Expected stable for {tag}"
    for tag in unstable_tags:
        assert nodejs_fetcher._is_stable_tag(tag) is False, (
            f"Expected unstable for {tag}"
        )


def test_parse_version_from_tag(nodejs_fetcher: NodejsVersionFetcher) -> None:
    """Test _parse_version_from_tag method."""
    valid_tag: Dict[str, Any] = {
        "name": "v18.20.0",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }
    release_info: ReleaseInfo = nodejs_fetcher._parse_version_from_tag(valid_tag)
    assert release_info.version == "18.20.0"
    assert release_info.prerelease is False
    assert release_info.release_date is None
    assert release_info.additional_info["tag_name"] == "v18.20.0"
    assert release_info.additional_info["commit"]["sha"] == "abc123"
    assert release_info.additional_info["is_lts"] is False
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError, match="No tag name found"):
        nodejs_fetcher._parse_version_from_tag({"name": ""})


def test_get_additional_info(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_additional_info method."""
    mocker.patch.object(
        nodejs_fetcher,
        "_fetch_nodejs_lts_info",
        return_value={"18.20.0": True},
    )
    info: Dict[str, Any] = nodejs_fetcher._get_additional_info()
    assert info == {"lts_info": {"18.20.0": True}}


def test_get_stability_criteria_with_lts(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with LTS versions present."""
    mocker.patch.object(
        nodejs_fetcher,
        "_fetch_latest_lts_versions",
        return_value=["20.11.1", "18.20.0"],
    )
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="22.0.0", additional_info={"tag_name": "v22.0.0"}),
        ReleaseInfo(version="20.11.1", additional_info={"tag_name": "v20.11.1"}),
        ReleaseInfo(version="18.20.0", additional_info={"tag_name": "v18.20.0"}),
    ]
    latest, stable = nodejs_fetcher._get_stability_criteria(releases)
    assert latest.version == "22.0.0"
    assert stable.version == "20.11.1"


def test_get_stability_criteria_no_lts_fetch_tag(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when LTS is fetched via API."""
    mocker.patch.object(
        nodejs_fetcher, "_fetch_latest_lts_versions", return_value=["22.9.0"]
    )
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="23.0.0", additional_info={"tag_name": "v23.0.0"}),
        ReleaseInfo(version="21.0.0", additional_info={"tag_name": "v21.0.0"}),
    ]
    mock_tag: Dict[str, Any] = {
        "name": "v22.9.0",
        "commit": {"sha": "xyz789"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }
    mocker.patch.object(nodejs_fetcher, "_get_specific_tag", return_value=mock_tag)

    latest, stable = nodejs_fetcher._get_stability_criteria(releases)
    assert latest.version == "23.0.0"
    assert stable.version == "22.9.0"
    assert stable.additional_info["is_lts"] is True


def test_get_stability_criteria_no_lts_fetch_tag_failure(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when LTS fetch fails."""
    mocker.patch.object(
        nodejs_fetcher, "_fetch_latest_lts_versions", return_value=["22.9.0"]
    )
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="23.0.0", additional_info={"tag_name": "v23.0.0"}),
        ReleaseInfo(version="21.0.0", additional_info={"tag_name": "v21.0.0"}),
    ]
    mocker.patch.object(
        nodejs_fetcher,
        "_get_specific_tag",
        side_effect=Exception("API Error"),
    )

    latest, stable = nodejs_fetcher._get_stability_criteria(releases)
    assert latest.version == "23.0.0"
    assert stable.version == "23.0.0"  # Falls back to latest


def test_get_stability_criteria_no_lts_even_major(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria falling back to even major version."""
    mocker.patch.object(nodejs_fetcher, "_fetch_latest_lts_versions", return_value=[])
    mocker.patch.object(nodejs_fetcher, "_get_specific_tag", return_value=None)
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="23.0.0", additional_info={"tag_name": "v23.0.0"}),
        ReleaseInfo(version="22.0.0", additional_info={"tag_name": "v22.0.0"}),
        ReleaseInfo(version="21.0.0", additional_info={"tag_name": "v21.0.0"}),
    ]
    latest, stable = nodejs_fetcher._get_stability_criteria(releases)
    assert latest.version == "23.0.0"
    assert stable.version == "22.0.0"


def test_get_stability_criteria_no_lts_no_even_major(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria when no LTS or even major versions exist."""
    mocker.patch.object(nodejs_fetcher, "_fetch_latest_lts_versions", return_value=[])
    mocker.patch.object(nodejs_fetcher, "_get_specific_tag", return_value=None)
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="23.0.0", additional_info={"tag_name": "v23.0.0"}),
        ReleaseInfo(version="21.0.0", additional_info={"tag_name": "v21.0.0"}),
    ]
    latest, stable = nodejs_fetcher._get_stability_criteria(releases)
    assert latest.version == "23.0.0"
    assert stable.version == "23.0.0"
    (
        nodejs_fetcher.logger.warning.assert_called_once_with(  # type: ignore[attr-defined]
            "No LTS or even major version found. Using latest 23.0.0 as stable. Consider increasing --count."
        )
    )


def test_get_stability_criteria_with_invalid_version(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version to cover ValueError (lines 167-168)."""
    mocker.patch.object(nodejs_fetcher, "_fetch_latest_lts_versions", return_value=[])
    mocker.patch.object(nodejs_fetcher, "_get_specific_tag", return_value=None)
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="23.0.0", additional_info={"tag_name": "v23.0.0"}),
        ReleaseInfo(
            version="invalid", additional_info={"tag_name": "invalid"}
        ),  # Invalid version
        ReleaseInfo(version="21.0.0", additional_info={"tag_name": "v21.0.0"}),
    ]
    latest, stable = nodejs_fetcher._get_stability_criteria(releases)
    assert latest.version == "23.0.0"
    assert (
        stable.version == "23.0.0"
    )  # Falls back to latest due to no LTS or even majors
    (
        nodejs_fetcher.logger.warning.assert_called_once_with(  # type: ignore[attr-defined]
            "No LTS or even major version found. Using latest 23.0.0 as stable. Consider increasing --count."
        )
    )


def test_get_stability_criteria_no_releases(
    nodejs_fetcher: NodejsVersionFetcher,
) -> None:
    """Test _get_stability_criteria with empty releases."""
    with pytest.raises(ValueError, match="No releases available"):
        nodejs_fetcher._get_stability_criteria([])


def test_fetch_latest_lts_versions_success(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _fetch_latest_lts_versions with successful API response."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = [
        {"version": "v20.11.1", "lts": "Iron"},
        {"version": "v18.20.0", "lts": "Hydrogen"},
        {"version": "v22.0.0", "lts": False},
    ]
    mocker.patch.object(nodejs_fetcher.session, "get", return_value=mock_response)
    lts_versions: List[str] = nodejs_fetcher._fetch_latest_lts_versions()
    assert lts_versions == ["20.11.1", "18.20.0"]


def test_fetch_latest_lts_versions_no_lts(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _fetch_latest_lts_versions with no LTS versions."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = [{"version": "v22.0.0", "lts": False}]
    mocker.patch.object(nodejs_fetcher.session, "get", return_value=mock_response)
    lts_versions: List[str] = nodejs_fetcher._fetch_latest_lts_versions()
    assert lts_versions == []


def test_fetch_latest_lts_versions_api_failure(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _fetch_latest_lts_versions with API failure."""
    mocker.patch.object(
        nodejs_fetcher.session,
        "get",
        side_effect=requests.exceptions.RequestException("API Failure"),
    )
    lts_versions: List[str] = nodejs_fetcher._fetch_latest_lts_versions()
    assert lts_versions == []
    (
        nodejs_fetcher.logger.warning.assert_called_once_with(  # type: ignore[attr-defined]
            "Failed to fetch LTS versions: API Failure"
        )
    )


def test_fetch_latest_lts_versions_empty_response(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _fetch_latest_lts_versions with empty API response."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = []
    mocker.patch.object(nodejs_fetcher.session, "get", return_value=mock_response)
    lts_versions: List[str] = nodejs_fetcher._fetch_latest_lts_versions()
    assert lts_versions == []
    (
        nodejs_fetcher.logger.warning.assert_called_once_with(  # type: ignore[attr-defined]
            "No LTS versions found in API response"
        )
    )


def test_get_specific_tag_success(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_specific_tag with successful API calls."""
    mock_ref_response = mocker.Mock()
    mock_ref_response.json.return_value = {"object": {"url": "http://tag-url"}}
    mock_tag_response = mocker.Mock()
    mock_tag_response.json.return_value = {"object": {"url": "http://commit-url"}}
    mock_commit_response = mocker.Mock()
    mock_commit_response.json.return_value = {"sha": "abc123"}
    mocker.patch.object(
        nodejs_fetcher.session,
        "get",
        side_effect=[mock_ref_response, mock_tag_response, mock_commit_response],
    )
    tag: Optional[Dict[str, Any]] = nodejs_fetcher._get_specific_tag("v22.0.0")
    assert tag == {"name": "v22.0.0", "commit": {"sha": "abc123"}}


def test_get_specific_tag_failure(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_specific_tag with API failure."""
    mocker.patch.object(
        nodejs_fetcher.session,
        "get",
        side_effect=requests.exceptions.RequestException("API Error"),
    )
    tag: Optional[Dict[str, Any]] = nodejs_fetcher._get_specific_tag("v22.0.0")
    assert tag is None
    (
        nodejs_fetcher.logger.warning.assert_called_once_with(  # type: ignore[attr-defined]
            "Failed to fetch tag v22.0.0: API Error"
        )
    )


def test_get_specific_tag_no_tag_url(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_specific_tag when tag_url is missing (covers line 243)."""
    mock_ref_response = mocker.Mock()
    mock_ref_response.json.return_value = {"object": {}}  # No 'url' key
    mocker.patch.object(
        nodejs_fetcher.session,
        "get",
        return_value=mock_ref_response,
    )
    tag: Optional[Dict[str, Any]] = nodejs_fetcher._get_specific_tag("v22.0.0")
    assert tag is None
    # No warning expected since this is a silent return


def test_get_specific_tag_no_commit_url(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_specific_tag when commit_url is missing (covers line 249)."""
    mock_ref_response = mocker.Mock()
    mock_ref_response.json.return_value = {"object": {"url": "http://tag-url"}}
    mock_tag_response = mocker.Mock()
    mock_tag_response.json.return_value = {"object": {}}  # No 'url' key
    mocker.patch.object(
        nodejs_fetcher.session,
        "get",
        side_effect=[mock_ref_response, mock_tag_response],
    )
    tag: Optional[Dict[str, Any]] = nodejs_fetcher._get_specific_tag("v22.0.0")
    assert tag is None
    # No warning expected since this is a silent return


def test_fetch_nodejs_lts_info_success(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _fetch_nodejs_lts_info with successful API response."""
    mock_response = mocker.Mock()
    mock_response.json.return_value = [
        {"version": "v20.11.1", "lts": "Iron"},
        {"version": "v18.20.0", "lts": "Hydrogen"},
        {"version": "v22.0.0", "lts": False},
    ]
    mocker.patch.object(nodejs_fetcher.session, "get", return_value=mock_response)
    lts_info: Dict[str, bool] = nodejs_fetcher._fetch_nodejs_lts_info()
    assert lts_info == {"20.11.1": True, "18.20.0": True}
    (
        nodejs_fetcher.logger.info.assert_called_once_with(  # type: ignore[attr-defined]
            "Retrieved 2 LTS versions from Node.js API"
        )
    )


def test_fetch_nodejs_lts_info_failure(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _fetch_nodejs_lts_info with API failure."""
    mocker.patch.object(
        nodejs_fetcher.session,
        "get",
        side_effect=requests.exceptions.RequestException("API Error"),
    )
    lts_info: Dict[str, bool] = nodejs_fetcher._fetch_nodejs_lts_info()
    assert lts_info == {}
    (
        nodejs_fetcher.logger.warning.assert_called_once_with(  # type: ignore[attr-defined]
            "Failed to fetch LTS information: API Error"
        )
    )


def test_get_stability_criteria_lts_not_22(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with LTS versions not starting with '22.'."""
    mocker.patch.object(
        nodejs_fetcher,
        "_fetch_latest_lts_versions",
        return_value=["20.11.1", "18.20.0"],
    )
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="23.0.0", additional_info={"tag_name": "v23.0.0"}),
        ReleaseInfo(version="21.0.0", additional_info={"tag_name": "v21.0.0"}),
    ]
    # Mock _get_specific_tag to return None to simulate fetch failure
    mocker.patch.object(nodejs_fetcher, "_get_specific_tag", return_value=None)

    latest, stable = nodejs_fetcher._get_stability_criteria(releases)
    assert latest.version == "23.0.0"
    assert (
        stable.version == "23.0.0"
    )  # Falls back to latest due to no LTS match or even major


def test_get_stability_criteria_lts_fetch_none(
    nodejs_fetcher: NodejsVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria where LTS fetch returns None."""
    mocker.patch.object(
        nodejs_fetcher, "_fetch_latest_lts_versions", return_value=["22.9.0", "20.11.1"]
    )
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="23.0.0", additional_info={"tag_name": "v23.0.0"}),
        ReleaseInfo(version="21.0.0", additional_info={"tag_name": "v21.0.0"}),
    ]
    # Mock _get_specific_tag to return None for "v22.9.0"
    mocker.patch.object(nodejs_fetcher, "_get_specific_tag", return_value=None)

    latest, stable = nodejs_fetcher._get_stability_criteria(releases)
    assert latest.version == "23.0.0"
    assert stable.version == "23.0.0"  # Falls back to latest


def test_nodejs_filter_func() -> None:
    """Test nodejs_filter_func with various tag scenarios."""
    stable_tags: List[Dict[str, Any]] = [
        {"name": "v18.20.0"},
        {"name": "v20.11.1"},
    ]
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "v18.20.0-rc.1"},
        {"name": "v20.11.1-alpha.1"},
        {"name": ""},  # Invalid format
    ]
    for tag in stable_tags:
        assert nodejs_filter_func(tag) is True
    for tag in unstable_tags:
        assert nodejs_filter_func(tag) is False
