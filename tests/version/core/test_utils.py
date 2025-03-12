import logging
from typing import Any, Dict

import pytest
import requests
from pytest_mock import MockFixture

from json2vars_setter.version.core.utils import (
    ReleaseInfo,
    VersionInfo,
    check_github_api,
    clean_version,
    is_prerelease,
    parse_semver,
    setup_logging,
    standardize_date,
)


def test_release_info_initialization() -> None:
    """Test ReleaseInfo initialization with basic properties"""
    release = ReleaseInfo(version="1.0.0", prerelease=False)
    assert release.version == "1.0.0"
    assert release.prerelease is False


def test_release_info_with_additional_data() -> None:
    """Test ReleaseInfo initialization with additional data"""
    release = ReleaseInfo(
        version="1.0.0-beta",
        prerelease=True,
        release_date="2023-01-01",
        additional_info={"commit_hash": "abc123"},
    )
    assert release.version == "1.0.0-beta"
    assert release.prerelease is True
    assert release.release_date == "2023-01-01"
    assert release.additional_info.get("commit_hash") == "abc123"


def test_release_info_str_representation() -> None:
    """Test ReleaseInfo string representation"""
    release = ReleaseInfo(version="1.0.0", prerelease=False)
    assert release.version in str(release)
    str_repr = str(release)
    assert "1.0.0" in str_repr
    assert "ReleaseInfo" in str_repr


def test_version_info_initialization() -> None:
    """Test VersionInfo initialization with basic properties"""
    version_info = VersionInfo()
    assert version_info.latest is None
    assert version_info.stable is None
    assert version_info.recent_releases == []
    assert isinstance(version_info.details, dict)
    assert len(version_info.details) == 0
    version_info = VersionInfo(latest="1.1.0", stable="1.0.0")
    assert version_info.latest == "1.1.0"
    assert version_info.stable == "1.0.0"
    assert version_info.recent_releases == []


def test_version_info_with_recent_releases() -> None:
    """Test VersionInfo with recent releases"""
    release1 = ReleaseInfo(version="1.0.0", prerelease=False)
    release2 = ReleaseInfo(version="1.1.0", prerelease=False)
    version_info = VersionInfo(
        latest="1.1.0", stable="1.0.0", recent_releases=[release1, release2]
    )
    assert len(version_info.recent_releases) == 2
    assert version_info.recent_releases[0].version == "1.0.0"
    assert version_info.recent_releases[1].version == "1.1.0"


def test_version_info_with_details() -> None:
    """Test VersionInfo with details dictionary"""
    details = {
        "source": "github:test/repo",
        "fetch_time": "2023-01-01T12:00:00",
        "additional_info": "test data",
    }
    version_info = VersionInfo(latest="1.1.0", stable="1.0.0", details=details)
    assert version_info.details == details
    assert version_info.details["source"] == "github:test/repo"
    assert version_info.details["fetch_time"] == "2023-01-01T12:00:00"
    assert version_info.details["additional_info"] == "test data"


def test_version_info_str_representation() -> None:
    """Test VersionInfo string representation"""
    version_info = VersionInfo(latest="1.1.0", stable="1.0.0")
    str_repr = str(version_info)
    assert "1.1.0" in str_repr
    assert "1.0.0" in str_repr


def test_version_info_repr() -> None:
    """Test VersionInfo repr representation"""
    version_info = VersionInfo(latest="1.1.0", stable="1.0.0")
    repr_str = repr(version_info)
    assert "VersionInfo" in repr_str
    assert "1.1.0" in repr_str
    assert "1.0.0" in repr_str


def test_release_info_comparison() -> None:
    """Test ReleaseInfo comparison operations"""
    release1 = ReleaseInfo(version="1.0.0", prerelease=False)
    release2 = ReleaseInfo(version="1.1.0", prerelease=False)
    with pytest.raises(TypeError):
        release1 < release2
    with pytest.raises(TypeError):
        release1 > release2
    with pytest.raises(TypeError):
        release1 <= release2
    with pytest.raises(TypeError):
        release1 >= release2
    assert release1 == ReleaseInfo(version="1.0.0", prerelease=False)
    assert release1 != release2


def test_version_info_error_handling() -> None:
    """Test VersionInfo error handling through details"""
    version_info = VersionInfo(
        details={"error": "Test error", "error_type": "TestError"}
    )
    assert "error" in version_info.details
    assert version_info.details["error"] == "Test error"
    assert version_info.details["error_type"] == "TestError"
    assert version_info.has_error() is True


def test_version_info_details_none() -> None:
    version_info = VersionInfo(
        stable="1.0.0",
        latest="1.0.0",
        details={},
    )
    assert version_info.details == {}


def test_clean_version() -> None:
    """Test clean_version function with various inputs"""
    assert clean_version("v1.2.3") == "1.2.3"
    assert clean_version("version1.2.3") == "1.2.3"
    assert clean_version("go1.2.3") == "1.2.3"
    assert clean_version("node1.2.3") == "1.2.3"
    assert clean_version("ruby1.2.3") == "1.2.3"
    assert clean_version("v3_0_0") == "3.0.0"
    assert clean_version("  v1.2.3  ") == "1.2.3"


