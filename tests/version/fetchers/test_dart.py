from typing import List, Optional

import pytest
import pytest_mock

from json2vars_setter.version.core.utils import JsonObject, ReleaseInfo
from json2vars_setter.version.fetchers.dart import DartVersionFetcher


@pytest.fixture
def dart_fetcher() -> DartVersionFetcher:
    """Fixture to create a DartVersionFetcher instance"""
    return DartVersionFetcher()


class _FakeResponse:
    """Minimal stand-in for a requests.Response used in tests"""

    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


def _prefixes(versions: List[str], extra: Optional[List[str]] = None) -> List[str]:
    """Build GCS-style release prefixes for the given versions"""
    items = [f"channels/stable/release/{v}/" for v in versions]
    if extra:
        items.extend(extra)
    return items


def test_init(dart_fetcher: DartVersionFetcher) -> None:
    """Test __init__ sets the (unused) GitHub repository information"""
    assert dart_fetcher.github_owner == "dart-lang"
    assert dart_fetcher.github_repo == "sdk"


def test_tag_methods_not_implemented(dart_fetcher: DartVersionFetcher) -> None:
    """The GitHub-tags hooks are not used and must raise"""
    with pytest.raises(NotImplementedError):
        dart_fetcher._is_stable_tag({"name": "3.12.1"})
    with pytest.raises(NotImplementedError):
        dart_fetcher._parse_version_from_tag({"name": "3.12.1"})


def test_list_stable_versions_single_page(
    dart_fetcher: DartVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Lexicographically ordered prefixes are returned numerically, newest first"""
    payload = {
        # Deliberately out of order and including a non-version entry ("latest/")
        "prefixes": _prefixes(
            ["3.9.4", "3.12.1", "3.10.0", "3.12.0"],
            extra=["channels/stable/release/latest/"],
        ),
    }
    mock_get = mocker.patch.object(
        dart_fetcher.session, "get", return_value=_FakeResponse(payload)
    )

    versions = dart_fetcher._list_stable_versions()

    assert versions == ["3.12.1", "3.12.0", "3.10.0", "3.9.4"]
    assert mock_get.call_count == 1


def test_list_stable_versions_paginated(
    dart_fetcher: DartVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Pagination via nextPageToken is followed and results are merged"""
    page1 = {"prefixes": _prefixes(["3.11.0", "3.11.1"]), "nextPageToken": "tok"}
    page2 = {"prefixes": _prefixes(["3.12.0"])}
    mock_get = mocker.patch.object(
        dart_fetcher.session,
        "get",
        side_effect=[_FakeResponse(page1), _FakeResponse(page2)],
    )

    versions = dart_fetcher._list_stable_versions()

    assert versions == ["3.12.0", "3.11.1", "3.11.0"]
    assert mock_get.call_count == 2
    # The second request must carry the page token
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["pageToken"] == "tok"


def test_select_latest_stable(dart_fetcher: DartVersionFetcher) -> None:
    """Latest is first; stable is the newest patch of the previous minor"""
    versions = ["3.12.1", "3.12.0", "3.11.6", "3.11.5", "3.10.0"]
    latest, stable = dart_fetcher._select_latest_stable(versions)
    assert latest == "3.12.1"
    assert stable == "3.11.6"


def test_select_latest_stable_no_previous_minor(
    dart_fetcher: DartVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """Falls back to latest when no previous-minor release exists"""
    mocker.patch.object(dart_fetcher, "logger", mocker.Mock())
    versions = ["3.0.1", "3.0.0"]
    latest, stable = dart_fetcher._select_latest_stable(versions)
    assert latest == "3.0.1"
    assert stable == "3.0.1"


def test_select_latest_stable_empty(dart_fetcher: DartVersionFetcher) -> None:
    """An empty list raises ValueError"""
    with pytest.raises(ValueError):
        dart_fetcher._select_latest_stable([])


def test_fetch_versions_integration(
    dart_fetcher: DartVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """fetch_versions builds a VersionInfo from the listed versions"""
    mocker.patch.object(
        dart_fetcher,
        "_list_stable_versions",
        return_value=["3.12.1", "3.12.0", "3.11.6"],
    )

    versions = dart_fetcher.fetch_versions(recent_count=2)

    assert versions.latest == "3.12.1"
    assert versions.stable == "3.11.6"
    assert len(versions.recent_releases) == 2
    assert versions.recent_releases[0] == ReleaseInfo(
        version="3.12.1", prerelease=False
    )
    assert "fetch_time" in versions.details
    assert versions.details["source"] == "dart-archive:channels/stable/release"


def test_fetch_versions_no_versions(
    dart_fetcher: DartVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """An empty listing yields an error VersionInfo"""
    mocker.patch.object(dart_fetcher, "_list_stable_versions", return_value=[])

    versions = dart_fetcher.fetch_versions()

    assert versions.latest is None
    assert versions.details["error"] == "No releases found"


def test_fetch_versions_error(
    dart_fetcher: DartVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """A network/parse error is captured in the VersionInfo details"""
    mocker.patch.object(dart_fetcher, "logger", mocker.Mock())
    mocker.patch.object(
        dart_fetcher,
        "_list_stable_versions",
        side_effect=RuntimeError("boom"),
    )

    versions = dart_fetcher.fetch_versions()

    assert versions.latest is None
    assert versions.details["error"] == "boom"
    assert versions.details["error_type"] == "RuntimeError"


def test_list_stable_versions_real_url(
    dart_fetcher: DartVersionFetcher, mocker: "pytest_mock.MockerFixture"
) -> None:
    """The listing request targets the Dart archive bucket with the stable prefix"""
    payload: JsonObject = {"prefixes": _prefixes(["3.12.1"])}
    mock_get = mocker.patch.object(
        dart_fetcher.session, "get", return_value=_FakeResponse(payload)
    )

    dart_fetcher._list_stable_versions()

    args, kwargs = mock_get.call_args
    assert args[0].endswith("/storage/v1/b/dart-archive/o")
    assert kwargs["params"]["prefix"] == "channels/stable/release/"
