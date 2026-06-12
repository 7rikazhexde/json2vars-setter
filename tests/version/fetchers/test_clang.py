from typing import List, cast

import pytest
import pytest_mock
import requests
from _pytest.capture import CaptureFixture

from json2vars_setter.version.core.exceptions import ParseError
from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.clang import ClangVersionFetcher, check_api


@pytest.fixture
def clang_fetcher(mocker: "pytest_mock.MockerFixture") -> ClangVersionFetcher:
    """Fixture to create a ClangVersionFetcher instance with mocked logger."""
    fetcher: ClangVersionFetcher = ClangVersionFetcher()
    mocker.patch.object(fetcher, "logger", autospec=True)  # Mock logger for all tests
    return fetcher


def test_init(clang_fetcher: ClangVersionFetcher) -> None:
    """Test __init__ method."""
    assert clang_fetcher.github_owner == "llvm"
    assert clang_fetcher.github_repo == "llvm-project"


def test_is_stable_tag(clang_fetcher: ClangVersionFetcher) -> None:
    """Test _is_stable_tag method with various tag scenarios."""
    stable_tags: List[JsonObject] = [
        {"name": "llvmorg-22.1.7"},
        {"name": "llvmorg-21.1.8"},
        {"name": "llvmorg-20.1.0"},
    ]
    unstable_tags: List[JsonObject] = [
        {"name": "llvmorg-22.1.0-rc3"},
        {"name": "llvmorg-22.1.0-rc1"},
        {"name": "llvmorg-23-init"},  # dev-cycle opener
        {"name": "llvmorg-22-init"},
        {"name": "22.1.7"},  # missing the "llvmorg-" prefix
        {"name": "llvmorg-22.1"},  # incomplete (no patch)
        {"name": "build-1.0"},
        {"name": ""},  # Missing name
    ]

    for tag in stable_tags:
        assert clang_fetcher._is_stable_tag(tag) is True, f"Expected stable for {tag}"
    for tag in unstable_tags:
        assert clang_fetcher._is_stable_tag(tag) is False, (
            f"Expected unstable for {tag}"
        )


def test_parse_version_from_tag(clang_fetcher: ClangVersionFetcher) -> None:
    """Test _parse_version_from_tag method."""
    valid_tag: JsonObject = {
        "name": "llvmorg-22.1.7",
        "commit": {"sha": "abc123"},
        "tarball_url": "https://example.com/tarball",
        "zipball_url": "https://example.com/zipball",
    }
    release_info: ReleaseInfo = clang_fetcher._parse_version_from_tag(valid_tag)
    assert release_info.version == "22.1.7"
    assert release_info.prerelease is False
    assert release_info.release_date is None
    assert release_info.additional_info["tag_name"] == "llvmorg-22.1.7"
    assert cast(JsonObject, release_info.additional_info["commit"])["sha"] == "abc123"
    assert release_info.additional_info["tarball_url"] == "https://example.com/tarball"
    assert release_info.additional_info["zipball_url"] == "https://example.com/zipball"

    with pytest.raises(ParseError, match="No tag name found"):
        clang_fetcher._parse_version_from_tag({"name": ""})


def test_get_stability_criteria_with_previous_line(
    clang_fetcher: ClangVersionFetcher,
) -> None:
    """Test _get_stability_criteria picks the newest release on the previous line."""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="22.1.7", additional_info={"tag_name": "llvmorg-22.1.7"}),
        ReleaseInfo(version="22.1.6", additional_info={"tag_name": "llvmorg-22.1.6"}),
        ReleaseInfo(version="21.1.8", additional_info={"tag_name": "llvmorg-21.1.8"}),
        ReleaseInfo(version="21.1.7", additional_info={"tag_name": "llvmorg-21.1.7"}),
    ]
    latest, stable = clang_fetcher._get_stability_criteria(releases)
    assert latest.version == "22.1.7"
    assert stable.version == "21.1.8"  # previous major.minor line, newest patch
    (
        clang_fetcher.logger.info.assert_called_once_with(  # type: ignore[attr-defined]
            "Using 21.1.8 as stable vs latest 22.1.7"
        )
    )


def test_get_stability_criteria_no_previous_line(
    clang_fetcher: ClangVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria with only one line present, falling back to latest."""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="22.1.7", additional_info={"tag_name": "llvmorg-22.1.7"}),
        ReleaseInfo(version="22.1.6", additional_info={"tag_name": "llvmorg-22.1.6"}),
    ]
    latest, stable = clang_fetcher._get_stability_criteria(releases)
    assert latest.version == "22.1.7"
    assert stable.version == "22.1.7"
    (
        clang_fetcher.logger.info.assert_called_once_with(  # type: ignore[attr-defined]
            "No suitable stable version found, using latest 22.1.7 as stable"
        )
    )


def test_get_stability_criteria_with_invalid_version(
    clang_fetcher: ClangVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test _get_stability_criteria skips an unparsable release in the loop."""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(version="22.1.7", additional_info={"tag_name": "llvmorg-22.1.7"}),
        ReleaseInfo(
            version="invalid", additional_info={"tag_name": "invalid"}
        ),  # Invalid version, skipped
        ReleaseInfo(version="21.1.8", additional_info={"tag_name": "llvmorg-21.1.8"}),
    ]
    latest, stable = clang_fetcher._get_stability_criteria(releases)
    assert latest.version == "22.1.7"
    assert stable.version == "21.1.8"  # previous line, skipping the invalid entry
    (
        clang_fetcher.logger.info.assert_called_once_with(  # type: ignore[attr-defined]
            "Using 21.1.8 as stable vs latest 22.1.7"
        )
    )


