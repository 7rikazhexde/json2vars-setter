from typing import Any, Dict, List

import pytest
import pytest_mock
import requests
from _pytest.capture import CaptureFixture

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import ReleaseInfo
from json2vars_setter.version.fetchers.go import GoVersionFetcher, check_api


@pytest.fixture
def go_fetcher(mocker: "pytest_mock.MockerFixture") -> GoVersionFetcher:
    """Fixture to create a GoVersionFetcher instance with mocked logger."""
    fetcher: GoVersionFetcher = GoVersionFetcher()
    mocker.patch.object(fetcher, "logger", autospec=True)  # Mock logger for all tests
    return fetcher


def test_init(go_fetcher: GoVersionFetcher) -> None:
    """Test __init__ method."""
    assert go_fetcher.github_owner == "golang"
    assert go_fetcher.github_repo == "go"


def test_is_stable_tag(go_fetcher: GoVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios."""
    stable_tags: List[Dict[str, Any]] = [
        {"name": "go1.22.1"},
        {"name": "go1.21.0"},
        {"name": "go1.20.3"},
    ]
    unstable_tags: List[Dict[str, Any]] = [
        {"name": "go1.22.1-rc1"},
        {"name": "go1.21.0-alpha.1"},
        {"name": "go1.20.3-beta.2"},
        {"name": "go1.22.1-preview"},
        {"name": "go1.21.0-pre"},
        {"name": "go1.20.3-test"},
        {"name": "go1.22.1-dev"},
        {"name": "go1.21.0-snapshot"},
        {"name": ""},  # Missing name
    ]

    for tag in stable_tags:
        assert go_fetcher._is_stable_tag(tag) is True, f"Expected stable for {tag}"
    for tag in unstable_tags:
        assert go_fetcher._is_stable_tag(tag) is False, f"Expected unstable for {tag}"


def test_parse_version_from_tag(go_fetcher: GoVersionFetcher) -> None:
    """Test _parse_version_from_tag method."""
    valid_tag: Dict[str, Any] = {
        "name": "go1.22.1",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }
    release_info: ReleaseInfo = go_fetcher._parse_version_from_tag(valid_tag)
    assert release_info.version == "1.22.1"
    assert release_info.prerelease is False
    assert release_info.release_date is None
    assert release_info.additional_info["tag_name"] == "go1.22.1"
    assert release_info.additional_info["commit"]["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError, match="No tag name found"):
        go_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria_with_previous_minor(
    go_fetcher: GoVersionFetcher,
) -> None:
    """Test _get_stability_criteria with a previous minor version present."""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="1.22.1", additional_info={"tag_name": "go1.22.1"}),
        ReleaseInfo(version="1.21.0", additional_info={"tag_name": "go1.21.0"}),
        ReleaseInfo(version="1.20.3", additional_info={"tag_name": "go1.20.3"}),
    ]
    latest, stable = go_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.22.1"
    assert stable.version == "1.21.0"
    (
        go_fetcher.logger.info.assert_called_once_with(  # type: ignore[attr-defined]
            "Using 1.21.0 as stable vs latest 1.22.1"
        )
    )


def test_get_stability_criteria_no_previous_minor(
    go_fetcher: GoVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with no previous minor version, falling back to latest."""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="1.22.1", additional_info={"tag_name": "go1.22.1"}),
        ReleaseInfo(version="1.22.0", additional_info={"tag_name": "go1.22.0"}),
    ]
    latest, stable = go_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.22.1"
    assert stable.version == "1.22.1"
    (
        go_fetcher.logger.info.assert_called_once_with(  # type: ignore[attr-defined]
            "No suitable stable version found, using latest 1.22.1 as stable"
        )
    )


def test_get_stability_criteria_with_invalid_version(
    go_fetcher: GoVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with an invalid version to cover regex mismatch."""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="1.22.1", additional_info={"tag_name": "go1.22.1"}),
        ReleaseInfo(
            version="invalid", additional_info={"tag_name": "invalid"}
        ),  # Invalid version
        ReleaseInfo(version="1.21.0", additional_info={"tag_name": "go1.21.0"}),
    ]
    latest, stable = go_fetcher._get_stability_criteria(releases)
    assert latest.version == "1.22.1"
    assert stable.version == "1.21.0"  # Corrected: stable is the previous minor version
    (
        go_fetcher.logger.info.assert_called_once_with(  # type: ignore[attr-defined]
            "Using 1.21.0 as stable vs latest 1.22.1"
        )
    )


def test_get_stability_criteria_no_releases(go_fetcher: GoVersionFetcher) -> None:
    """Test _get_stability_criteria with empty releases."""
    with pytest.raises(ValueError, match="No releases available"):
        go_fetcher._get_stability_criteria([])


def test_check_api_success(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with successful API response."""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "go1.22.1"},
        {"name": "go1.21.0-rc1"},
        {"name": "go1.21.0"},
    ]
    mock_session.get.return_value = mock_response

    check_api(session=mock_session, count=2, verbose=True)
    captured = capsys.readouterr()
    assert "Total stable tags found: 2" in captured.out
    assert "- go1.22.1" in captured.out
    assert "- go1.21.0" in captured.out