def test_parse_semver() -> None:
    """Test parse_semver function"""
    assert parse_semver("1.2.3") == (1, 2, 3)
    assert parse_semver("v1.2.3") == (1, 2, 3)
    with pytest.raises(ValueError, match="Invalid version format"):
        parse_semver("1.2")
    with pytest.raises(ValueError, match="Invalid version format"):
        parse_semver("v1.2")
    with pytest.raises(ValueError, match="Invalid version format"):
        parse_semver("1.2.3.4")
    with pytest.raises(ValueError, match="Invalid version format"):
        parse_semver("abc")


def test_standardize_date() -> None:
    """Test standardize_date function with various inputs"""
    assert standardize_date("2023-01-15") == "2023-01-15"
    assert standardize_date("2023-01-15Z") == "2023-01-15"
    assert standardize_date("15/01/2023") == "2023-01-15"
    assert standardize_date(None) is None
    assert standardize_date("") is None
    assert standardize_date("invalid-date") is None
    assert standardize_date("01-15-2023") is None


def test_is_prerelease() -> None:
    """Test is_prerelease function"""
    assert is_prerelease("1.0.0-alpha") is True
    assert is_prerelease("1.0.0-beta") is True
    assert is_prerelease("1.0.0-rc1") is True
    assert is_prerelease("1.0.0-dev") is True
    assert is_prerelease("1.0.0-preview") is True
    assert is_prerelease("1.0.0-pre") is True
    assert is_prerelease("1.0.0-nightly") is True
    assert is_prerelease("1.0.0-snapshot") is True
    assert is_prerelease("1.0.0-test") is True
    assert is_prerelease("1.0.0-experimental") is True
    assert is_prerelease("1.0.0") is False
    assert is_prerelease("1.2.3") is False


def test_release_info_repr_and_str() -> None:
    """Test ReleaseInfo repr and str methods"""
    release = ReleaseInfo(version="1.0.0", prerelease=False)
    repr_str = repr(release)
    assert "ReleaseInfo" in repr_str
    assert "version='1.0.0'" in repr_str
    assert "1.0.0" in str(release)


def test_version_info_additional_scenarios() -> None:
    """Test additional VersionInfo scenarios"""
    version_info = VersionInfo(details={})
    assert version_info.details == {}
    version_info = VersionInfo(latest="1.2.0")
    assert version_info.latest == "1.2.0"
    assert version_info.stable is None


def test_release_info_additional_data_handling() -> None:
    """Test ReleaseInfo handling of additional data"""
    release = ReleaseInfo(
        version="1.0.0",
        additional_info={
            "commit": "abc123",
            "build_date": "2023-01-01",
            "platforms": ["linux", "windows"],
        },
    )
    assert release.additional_info["commit"] == "abc123"
    assert release.additional_info["platforms"] == ["linux", "windows"]


def test_release_info_post_init_cleaning() -> None:
    """Test ReleaseInfo.__post_init__ cleaning behavior (line 30)"""
    release = ReleaseInfo(version=" v1.0.0 ", prerelease=False)
    assert release.version == "1.0.0"
    release = ReleaseInfo(version="1.0.0-beta", prerelease=False)
    assert release.prerelease is True


def test_release_info_not_equal() -> None:
    """Test ReleaseInfo.__ne__ method (line 37)"""
    release1 = ReleaseInfo(version="1.0.0", prerelease=False)
    release2 = ReleaseInfo(version="1.0.0", prerelease=False)
    release3 = ReleaseInfo(version="1.1.0", prerelease=False)
    assert not (release1 != release2)
    assert release1 != release3
    assert release1 != "string"


def test_clean_version_underscore_prefix() -> None:
    """Test clean_version with underscore prefix (line 74)"""
    assert clean_version("v_1_2_3") == "1.2.3"  # Match new implementation
    assert clean_version("_1_2_3") == "1.2.3"  # Case with only underscores
    assert clean_version("v1_2_3") == "1.2.3"  # Underscore after prefix


def test_standardize_date_alternative_formats() -> None:
    """Test standardize_date with additional formats (lines 158-159)"""
    assert standardize_date("2023/01/15") == "2023-01-15"  # %Y/%m/%d
    assert standardize_date("15-01-2023") == "2023-01-15"  # %d-%m-%Y is supported
    assert standardize_date("2023-01-15T12:00:00Z") == "2023-01-15"  # ISO format
    assert standardize_date("15/01/2023") == "2023-01-15"  # %d/%m/%Y


def test_clean_version_underscore_variations() -> None:
    """Test all patterns of clean_version with underscores (line 74)"""
    assert clean_version("v_1_2_3") == "1.2.3"  # Prefix + underscore
    assert clean_version("_1_2_3") == "1.2.3"  # No prefix, only underscores
    assert clean_version("v1_2_3") == "1.2.3"  # Underscore after prefix
    assert clean_version("1_2_3") == "1.2.3"  # Normal case without prefix
    assert clean_version("v__1__2__3") == "1.2.3"  # Consecutive underscores