def test_get_stability_criteria_no_releases(
    clang_fetcher: ClangVersionFetcher,
) -> None:
    """Test _get_stability_criteria with empty releases."""
    with pytest.raises(ValueError, match="No releases available"):
        clang_fetcher._get_stability_criteria([])


def test_get_stability_criteria_with_invalid_version_pattern(
    clang_fetcher: ClangVersionFetcher,
) -> None:
    """Test _get_stability_criteria with a completely invalid latest version pattern."""
    releases: List[ReleaseInfo] = [
        ReleaseInfo(
            version="not-a-valid-semver", additional_info={"tag_name": "invalid"}
        ),
        ReleaseInfo(version="21.1.8", additional_info={"tag_name": "llvmorg-21.1.8"}),
    ]
    latest, stable = clang_fetcher._get_stability_criteria(releases)
    assert latest.version == "not-a-valid-semver"
    assert stable.version == "not-a-valid-semver"  # no valid version found -> latest


def test_check_api_success(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with successful API response."""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "llvmorg-22.1.7"},
        {"name": "llvmorg-22.1.0-rc3"},
        {"name": "llvmorg-21.1.8"},
    ]
    mock_session.get.return_value = mock_response

    check_api(session=mock_session, count=2, verbose=True)
    captured = capsys.readouterr()
    assert "Total stable tags found: 2" in captured.out
    assert "- llvmorg-22.1.7" in captured.out
    assert "- llvmorg-21.1.8" in captured.out


def test_check_api_verbose_greater_than_one(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with verbose > 1 to cover raw tags output."""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "llvmorg-22.1.7"},
        {"name": "llvmorg-22.1.0-rc3"},
        {"name": "llvmorg-21.1.8"},
        {"name": "llvmorg-21.1.7"},
        {"name": "llvmorg-20.1.8"},
        {"name": "llvmorg-19.1.7"},  # More than 5 tags to ensure slicing
    ]
    mock_session.get.return_value = mock_response

    check_api(session=mock_session, count=2, verbose=2)  # verbose > 1
    captured = capsys.readouterr()
    assert "Total stable tags found: 5" in captured.out
    assert "First 5 raw tags on page 1:" in captured.out
    assert "- llvmorg-22.1.7" in captured.out
    assert "- llvmorg-22.1.0-rc3" in captured.out
    assert "- llvmorg-21.1.8" in captured.out
    assert "- llvmorg-21.1.7" in captured.out
    assert "- llvmorg-20.1.8" in captured.out


def test_check_api_partial_success(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with fewer stable tags than requested."""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "llvmorg-22.1.7"},
        {"name": "llvmorg-21.1.0-rc1"},
    ]
    mock_session.get.return_value = mock_response

    check_api(session=mock_session, count=3, verbose=True)
    captured = capsys.readouterr()
    assert "Total stable tags found: 1" in captured.out
    assert "- llvmorg-22.1.7" in captured.out


def test_check_api_multi_page(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api with multi-page response to cover pagination."""
    mock_session = mocker.Mock()
    mock_response_page1 = mocker.Mock()
    mock_response_page1.status_code = 200
    mock_response_page1.json.return_value = [{"name": "llvmorg-22.1.7"}] * 100
    mock_response_page2 = mocker.Mock()
    mock_response_page2.status_code = 200
    mock_response_page2.json.return_value = [
        {"name": "llvmorg-21.1.8"},
        {"name": "llvmorg-21.1.7"},
    ]  # Less than 100, last page
    mock_session.get.side_effect = [mock_response_page1, mock_response_page2]

    check_api(
        session=mock_session, count=102, verbose=True
    )  # Increased count to fetch 2 pages
    captured = capsys.readouterr()
    assert "Total stable tags found: 102" in captured.out
    assert "- llvmorg-22.1.7" in captured.out
    assert "- llvmorg-21.1.8" in captured.out


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


def test_check_api_multi_page_full_coverage(
    capsys: CaptureFixture[str], mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test check_api to cover while loop multiple iterations and exit condition."""
    mock_session = mocker.Mock()

    # Page 1: 100 tags (1 stable tag, 99 unstable tags)
    page1_tags = [{"name": "llvmorg-22.1.7"}] + [
        {"name": f"llvmorg-22.1.{i}-rc1"} for i in range(99)
    ]
    mock_response_page1 = mocker.Mock()
    mock_response_page1.status_code = 200
    mock_response_page1.json.return_value = page1_tags

    # Page 2: 100 tags (1 stable tag, 99 unstable tags)
    page2_tags = [{"name": "llvmorg-21.1.8"}] + [
        {"name": f"llvmorg-21.1.{i}-rc1"} for i in range(99)
    ]
    mock_response_page2 = mocker.Mock()
    mock_response_page2.status_code = 200
    mock_response_page2.json.return_value = page2_tags

    # Page 3: 100 tags (1 stable tag, 99 unstable tags)
    page3_tags = [{"name": "llvmorg-20.1.8"}] + [
        {"name": f"llvmorg-20.1.{i}-rc1"} for i in range(99)
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

    # Verification
    assert "Found 1 stable tags on page 1" in captured.out
    assert "Found 1 stable tags on page 2" in captured.out
    assert "Total stable tags found: 2" in captured.out
    assert "- llvmorg-22.1.7" in captured.out
    assert "- llvmorg-21.1.8" in captured.out