def test_check_api_verbose_greater_than_one(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with verbose > 1 to cover raw tags output (lines 108-110)."""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "go1.22.1"},
        {"name": "go1.21.0-rc1"},
        {"name": "go1.21.0"},
        {"name": "go1.20.3"},
        {"name": "go1.19.0"},
        {"name": "go1.18.2"},  # More than 5 tags to ensure slicing
    ]
    mock_session.get.return_value = mock_response

    check_api(session=mock_session, count=2, verbose=2)  # verbose > 1
    captured = capsys.readouterr()
    assert "Total stable tags found: 5" in captured.out
    assert "First 5 raw tags on page 1:" in captured.out
    assert "- go1.22.1" in captured.out
    assert "- go1.21.0-rc1" in captured.out
    assert "- go1.21.0" in captured.out
    assert "- go1.20.3" in captured.out
    assert "- go1.19.0" in captured.out


def test_check_api_partial_success(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with fewer stable tags than requested."""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "go1.22.1"},
        {"name": "go1.21.0-beta1"},
    ]
    mock_session.get.return_value = mock_response

    check_api(session=mock_session, count=3, verbose=True)
    captured = capsys.readouterr()
    assert "Total stable tags found: 1" in captured.out
    assert "- go1.22.1" in captured.out


def test_check_api_multi_page(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with multi-page response to cover pagination."""
    mock_session = mocker.Mock()
    mock_response_page1 = mocker.Mock()
    mock_response_page1.status_code = 200
    mock_response_page1.json.return_value = [{"name": "go1.22.1"}] * 100  # Full page
    mock_response_page2 = mocker.Mock()
    mock_response_page2.status_code = 200
    mock_response_page2.json.return_value = [
        {"name": "go1.21.0"},
        {"name": "go1.20.3"},
    ]  # Less than 100, last page
    mock_session.get.side_effect = [mock_response_page1, mock_response_page2]

    check_api(
        session=mock_session, count=102, verbose=True
    )  # Increased count to fetch 2 pages
    captured = capsys.readouterr()
    assert "Total stable tags found: 102" in captured.out
    assert "- go1.22.1" in captured.out
    assert "- go1.21.0" in captured.out


def test_check_api_failure(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with API failure."""
    mock_session = mocker.Mock()
    mock_session.get.side_effect = requests.exceptions.RequestException("API Error")

    check_api(session=mock_session, count=2, verbose=True)
    captured = capsys.readouterr()
    assert "Error: API Error" in captured.out


def test_check_api_no_verbose(mocker: "pytest_mock.MockerFixture") -> None:
    """Test check_api with verbose=False (early return)."""
    mock_session = mocker.Mock()
    check_api(session=mock_session, count=2, verbose=False)
    mock_session.get.assert_not_called()  # No API calls should be made


def test_check_api_empty_response(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with empty API response."""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = []
    mock_session.get.return_value = mock_response

    check_api(session=mock_session, count=2, verbose=True)
    captured = capsys.readouterr()
    assert "Total stable tags found: 0" in captured.out


def test_get_stability_criteria_with_invalid_version_pattern(
    go_fetcher: GoVersionFetcher,
) -> None:
    """Test _get_stability_criteria with a completely invalid version pattern to cover line 113 branch."""
    # Release information with an invalid version pattern
    # Create a version string that is completely non-SemVer
    releases: List[ReleaseInfo] = [
        ReleaseInfo(
            version="not-a-valid-semver", additional_info={"tag_name": "go-invalid"}
        ),
        ReleaseInfo(version="1.21.0", additional_info={"tag_name": "go1.21.0"}),
    ]

    # Execute the function
    latest, stable = go_fetcher._get_stability_criteria(releases)

    # Verify that the versions match
    assert latest.version == "not-a-valid-semver"
    assert (
        stable.version == "not-a-valid-semver"
    )  # Use latest as no valid version is found


def test_check_api_multi_page_full_coverage(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api to cover while loop multiple iterations and exit condition."""
    mock_session = mocker.Mock()

    # Page 1: 100 tags (1 stable tag, 99 unstable tags)
    page1_tags = [{"name": "go1.22.1"}] + [
        {"name": f"go1.21.{i}-rc1"} for i in range(99)
    ]
    mock_response_page1 = mocker.Mock()
    mock_response_page1.status_code = 200
    mock_response_page1.json.return_value = page1_tags

    # Page 2: 100 tags (1 stable tag, 99 unstable tags)
    page2_tags = [{"name": "go1.21.0"}] + [
        {"name": f"go1.20.{i}-rc1"} for i in range(99)
    ]
    mock_response_page2 = mocker.Mock()
    mock_response_page2.status_code = 200
    mock_response_page2.json.return_value = page2_tags

    # Page 3: 100 tags (1 stable tag, 99 unstable tags)
    page3_tags = [{"name": "go1.20.3"}] + [
        {"name": f"go1.19.{i}-rc1"} for i in range(99)
    ]
    mock_response_page3 = mocker.Mock()
    mock_response_page3.status_code = 200
    mock_response_page3.json.return_value = page3_tags

    # Page 4 (expected to exceed): empty
    mock_response_page4 = mocker.Mock()
    mock_response_page4.status_code = 200
    mock_response_page4.json.return_value = []

    mock_session.get.side_effect = [
        mock_response_page1,
        mock_response_page2,
        mock_response_page3,
        mock_response_page4,
    ]

    # Call with count=2 (terminate at 2)
    check_api(session=mock_session, count=2, verbose=True)
    captured = capsys.readouterr()

    # Verify output for debugging
    print("Captured output:\n", captured.out)

    # Verification
    assert "Found 1 stable tags on page 1" in captured.out
    assert "Found 1 stable tags on page 2" in captured.out
    assert "Total stable tags found: 2" in captured.out
    assert "- go1.22.1" in captured.out
    assert "- go1.21.0" in captured.out
