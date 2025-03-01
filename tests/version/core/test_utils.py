import pytest

from json2vars_setter.version.core.utils import (
    ReleaseInfo,
    VersionInfo,
    clean_version,
    is_prerelease,
    parse_semver,
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

    # デフォルトの文字列表現を確認
    assert release.version in str(release)
    # または、より柔軟なアサーションを使用
    str_repr = str(release)
    assert "1.0.0" in str_repr
    assert "ReleaseInfo" in str_repr


def test_version_info_initialization() -> None:
    """Test VersionInfo initialization with basic properties"""
    # Basic initialization
    version_info = VersionInfo()
    assert version_info.latest is None
    assert version_info.stable is None
    assert version_info.recent_releases == []
    assert isinstance(version_info.details, dict)
    assert len(version_info.details) == 0

    # Initialization with values
    version_info = VersionInfo(latest="1.1.0", stable="1.0.0")
    assert version_info.latest == "1.1.0"
    assert version_info.stable == "1.0.0"
    assert version_info.recent_releases == []


def test_version_info_with_recent_releases() -> None:
    """Test VersionInfo with recent releases"""
    # Create some releases
    release1 = ReleaseInfo(version="1.0.0", prerelease=False)
    release2 = ReleaseInfo(version="1.1.0", prerelease=False)

    # Add them to VersionInfo
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

    # Ensure string representation contains version information
    str_repr = str(version_info)
    assert "1.1.0" in str_repr
    assert "1.0.0" in str_repr


def test_version_info_repr() -> None:
    """Test VersionInfo repr representation"""
    version_info = VersionInfo(latest="1.1.0", stable="1.0.0")

    # Ensure repr contains class name and version information
    repr_str = repr(version_info)
    assert "VersionInfo" in repr_str
    assert "1.1.0" in repr_str
    assert "1.0.0" in repr_str


def test_release_info_comparison() -> None:
    """Test ReleaseInfo comparison operations"""
    release1 = ReleaseInfo(version="1.0.0", prerelease=False)
    release2 = ReleaseInfo(version="1.1.0", prerelease=False)

    # Ensure comparison raises a TypeError
    with pytest.raises(TypeError):
        release1 < release2

    with pytest.raises(TypeError):
        release1 > release2

    with pytest.raises(TypeError):
        release1 <= release2

    with pytest.raises(TypeError):
        release1 >= release2

    # 等価性の比較は許可されているべき
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


def test_clean_version() -> None:
    """Test clean_version function with various inputs"""
    # Test removing common prefixes
    assert clean_version("v1.2.3") == "1.2.3"

    # Versions with prefixes
    assert clean_version("version1.2.3") == "1.2.3"

    # Test handling of different language prefixes
    assert clean_version("go1.2.3") == "1.2.3"
    assert clean_version("node1.2.3") == "1.2.3"
    assert clean_version("ruby1.2.3") == "1.2.3"

    # Test handling of underscore-separated versions
    assert clean_version("v3_0_0") == "3.0.0"

    # Test handling of whitespace with prefix
    assert clean_version("  v1.2.3  ") == "1.2.3"


def test_parse_semver() -> None:
    """Test parse_semver function"""
    # Test successful parsing
    assert parse_semver("1.2.3") == (1, 2, 3)
    assert parse_semver("v1.2.3") == (1, 2, 3)

    # Test error cases
    with pytest.raises(ValueError, match="Invalid version format"):
        parse_semver("1.2")  # 不完全なバージョン文字列（x.y形式）

    with pytest.raises(ValueError, match="Invalid version format"):
        parse_semver("v1.2")  # プレフィックス付きの不完全なバージョン文字列

    with pytest.raises(ValueError, match="Invalid version format"):
        parse_semver("1.2.3.4")  # 余分な数字

    with pytest.raises(ValueError, match="Invalid version format"):
        parse_semver("abc")  # 全く不正な形式


def test_standardize_date() -> None:
    """Test standardize_date function with various inputs"""
    # Test ISO format dates
    assert standardize_date("2023-01-15") == "2023-01-15"
    assert standardize_date("2023-01-15Z") == "2023-01-15"

    # Test alternative date formats
    assert standardize_date("15/01/2023") == "2023-01-15"

    # Test edge cases
    assert standardize_date(None) is None
    assert standardize_date("") is None

    # Test invalid date formats
    assert standardize_date("invalid-date") is None
    assert (
        standardize_date("01-15-2023") is None
    )  # この形式は実際にはサポートされていない


def test_is_prerelease() -> None:
    """Test is_prerelease function"""
    # Test prerelease indicators
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

    # Test non-prerelease versions
    assert is_prerelease("1.0.0") is False
    assert is_prerelease("1.2.3") is False


def test_release_info_repr_and_str() -> None:
    """Test ReleaseInfo repr and str methods"""
    release = ReleaseInfo(version="1.0.0", prerelease=False)

    # Check repr contains class name and version details
    repr_str = repr(release)
    assert "ReleaseInfo" in repr_str
    assert "version='1.0.0'" in repr_str

    # __str__メソッドが存在しない場合、デフォルトの文字列表現をテスト
    assert "1.0.0" in str(release)


def test_version_info_additional_scenarios() -> None:
    """Test additional VersionInfo scenarios"""
    # Test with empty details
    version_info = VersionInfo(details={})
    assert version_info.details == {}

    # Test with partial information
    version_info = VersionInfo(latest="1.2.0")
    assert version_info.latest == "1.2.0"
    assert version_info.stable is None


def test_release_info_additional_data_handling() -> None:
    """Test ReleaseInfo handling of additional data"""
    # Test with complex additional info
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
