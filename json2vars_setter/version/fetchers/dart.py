import re
from typing import List, Optional, Tuple, cast

import requests

from json2vars_setter.version.core.base import BaseVersionFetcher
from json2vars_setter.version.core.utils import (
    JsonObject,
    ReleaseInfo,
    VersionInfo,
    get_utc_now,
    setup_logging,
)

# Dart SDK versions are not cleanly represented by the dart-lang/sdk GitHub tags
# (that monorepo is dominated by per-package tags such as ``analyzer-*`` and the
# plain SDK version tags are buried). The Dart release archive on Google Cloud
# Storage is the authoritative, clean source for "which Dart SDK versions exist".
DART_ARCHIVE_LIST_URL = "https://storage.googleapis.com/storage/v1/b/dart-archive/o"
DART_STABLE_PREFIX = "channels/stable/release/"

# Matches the version segment of a release prefix, e.g.
# "channels/stable/release/3.12.1/" -> "3.12.1".
_VERSION_RE = re.compile(rf"{re.escape(DART_STABLE_PREFIX)}(\d+\.\d+\.\d+)/$")


class DartVersionFetcher(BaseVersionFetcher):
    """Fetches Dart SDK version information from the Dart release archive"""

    def __init__(self) -> None:
        """Initialize the fetcher.

        The base class wires up a requests session; the github owner/repo are
        unused because this fetcher overrides ``fetch_versions`` and talks to the
        Dart archive (GCS) rather than the GitHub tags endpoint.
        """
        super().__init__("dart-lang", "sdk")

    def _is_stable_tag(self, tag: JsonObject) -> bool:
        """Not used: DartVersionFetcher uses the Dart archive, not GitHub tags."""
        raise NotImplementedError("DartVersionFetcher uses the Dart archive, not tags")

    def _parse_version_from_tag(self, tag: JsonObject) -> ReleaseInfo:
        """Not used: DartVersionFetcher uses the Dart archive, not GitHub tags."""
        raise NotImplementedError("DartVersionFetcher uses the Dart archive, not tags")

    def _list_stable_versions(self) -> List[str]:
        """
        List every stable Dart SDK version from the release archive.

        The GCS bucket listing returns release "folders" as ``prefixes``, sorted
        lexicographically (so ``3.9.x`` sorts after ``3.12.x``); this method
        extracts the version segments and returns them sorted **numerically**,
        newest first.

        Returns:
            Stable version strings (e.g. ["3.12.1", "3.12.0", ...]), newest first
        """
        versions: List[str] = []
        page_token: Optional[str] = None
        max_pages = 10  # Safety limit; the listing currently fits in one page

        for _ in range(max_pages):
            params = {
                "delimiter": "/",
                "prefix": DART_STABLE_PREFIX,
                "fields": "prefixes,nextPageToken",
            }
            if page_token:
                params["pageToken"] = page_token

            # Use a plain requests.get (not self.session) so the GitHub
            # Authorization header is not forwarded to GCS — GCS rejects
            # GitHub tokens with 401.
            response = requests.get(DART_ARCHIVE_LIST_URL, params=params, timeout=10)
            response.raise_for_status()
            data = cast(JsonObject, response.json())

            for prefix in cast(List[str], data.get("prefixes", [])):
                match = _VERSION_RE.search(str(prefix))
                if match:
                    versions.append(match.group(1))

            page_token = cast(Optional[str], data.get("nextPageToken"))
            if not page_token:
                break

        # Sort numerically (major, minor, patch), newest first
        versions.sort(key=lambda v: tuple(int(p) for p in v.split(".")), reverse=True)
        return versions

    def _select_latest_stable(self, versions: List[str]) -> Tuple[str, str]:
        """
        Pick the latest version and a stable version from a newest-first list.

        - latest: the most recent version
        - stable: the newest patch of the previous minor of latest (falls back to
          latest when no previous-minor release is available)

        Args:
            versions: Stable versions, newest first

        Returns:
            Tuple of (latest, stable)

        Raises:
            ValueError: If the list is empty
        """
        if not versions:
            raise ValueError("No releases available")

        latest = versions[0]
        major, minor, _patch = (int(p) for p in latest.split("."))
        prev_minor = minor - 1

        for version in versions:
            v_major, v_minor, _v_patch = (int(p) for p in version.split("."))
            if v_major == major and v_minor == prev_minor:
                self.logger.info(f"Using {version} as stable vs latest {latest}")
                return latest, version

        self.logger.info(
            f"No suitable stable version found, using latest {latest} as stable"
        )
        return latest, latest

    def fetch_versions(self, recent_count: int = 5) -> VersionInfo:
        """
        Fetch Dart SDK version information from the Dart release archive

        Args:
            recent_count: Number of recent stable releases to include

        Returns:
            VersionInfo object containing version information
        """
        try:
            versions = self._list_stable_versions()
            if not versions:
                return VersionInfo(details={"error": "No releases found"})

            latest, stable = self._select_latest_stable(versions)

            recent_releases = [
                ReleaseInfo(version=v, prerelease=False)
                for v in versions[:recent_count]
            ]

            return VersionInfo(
                latest=latest,
                stable=stable,
                recent_releases=recent_releases,
                details={
                    "fetch_time": get_utc_now().isoformat(),
                    "source": "dart-archive:channels/stable/release",
                    "latest": latest,
                    "stable": stable,
                },
            )
        except Exception as error:
            self.logger.error("Error fetching versions: %s", str(error), exc_info=True)
            return VersionInfo(
                details={"error": str(error), "error_type": type(error).__name__}
            )


if __name__ == "__main__":
    import argparse
    import json

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Fetch Dart version information")
    parser.add_argument(
        "--count", type=int, default=5, help="Number of versions to fetch"
    )
    parser.add_argument(
        "--verbose", "-v", action="count", default=0, help="Increase verbosity"
    )
    args = parser.parse_args()

    # Set up logging
    logger = setup_logging(args.verbose)

    # Display header in verbose mode
    if args.verbose > 0:
        print("\n=== Fetching Dart Versions (Dart archive) ===")

    # Main processing
    fetcher = DartVersionFetcher()
    versions = fetcher.fetch_versions(recent_count=args.count)

    # Output results
    print(
        json.dumps(
            {
                "latest": versions.latest,
                "stable": versions.stable,
                "recent_releases": [vars(r) for r in versions.recent_releases],
                "details": versions.details,
            },
            indent=2,
        )
    )
