from typing import List

import pytest
import pytest_mock

from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.flutter import (
    FLUTTER_RELEASES_URL,
    FlutterVersionFetcher,
)


@pytest.fixture
def flutter_fetcher() -> FlutterVersionFetcher:
    """Fixture to create a FlutterVersionFetcher instance"""
    return FlutterVersionFetcher()


class _FakeResponse:
    """Minimal stand-in for a requests.Response used in tests"""

    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


def _manifest(releases: List[JsonObject]) -> JsonObject:
    """Build a release-manifest payload from the given release entries"""
    return {
        "base_url": "https://storage.googleapis.com/flutter_infra_release/releases",
        "releases": releases,
    }


def test_init(flutter_fetcher: FlutterVersionFetcher) -> None:
    """Test __init__ sets the (unused) GitHub repository information"""
    assert flutter_fetcher.github_owner == "flutter"
    assert flutter_fetcher.github_repo == "flutter"


def test_tag_methods_not_implemented(flutter_fetcher: FlutterVersionFetcher) -> None:
    """The GitHub-tags hooks are not used and must raise"""
    with pytest.raises(NotImplementedError):
        flutter_fetcher._is_stable_tag({"name": "3.44.2"})
    with pytest.raises(NotImplementedError):
        flutter_fetcher._parse_version_from_tag({"name": "3.44.2"})


def test_list_stable_versions(
    flutter_fetcher: FlutterVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Only clean stable-channel versions are kept, de-duplicated and sorted desc"""
    payload = _manifest(
        [
            {"channel": "stable", "version": "3.44.1"},
            {"channel": "beta", "version": "3.45.0"},  # non-stable channel excluded
            {"channel": "stable", "version": "3.44.2"},
            {"channel": "stable", "version": "3.41.9"},
            {"channel": "stable", "version": "1.12.13+hotfix.9"},  # non-clean excluded
            {"channel": "stable", "version": "3.44.2"},  # duplicate
        ]
    )
    mock_get = mocker.patch.object(
        flutter_fetcher.session, "get", return_value=_FakeResponse(payload)
    )

    versions = flutter_fetcher._list_stable_versions()

    assert versions == ["3.44.2", "3.44.1", "3.41.9"]
    assert mock_get.call_count == 1


def test_list_stable_versions_real_url(
    flutter_fetcher: FlutterVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """The listing request targets the official Flutter release manifest"""
    payload = _manifest([{"channel": "stable", "version": "3.44.2"}])
    mock_get = mocker.patch.object(
        flutter_fetcher.session, "get", return_value=_FakeResponse(payload)
    )

    flutter_fetcher._list_stable_versions()

    args, _kwargs = mock_get.call_args
    assert args[0] == FLUTTER_RELEASES_URL
    assert args[0].endswith("releases_linux.json")


def test_select_latest_stable(flutter_fetcher: FlutterVersionFetcher) -> None:
    """Latest is first; stable is the newest release on the previous minor line"""
    versions = ["3.44.2", "3.44.1", "3.41.9", "3.41.8"]
    latest, stable = flutter_fetcher._select_latest_stable(versions)
    assert latest == "3.44.2"
    assert stable == "3.41.9"


def test_select_latest_stable_no_previous_minor(
    flutter_fetcher: FlutterVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Falls back to latest when every release shares the minor line"""
    mocker.patch.object(flutter_fetcher, "logger", mocker.Mock())
    versions = ["3.44.2", "3.44.1"]
    latest, stable = flutter_fetcher._select_latest_stable(versions)
    assert latest == "3.44.2"
    assert stable == "3.44.2"


def test_select_latest_stable_empty(flutter_fetcher: FlutterVersionFetcher) -> None:
    """An empty list raises ValueError"""
    with pytest.raises(ValueError):
        flutter_fetcher._select_latest_stable([])


def test_fetch_versions_integration(
    flutter_fetcher: FlutterVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """fetch_versions builds a VersionInfo from the listed versions"""
    mocker.patch.object(
        flutter_fetcher,
        "_list_stable_versions",
        return_value=["3.44.2", "3.44.1", "3.41.9"],
    )

    versions = flutter_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "3.44.2"
    assert versions.stable == "3.41.9"
    assert len(versions.recent_releases) == 2
    assert versions.recent_releases[0] == ReleaseInfo(
        version="3.44.2", prerelease=False
    )
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "flutter-releases:stable"


def test_fetch_versions_no_versions(
    flutter_fetcher: FlutterVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """An empty listing yields an error VersionInfo"""
    mocker.patch.object(flutter_fetcher, "_list_stable_versions", return_value=[])

    versions = flutter_fetcher.fetch_versions()

    assert versions.latest is None
    assert versions.details["error"] == "No releases found"


def test_fetch_versions_error(
    flutter_fetcher: FlutterVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """A network/parse error is captured in the VersionInfo details"""
    mocker.patch.object(flutter_fetcher, "logger", mocker.Mock())
    mocker.patch.object(
        flutter_fetcher,
        "_list_stable_versions",
        side_effect=RuntimeError("boom"),
    )

    versions = flutter_fetcher.fetch_versions()

    assert versions.latest is None
    assert versions.details["error"] == "boom"
    assert versions.details["error_type"] == "RuntimeError"
