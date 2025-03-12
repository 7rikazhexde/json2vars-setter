from typing import Any, Dict, List

import pytest
import pytest_mock
import requests

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import ReleaseInfo
from json2vars_setter.version.fetchers.rust import RustVersionFetcher, rust_filter_func


@pytest.fixture
def rust_fetcher(mocker: "pytest_mock.MockerFixture") -> RustVersionFetcher:
    """Fixture to create a RustVersionFetcher instance with mocked logger."""
    fetcher: RustVersionFetcher = RustVersionFetcher()
    mocker.patch.object(fetcher, "logger", autospec=True)  # Mock logger for all tests
    return fetcher


def test_init(rust_fetcher: RustVersionFetcher) -> None:
    """Test __init__ method."""
    assert rust_fetcher.github_owner == "rust-lang"
    assert rust_fetcher.github_repo == "rust"


def test_is_stable_tag(rust_fetcher: RustVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios."""
    stable_tags: List[Dict[str, Any]] = [
        {"name": "1.75.0"},
        {"name": "1.74.1"},
        {"name": "1.73.0"},
    ]
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "1.75.0-beta.1"},
        {"name": "1.74.1-alpha.2"},
        {"name": "1.73.0-rc.1"},
        {"name": "1.75.0-nightly"},
        {"name": "1.74.1-dev"},
        {"name": "1.73.0-test"},
        {"name": "1.75.0-pre"},
        {"name": ""},  # Missing name
    ]

    for tag in stable_tags:
        assert rust_fetcher._is_stable_tag(tag) is True, f"Expected stable for {tag}"
    for tag in unstable_tags:
        assert rust_fetcher._is_stable_tag(tag) is False, f"Expected unstable for {tag}"


def test_parse_version_from_tag(rust_fetcher: RustVersionFetcher) -> None:
    """Test _parse_version_from_tag method."""
    valid_tag: Dict[str, Any] = {
        "name": "1.75.0",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }
    release_info: ReleaseInfo = rust_fetcher._parse_version_from_tag(valid_tag)
    assert release_info.version == "1.75.0"
    assert release_info.prerelease is False
    assert release_info.release_date is None
    assert release_info.additional_info["tag_name"] == "1.75.0"
    assert release_info.additional_info["commit"]["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError, match="No tag name found"):
        rust_fetcher._parse_version_from_tag({"name": ""})


def test_get_additional_info_success(
    rust_fetcher: RustVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_additional_info with successful channel fetch."""
    mocker.patch.object(
        rust_fetcher,
        "_fetch_rust_channel_info",
        return_value={"stable_channel_available": True},
    )
    info: Dict[str, Any] = rust_fetcher._get_additional_info()
    assert info == {"channel_info": {"stable_channel_available": True}}


def test_fetch_rust_channel_info_success(
    rust_fetcher: RustVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _fetch_rust_channel_info with successful API response."""
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None  # Successful request
    mocker.patch.object(rust_fetcher.session, "get", return_value=mock_response)

    channel_info: Dict[str, Any] = rust_fetcher._fetch_rust_channel_info()
    assert channel_info == {"stable_channel_available": True}


def test_fetch_rust_channel_info_failure(
    rust_fetcher: RustVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _fetch_rust_channel_info with API failure."""
    mocker.patch.object(
        rust_fetcher.session,
        "get",
        side_effect=requests.exceptions.RequestException("API Error"),
    )

    channel_info: Dict[str, Any] = rust_fetcher._fetch_rust_channel_info()
    assert channel_info == {"stable_channel_available": False}
    (
        rust_fetcher.logger.warning.assert_called_once_with(  # type: ignore[attr-defined]
            "Failed to fetch Rust channel information: %s", "API Error"
        )
    )


def test_get_stability_criteria_with_releases(
    rust_fetcher: RustVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with releases present."""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="1.75.0", additional_info={"tag_name": "1.75.0"}),
        ReleaseInfo(version="1.74.1", additional_info={"tag_name": "1.74.1"}),
    ]
    latest, stable = rust_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.75.0"
    assert stable.version == "1.75.0"  # Stable is the same as latest
    (
        rust_fetcher.logger.info.assert_called_once_with(  # type: ignore[attr-defined]
            "For Rust, using latest 1.75.0 as stable (stable channel)"
        )
    )


def test_get_stability_criteria_no_releases(rust_fetcher: RustVersionFetcher) -> None:
    """Test _get_stability_criteria with empty releases."""
    with pytest.raises(ValueError, match="No releases available"):
        rust_fetcher._get_stability_criteria([])


def test_rust_filter_func() -> None:
    """Test rust_filter_func with various tag scenarios."""
    stable_tags: List[Dict[str, Any]] = [
        {"name": "1.75.0"},
        {"name": "1.74.1"},
    ]
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "1.75.0-beta.1"},
        {"name": "1.74.1-alpha.2"},
        {"name": "1.73.0-rc.1"},
        {"name": "1.75.0-nightly"},
        {"name": "1.74.1-dev"},
        {"name": "1.73.0-test"},
        {"name": "1.75.0-pre"},
        {"name": ""},  # Invalid format
    ]
    for tag in stable_tags:
        assert rust_filter_func(tag) is True
    for tag in unstable_tags:
        assert rust_filter_func(tag) is False
