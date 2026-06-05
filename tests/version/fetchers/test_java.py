import pytest
import pytest_mock

from json2vars_setter.version.fetchers.java import JavaVersionFetcher


@pytest.fixture
def java_fetcher() -> JavaVersionFetcher:
    """Fixture to create a JavaVersionFetcher instance"""
    return JavaVersionFetcher()


def test_init(java_fetcher: JavaVersionFetcher) -> None:
    """Test __init__ sets the Adoptium API endpoint"""
    assert java_fetcher.github_owner == "adoptium"
    assert java_fetcher.github_repo == "temurin"
    assert java_fetcher.available_releases_url == (
        "https://api.adoptium.net/v3/info/available_releases"
    )


def test_fetch_versions_success(
    java_fetcher: JavaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions with a successful Adoptium API response"""
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "available_releases": [8, 11, 16, 17, 21, 22, 23, 24, 25, 26],
        "available_lts_releases": [8, 11, 17, 21, 25],
        "most_recent_feature_release": 26,
        "most_recent_lts": 25,
        "tip_version": 27,
    }
    mocker.patch.object(java_fetcher.session, "get", return_value=mock_response)

    versions = java_fetcher.fetch_versions(recent_count=5)

    assert versions.latest == "26"
    assert versions.stable == "25"

    # recent_releases are the LTS releases, newest first
    recent_versions = [r.version for r in versions.recent_releases]
    assert recent_versions == ["25", "21", "17", "11", "8"]

    # Details
    assert versions.details["source"] == "adoptium:info/available_releases"
    assert versions.details["most_recent_feature_release"] == 26
    assert versions.details["most_recent_lts"] == 25
    assert versions.details["available_lts_releases"] == [25, 21, 17, 11, 8]
    assert "fetch_time" in versions.details


def test_fetch_versions_respects_recent_count(
    java_fetcher: JavaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions limits recent_releases to recent_count"""
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        "available_lts_releases": [8, 11, 17, 21, 25],
        "most_recent_feature_release": 26,
        "most_recent_lts": 25,
    }
    mocker.patch.object(java_fetcher.session, "get", return_value=mock_response)

    versions = java_fetcher.fetch_versions(recent_count=2)

    recent_versions = [r.version for r in versions.recent_releases]
    assert recent_versions == ["25", "21"]


def test_fetch_versions_missing_fields(
    java_fetcher: JavaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions handles missing fields gracefully"""
    mock_response = mocker.Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {}  # no fields at all
    mocker.patch.object(java_fetcher.session, "get", return_value=mock_response)

    versions = java_fetcher.fetch_versions()

    assert versions.latest is None
    assert versions.stable is None
    assert versions.recent_releases == []
    assert versions.details["available_lts_releases"] == []


def test_fetch_versions_error(
    java_fetcher: JavaVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Test fetch_versions returns error details when the API call fails"""
    mocker.patch.object(java_fetcher, "logger", mocker.Mock())
    mocker.patch.object(java_fetcher.session, "get", side_effect=Exception("API error"))

    versions = java_fetcher.fetch_versions()

    assert versions.latest is None
    assert versions.stable is None
    assert "error" in versions.details
    assert versions.details["error_type"] == "Exception"


def test_abstract_methods_not_used(java_fetcher: JavaVersionFetcher) -> None:
    """The GitHub-tag hooks are intentionally unused for the Adoptium-based fetcher"""
    with pytest.raises(NotImplementedError):
        java_fetcher._is_stable_tag({"name": "irrelevant"})
    with pytest.raises(NotImplementedError):
        java_fetcher._parse_version_from_tag({"name": "irrelevant"})