def test_standardize_date_all_formats() -> None:
    """Test all formats of standardize_date (lines 158-159)"""
    # Existing formats
    assert standardize_date("2023/01/15") == "2023-01-15"  # %Y/%m/%d
    assert standardize_date("15-01-2023") == "2023-01-15"  # %d-%m-%Y
    assert standardize_date("2023-01-15T12:00:00Z") == "2023-01-15"  # ISO
    assert standardize_date("15/01/2023") == "2023-01-15"  # %d/%m/%Y

    # Untested supported formats
    assert standardize_date("2023-01-15") == "2023-01-15"  # %Y-%m-%d (direct pass)


def test_check_github_api_success(mocker: MockFixture) -> None:
    """Test check_github_api function success case (lines 207-232)"""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"name": "v1.0.0"}, {"name": "v1.1.0"}]
    mock_session.get.return_value = mock_response
    check_github_api(mock_session, "test-owner", "test-repo", count=2)
    mock_session.get.assert_called_once_with(
        "https://api.github.com/repos/test-owner/test-repo/tags",
        params={"per_page": 100},
        timeout=10,
    )


def test_check_github_api_no_tags(
    mocker: MockFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Test check_github_api when no tags are returned
    """
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = []  # Empty list of tags
    mock_session.get.return_value = mock_response

    check_github_api(mock_session, "test-owner", "test-repo")
    captured = capsys.readouterr()
    assert "Status Code: 200" in captured.out
    assert "Number of tags: 0" in captured.out
    assert "Error:" not in captured.out


def test_check_github_api_with_complex_filter(
    mocker: MockFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Test check_github_api with a more complex filter function
    """
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"name": "v1.0.0"},
        {"name": "v2.0.0-beta"},
        {"name": "v3.0.0-alpha"},
        {"name": "v4.0.0"},
    ]
    mock_session.get.return_value = mock_response

    def complex_filter(tag: Dict[str, Any]) -> bool:
        """
        Filter to keep only stable (non-beta/alpha) tags
        """
        return not any(pre in tag["name"] for pre in ["-beta", "-alpha"])

    check_github_api(
        mock_session, "test-owner", "test-repo", count=2, filter_func=complex_filter
    )
    captured = capsys.readouterr()
    assert "Number of filtered tags: 2" in captured.out
    assert "v1.0.0" in captured.out
    assert "v4.0.0" in captured.out


def test_check_github_api_error_handling(
    mocker: MockFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """
    Test check_github_api with various error scenarios
    """
    # Simulate HTTP error
    mock_session = mocker.Mock()
    mock_session.get.side_effect = requests.exceptions.HTTPError("HTTP Error")

    check_github_api(mock_session, "test-owner", "test-repo")
    captured = capsys.readouterr()
    assert "Error:" in captured.out
    assert "HTTP Error" in captured.out

    # Reset mock
    mock_session = mocker.Mock()
    mock_session.get.side_effect = ValueError("Unexpected error")

    check_github_api(mock_session, "test-owner", "test-repo")
    captured = capsys.readouterr()
    assert "Error:" in captured.out
    assert "Unexpected error" in captured.out


def test_check_github_api_error(
    mocker: MockFixture, capsys: pytest.CaptureFixture[str]
) -> None:
    """Test check_github_api function error case (lines 207-232)"""
    mock_session = mocker.Mock()
    mock_session.get.side_effect = Exception("API error")
    check_github_api(mock_session, "test-owner", "test-repo")
    captured = capsys.readouterr()
    assert "Error: API error" in captured.out  # Exception is only printed


def test_check_github_api_with_filter(mocker: MockFixture) -> None:
    """Test check_github_api with filtering case (lines 223-224)"""
    mock_session = mocker.Mock()
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"name": "v1.0.0"}, {"name": "v2.0.0-beta"}]
    mock_session.get.return_value = mock_response

    def filter_func(tag: Dict[str, Any]) -> bool:
        return "beta" not in tag["name"]

    check_github_api(
        mock_session, "test-owner", "test-repo", count=2, filter_func=filter_func
    )


def test_setup_logging_all_levels(caplog: pytest.LogCaptureFixture) -> None:
    """Test setup_logging function with all levels (lines 246-259)"""
    with caplog.at_level(logging.WARNING):
        logger = setup_logging(verbosity=0)
        assert logger.level == logging.WARNING
    with caplog.at_level(logging.INFO):
        logger = setup_logging(verbosity=1)
        assert logger.level == logging.INFO
    with caplog.at_level(logging.DEBUG):
        logger = setup_logging(verbosity=2)
        assert logger.level == logging.DEBUG
    with caplog.at_level(logging.DEBUG):
        logger = setup_logging(verbosity=3)
        assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def fixed_clean_version(version: str) -> str:
    cleaned = clean_version(version)
    return cleaned.lstrip(".")
