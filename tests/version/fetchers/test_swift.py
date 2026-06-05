from typing import List

import pytest
import pytest_mock

from json2vars_setter.version.core.utils import ReleaseInfo
from json2vars_setter.version.fetchers.swift import SwiftVersionFetcher


@pytest.fixture
def swift_fetcher() -> SwiftVersionFetcher:
    """Fixture to create a SwiftVersionFetcher instance"""
    return SwiftVersionFetcher()


class _FakeResponse:
    """Minimal stand-in for a requests.Response used in tests"""

    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


def _entries(names: List[str]) -> List[dict]:
    """Build swift.org-style release entries for the given names"""
    return [{"name": n, "tag": f"swift-{n}-RELEASE"} for n in names]


def test_init(swift_fetcher: SwiftVersionFetcher) -> None:
    """Test __init__ sets the (unused) GitHub repository information"""
    assert swift_fetcher.github_owner == "apple"
    assert swift_fetcher.github_repo == "swift"


def test_tag_methods_not_implemented(swift_fetcher: SwiftVersionFetcher) -> None:
    """The GitHub-tags hooks are not used and must raise"""
    with pytest.raises(NotImplementedError):
        swift_fetcher._is_stable_tag({"name": "6.3.2"})
    with pytest.raises(NotImplementedError):
        swift_fetcher._parse_version_from_tag({"name": "6.3.2"})


def test_list_release_versions(
    swift_fetcher: SwiftVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Names are filtered, parsed, and returned numerically, newest first"""
    payload = _entries(["6.2", "6.3.2", "6.2.4", "5.10.1"])
    # A non-version entry that must be ignored
    payload.append({"name": "main-snapshot", "tag": "swift-DEVELOPMENT-SNAPSHOT"})
    payload.append({"name": ""})

    mock_get = mocker.patch.object(
        swift_fetcher.session, "get", return_value=_FakeResponse(payload)
    )

    versions = swift_fetcher._list_release_versions()

    assert versions == ["6.3.2", "6.2.4", "6.2", "5.10.1"]
    assert mock_get.call_count == 1


def test_select_latest_stable(swift_fetcher: SwiftVersionFetcher) -> None:
    """Latest is first; stable is the newest release of the previous minor"""
    versions = ["6.3.2", "6.3.1", "6.2.4", "6.2", "5.10.1"]
    latest, stable = swift_fetcher._select_latest_stable(versions)
    assert latest == "6.3.2"
    assert stable == "6.2.4"


def test_select_latest_stable_no_previous_minor(
    swift_fetcher: SwiftVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Falls back to latest when no previous-minor release exists"""
    mocker.patch.object(swift_fetcher, "logger", mocker.Mock())
    versions = ["6.0", "6.0"]
    latest, stable = swift_fetcher._select_latest_stable(versions)
    assert latest == "6.0"
    assert stable == "6.0"


def test_select_latest_stable_empty(swift_fetcher: SwiftVersionFetcher) -> None:
    """An empty list raises ValueError"""
    with pytest.raises(ValueError):
        swift_fetcher._select_latest_stable([])


def test_fetch_versions_integration(
    swift_fetcher: SwiftVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """fetch_versions builds a VersionInfo from the listed versions"""
    mocker.patch.object(
        swift_fetcher,
        "_list_release_versions",
        return_value=["6.3.2", "6.3.1", "6.2.4"],
    )

    versions = swift_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "6.3.2"
    assert versions.stable == "6.2.4"
    assert len(versions.recent_releases) == 2
    assert versions.recent_releases[0] == ReleaseInfo(version="6.3.2", prerelease=False)
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "swift.org:install/releases"


def test_fetch_versions_no_versions(
    swift_fetcher: SwiftVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """An empty listing yields an error VersionInfo"""
    mocker.patch.object(swift_fetcher, "_list_release_versions", return_value=[])

    versions = swift_fetcher.fetch_versions()

    assert versions.latest is None
    assert versions.details["error"] == "No releases found"


def test_fetch_versions_error(
    swift_fetcher: SwiftVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """A network/parse error is captured in the VersionInfo details"""
    mocker.patch.object(swift_fetcher, "logger", mocker.Mock())
    mocker.patch.object(
        swift_fetcher,
        "_list_release_versions",
        side_effect=RuntimeError("boom"),
    )

    versions = swift_fetcher.fetch_versions()

    assert versions.latest is None
    assert versions.details["error"] == "boom"
    assert versions.details["error_type"] == "RuntimeError"


def test_list_release_versions_real_url(
    swift_fetcher: SwiftVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """The listing request targets the swift.org install API"""
    mock_get = mocker.patch.object(
        swift_fetcher.session, "get", return_value=_FakeResponse(_entries(["6.3.2"]))
    )

    swift_fetcher._list_release_versions()

    args, _ = mock_get.call_args
    assert args[0] == "https://www.swift.org/api/v1/install/releases.json"
